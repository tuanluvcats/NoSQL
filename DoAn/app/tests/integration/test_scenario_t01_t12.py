"""Kịch bản T01-T12 của CASSANDRA.MD §8 chạy end-to-end qua HTTP (đăng ký, khóa, đặt xe, bắt đầu, hoàn thành,
đánh giá, hủy, thêm/bớt city) và qua service (bật nhận chuyến, tranh nhận chuyến cần đọc dòng LWT hiện tại)."""
import re
from datetime import date

import pytest

from domain.rides import history_entries
from domain.tz import parse_vn
from services import accounts, consistency, driver_presence, rating, rides_flow
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.business

DAY = date(2026, 10, 4)


def _at(hhmmss: str):
    h = hhmmss if hhmmss.count(":") == 2 else hhmmss + ":00"
    return parse_vn(f"2026-10-04 {h}")


def _book_via_http(client, data):
    rid = re.search(r'name="ride_id"[^>]*value="([^"]+)"', client.get("/customer/book").text).group(1)
    r = client.post("/customer/book", data={"ride_id": rid, **data})
    assert r.status_code == 303 and r.headers["location"] == f"/rides/{rid}", r.text[:300]
    return rid


def _cities(db, code):
    return {r["promo_code"]: set(r["cities"]) for r in db.rows("A08_promo_cities", [[code]])}[code]


def test_t01_t12_final_state_matches_cassandra_md_s8(client_factory, db):
    """Khớp CASSANDRA.MD §8, trừ ride_id do ứng dụng sinh và lượt mã được giữ ở T04 thay vì T07."""
    clock = {"now": _at("10:01")}

    def now():
        return clock["now"]

    def client(username=None):
        c = client_factory(clock=now)
        if username:
            assert http_login(c, username).status_code == 303, username
        return c

    # ---- T01 (10:01): đăng ký cust016; đăng ký lại bị LWT chặn
    reg = {"username": "cust016", "password": "123456", "full_name": "Khách Thử Mười Sáu",
           "phone": "0901000016", "email": "cust016@example.com", "address": "1 Test"}
    anon = client()
    assert anon.post("/register", data=reg).status_code == 303
    assert anon.post("/register", data=reg).status_code == 409  # username_taken
    assert db.one("B01_account_get", ["cust016"])["role"] == "CUSTOMER"

    # ---- T02 (10:02): admin khóa cust016 -> đăng nhập bị từ chối -> mở khóa -> đăng nhập được
    clock["now"] = _at("10:02")
    admin = client("admin")
    assert admin.post("/admin/accounts/cust016/lock").status_code == 303
    assert http_login(client(), "cust016").status_code == 403
    assert accounts.login(db, "cust016", "123456", now()).code == "account_locked"
    assert admin.post("/admin/accounts/cust016/unlock").status_code == 303
    assert http_login(client(), "cust016").status_code == 303

    # ---- T03 (10:04): DRV_555 bật nhận chuyến ở Q1
    clock["now"] = _at("10:04")
    r = driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51K-567.89", 10.7815, 106.6985, now())
    assert r.ok, r
    assert any(a["driver_id"] == "DRV_555" for a in db.rows("B12_area_drivers", ["HCM", "Q1"]))

    # ---- T04 (10:05): CUST001 đặt xe có GIAM20
    clock["now"] = _at("10:05")
    cust001 = client("cust001")
    r1 = _book_via_http(cust001, {"city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1",
                                  "destination_address": "Sân bay Tân Sơn Nhất, Tân Bình", "distance_km": "8.1",
                                  "payment_method": "MOMO", "promo_code": "GIAM20"})

    # ---- T05: DRV_555 thắng lúc 10:06, DRV_554 thua lúc 10:06:01
    won = rides_flow.accept_ride(db, r1, "DRV_555", _at("10:06"))
    assert won.ok and won.code == "ok", won
    lost = rides_flow.accept_ride(db, r1, "DRV_554", _at("10:06:01"))
    assert not lost.ok and lost.current["status"] == "ACCEPTED", lost
    assert db.one("B03_driver_get", ["DRV_554"])["status"] == "AVAILABLE"  # bên thua không kẹt BUSY

    # ---- T06 (10:12): DRV_554 không phải tài xế của chuyến; DRV_555 bắt đầu
    clock["now"] = _at("10:12")
    coords = {"lat": "10.7995", "lng": "106.6790"}
    assert client("drv554").post(f"/rides/{r1}/start", data=coords).status_code == 403
    assert db.one("B06_ride_get", [r1])["status"] == "ACCEPTED"
    drv555 = client("drv555")
    assert drv555.post(f"/rides/{r1}/start", data=coords).status_code == 303
    assert db.one("B06_ride_get", [r1])["status"] == "ONGOING"

    # ---- T07: lượt mã đã được giữ ở T04 (seed used_count = 5)
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6

    # ---- T08 (10:35): hoàn thành tại TAN_BINH
    clock["now"] = _at("10:35")
    done = drv555.post(f"/rides/{r1}/complete", data={"drop_district": "TAN_BINH", "lat": "10.8185", "lng": "106.6588"})
    assert done.status_code == 303
    assert db.one("B06_ride_get", [r1])["status"] == "COMPLETED"

    # ---- T09 (10:40): CUST001 đánh giá 5 sao; đánh giá lại bị từ chối
    clock["now"] = _at("10:40")
    rate = {"stars": "5", "comment": "Ra sân bay đúng giờ", "tags": ["Đúng giờ", "Lịch sự"]}
    assert cust001.post(f"/rides/{r1}/rate", data=rate).status_code == 303
    assert len(db.rows("B14_ratings", ["DRV_555"])) == 3
    assert cust001.post(f"/rides/{r1}/rate", data={**rate, "stars": "1"}).status_code == 303  # bị từ chối, PRG
    assert rating.rate_ride(db, r1, "CUST001", 1, "x", [], now()).code == "already_rated"
    assert len(db.rows("B14_ratings", ["DRV_555"])) == 3

    # ---- T10: CUST006 đặt lúc 10:20 rồi hủy lúc 10:23
    clock["now"] = _at("10:20")
    cust006 = client("cust006")
    r2 = _book_via_http(cust006, {"city": "HCM", "district": "TAN_PHU", "pickup_address": "140 Lê Trọng Tấn, Tân Phú",
                                  "destination_address": "Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng",
                                  "distance_km": "1.8", "payment_method": "CASH", "promo_code": ""})
    clock["now"] = _at("10:23")
    assert cust006.post(f"/rides/{r2}/cancel", data={"reason": "Khách đổi ý"}).status_code == 303

    # ---- T11: thêm rồi bỏ city DN của GIAM20
    assert admin.post("/admin/promotions/GIAM20/cities/add", data={"city": "DN"}).status_code == 303
    assert _cities(db, "GIAM20") == {"DN", "HCM", "HN"}
    assert admin.post("/admin/promotions/GIAM20/cities/remove", data={"city": "DN"}).status_code == 303
    assert _cities(db, "GIAM20") == {"HCM", "HN"}

    # ---- T12: kết quả cuối
    ride1 = db.one("B06_ride_get", [r1])
    assert (ride1["status"], ride1["driver_id"], ride1["fare"], ride1["discount"], ride1["promo_code"]) == \
        ("COMPLETED", "DRV_555", 81000.0, 16000.0, "GIAM20")
    assert history_entries(ride1["status_history"]) == [
        (_at("10:05"), "REQUESTED"), (_at("10:06"), "ACCEPTED"), (_at("10:12"), "ONGOING"), (_at("10:35"), "COMPLETED")]

    ride2 = db.one("B06_ride_get", [r2])
    assert (ride2["status"], ride2["driver_id"], ride2["fare"], ride2["discount"], ride2["promo_code"]) == \
        ("CANCELLED", None, 27000.0, 0.0, None)

    drv = db.one("B03_driver_get", ["DRV_555"])
    assert (drv["rating"], drv["status"]) == (4.67, "AVAILABLE")

    pay = [p for p in db.rows("B15_payments_day", ["HCM", DAY]) if p["ride_id"] == r1]
    assert len(pay) == 1 and pay[0]["payment_method"] == "MOMO"
    assert (pay[0]["amount"], pay[0]["discount"]) == (65000.0, 16000.0)

    area = {a["driver_id"]: a for a in db.rows("B12_area_drivers", ["HCM", "TAN_BINH"])}
    assert area["DRV_555"]["rating"] == 4.67

    hist = {h["ride_id"]: h for h in db.rows("B08_customer_history_range", ["CUST001", DAY, DAY])}
    assert hist[r1]["status"] == "COMPLETED" and hist[r1]["driver_id"] == "DRV_555"

    assert len(db.rows("B14_ratings", ["DRV_555"])) == 3

    assert consistency.check_ride(db, r1) == []
    assert consistency.check_ride(db, r2) == []
