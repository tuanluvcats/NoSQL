"""Nhận chuyến LWT hai tầng trên Cassandra thật: đúng một bên thắng, bên thua được trả AVAILABLE, IDOR."""
import threading
from datetime import date

import pytest

from config import AREAS
from db import trace
from domain.ids import new_ride_id
from domain.tz import parse_vn
from domain.write_matrix import WRITE_MATRIX
from services import booking, driver_presence, rides_flow
from services.booking import BookingForm
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.nosql]

NOW = parse_vn("2026-10-04 10:04")
CLOCK = parse_vn("2026-10-04 10:05")


def _status(db, driver_id):
    return db.one("B03_driver_get", [driver_id])["status"]


def _month_ids(db, driver_id, yyyymm):
    return [r["ride_id"] for r in db.rows("B10_driver_month", [driver_id, yyyymm])]


def _new_ride(db, customer_id, clock, rand="AAAA", district="TAN_PHU"):
    f = BookingForm(ride_id=new_ride_id(clock, rand=lambda: rand), city="HCM", district=district,
                    pickup_address="1 Lũy Bán Bích", destination_address="2 Tân Hương", distance_km=3.0,
                    payment_method="CASH", promo_code=None)
    assert booking.book_ride(db, customer_id, f, clock).ok
    return f.ride_id


class _StaleRideDb:
    """Bọc CassandraDb: B06 trả bản chụp cũ (chuyến còn REQUESTED) để ép nhánh thua ở tầng rides."""

    def __init__(self, inner, stale):
        self._inner, self._stale = inner, stale
        self.keyspace = inner.keyspace

    def one(self, name, params=()):
        if name == "B06_ride_get":
            return dict(self._stale)
        return self._inner.one(name, params)

    def __getattr__(self, item):
        return getattr(self._inner, item)


def test_accept_success_updates_every_table_and_clears_areas(db):
    trace.start_request()
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    written = trace.tables_written(trace.current())
    assert r.ok and r.code == "ok", r
    assert set(WRITE_MATRIX["accept"]["required"]) <= set(written)
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["status"] == "ACCEPTED" and ride["driver_id"] == "DRV_551"
    assert ride["driver_name"] == "Lý Văn Phúc" and ride["vehicle_plate"] == "51F-123.45"
    assert ride["accepted_at"] is not None and len(ride["status_history"]) == 2
    assert _status(db, "DRV_551") == "BUSY"
    assert driver_presence.find_area_rows(db, "DRV_551") == []
    rbc = [x for x in db.rows("B07_customer_history", ["CUST006"]) if x["ride_id"] == "RIDE_1024"][0]
    assert rbc["driver_id"] == "DRV_551" and rbc["status"] == "ACCEPTED"
    area = [x for x in db.rows("B11_area_day", ["HCM", "TAN_PHU", date(2026, 10, 4)]) if x["ride_id"] == "RIDE_1024"][0]
    assert area["driver_id"] == "DRV_551" and area["status"] == "ACCEPTED"
    assert area["requested_at"] == ride["requested_at"]
    assert "RIDE_1024" in _month_ids(db, "DRV_551", 202610)
    assert driver_presence.waiting_rides(db, "HCM", "TAN_PHU", date(2026, 10, 4)) == []


def test_two_drivers_race_exactly_one_wins(db):
    barrier = threading.Barrier(2)
    results: dict[str, object] = {}

    def worker(driver_id):
        barrier.wait()
        try:
            results[driver_id] = rides_flow.accept_ride(db, "RIDE_1024", driver_id, NOW)
        except BaseException as e:  # noqa: BLE001
            results[driver_id] = e

    threads = [threading.Thread(target=worker, args=(d,)) for d in ("DRV_551", "DRV_553")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert len(results) == 2 and not any(isinstance(v, BaseException) for v in results.values()), results
    winners = [d for d, r in results.items() if r.ok]
    losers = [d for d, r in results.items() if not r.ok]
    assert len(winners) == 1 and len(losers) == 1
    win, lose = winners[0], losers[0]
    assert results[lose].code in ("lwt_lost", "invalid_transition")
    assert results[lose].current["status"] == "ACCEPTED"
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["driver_id"] == win and ride["status"] == "ACCEPTED"
    assert _status(db, win) == "BUSY"
    assert _status(db, lose) == "AVAILABLE"  # bên thua không kẹt BUSY
    assert "RIDE_1024" not in _month_ids(db, lose, 202610)
    assert "RIDE_1024" in _month_ids(db, win, 202610)
    assert driver_presence.find_area_rows(db, win) == []


def test_lost_at_rides_releases_driver_deterministically(db):
    stale = db.one("B06_ride_get", ["RIDE_1024"])
    assert rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW).ok
    trace.start_request()
    loser = rides_flow.accept_ride(_StaleRideDb(db, stale), "RIDE_1024", "DRV_553", NOW)
    assert not loser.ok and loser.code == "lwt_lost" and loser.current["status"] == "ACCEPTED"
    assert _status(db, "DRV_553") == "AVAILABLE"  # đã giữ rồi trả về
    assert db.one("B06_ride_get", ["RIDE_1024"])["driver_id"] == "DRV_551"
    assert "RIDE_1024" not in _month_ids(db, "DRV_553", 202610)
    assert [x["driver_id"] for x in db.rows("B12_area_drivers", ["HCM", "BINH_THANH"])] == ["DRV_553"]  # vẫn trong danh sách rảnh
    names = [e.name for e in trace.current()]
    assert names.index("APP07_driver_claim") < names.index("T05_ride_accept") < names.index("APP08_driver_release")


def test_accept_twice_by_same_driver_second_is_invalid_transition(db):
    assert rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW).ok
    again = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert not again.ok and again.code == "invalid_transition"
    assert _status(db, "DRV_551") == "BUSY"
    assert db.one("B06_ride_get", ["RIDE_1024"])["driver_id"] == "DRV_551"


def test_busy_driver_cannot_take_second_ride(db):
    # (a) vừa nhận một chuyến thì bị xóa khỏi drivers_by_area và BUSY, không nhận được chuyến thứ hai
    assert rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW).ok
    new_id = _new_ride(db, "CUST002", CLOCK)
    r = rides_flow.accept_ride(db, new_id, "DRV_551", CLOCK)
    assert not r.ok and r.code in {"driver_not_online", "driver_not_available"}
    assert db.one("B06_ride_get", [new_id])["status"] == "REQUESTED"
    assert db.one("B06_ride_get", [new_id])["driver_id"] is None
    assert _status(db, "DRV_551") == "BUSY"


def test_busy_driver_with_stale_area_row_is_stopped_by_drivers_lwt(db):
    # (b) dòng drivers_by_area cũ của tài xế BUSY: LWT trên drivers chặn
    db.exec("T03_area_insert", ["HCM", "TAN_PHU", "DRV_552", "Trương Minh Quang", "0912000552", 3.0,
                                "51G-234.56", None, None, NOW])
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_552", NOW)
    assert not r.ok and r.code == "driver_not_available" and r.current == {"status": "BUSY"}
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["status"] == "REQUESTED" and ride["driver_id"] is None
    assert _status(db, "DRV_552") == "BUSY"
    assert "RIDE_1024" not in _month_ids(db, "DRV_552", 202610)


def test_offline_driver_cannot_accept(db):
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_555", NOW)
    assert not r.ok and r.code == "driver_not_online"
    assert _status(db, "DRV_555") == "OFFLINE"
    assert db.one("B06_ride_get", ["RIDE_1024"])["status"] == "REQUESTED"


def test_accept_requires_driver_online_in_ride_city(db):
    # DRV_557 online ở HN, chuyến ở HCM
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_557", NOW)
    assert not r.ok and r.code == "driver_not_online"
    assert _status(db, "DRV_557") == "AVAILABLE"


def test_accept_missing_ride_and_non_requested_ride(db):
    assert rides_flow.accept_ride(db, "RIDE_NOPE", "DRV_551", NOW).code == "not_found"
    r = rides_flow.accept_ride(db, "RIDE_1001", "DRV_551", NOW)  # đã COMPLETED
    assert not r.ok and r.code == "invalid_transition" and r.current["status"] == "COMPLETED"
    assert _status(db, "DRV_551") == "AVAILABLE"


def test_accept_month_bucket_uses_plus07(db):
    clock = parse_vn("2026-11-01 06:30")
    ride_id = _new_ride(db, "CUST002", clock, rand="BEEF")
    r = rides_flow.accept_ride(db, ride_id, "DRV_551", parse_vn("2026-11-01 06:32"))
    assert r.ok, r
    assert ride_id in _month_ids(db, "DRV_551", 202611)
    assert ride_id not in _month_ids(db, "DRV_551", 202610)
    area = [x for x in db.rows("B11_area_day", ["HCM", "TAN_PHU", date(2026, 11, 1)]) if x["ride_id"] == ride_id]
    assert len(area) == 1 and area[0]["status"] == "ACCEPTED" and area[0]["driver_id"] == "DRV_551"


# ---------------- HTTP: phân quyền, IDOR ----------------
def _clock():
    return NOW


def test_http_driver_accepts_ride_and_sees_trace(client_factory, db):
    c = client_factory(clock=_clock)
    assert http_login(c, "drv551").status_code == 303
    r = c.post("/rides/RIDE_1024/accept")
    assert r.status_code == 303 and r.headers["location"] == "/rides/RIDE_1024"
    page = c.get("/rides/RIDE_1024")
    assert page.status_code == 200 and "ACCEPTED" in page.text and "DRV_551" in page.text
    assert "CQL của thao tác vừa rồi" in page.text and "APP07" in page.text and "T05" in page.text
    assert "ma trận ghi của sự kiện “Nhận chuyến”" in page.text and "thiếu" not in page.text
    assert _status(db, "DRV_551") == "BUSY"


def test_http_driver_cannot_forge_driver_id(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "drv551")
    r = c.post("/rides/RIDE_1024/accept", data={"driver_id": "DRV_553"})
    assert r.status_code == 303
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["driver_id"] == "DRV_551"  # lấy từ phiên đăng nhập, bỏ qua form
    assert _status(db, "DRV_553") == "AVAILABLE"


def test_http_losing_driver_gets_message_and_no_access_to_taken_ride(client_factory, db):
    winner = client_factory(clock=_clock)
    http_login(winner, "drv551")
    assert winner.post("/rides/RIDE_1024/accept").status_code == 303
    loser = client_factory(clock=_clock)
    http_login(loser, "drv553")
    r = loser.post("/rides/RIDE_1024/accept")
    assert r.status_code == 303 and r.headers["location"] == "/driver"
    assert loser.get("/rides/RIDE_1024").status_code == 403  # chuyến đã của tài xế khác
    assert db.one("B06_ride_get", ["RIDE_1024"])["driver_id"] == "DRV_551"
    assert _status(db, "DRV_553") == "AVAILABLE"
    assert loser.post("/rides/RIDE_NOPE/accept").status_code == 404


def test_http_customer_admin_and_guest_cannot_accept(client_factory, db):
    cust = client_factory(clock=_clock)
    http_login(cust, "cust006")
    assert cust.post("/rides/RIDE_1024/accept").status_code == 403
    assert cust.get("/driver").status_code == 403
    assert cust.post("/driver/online", data={"city": "HCM", "district": "Q1", "plate": "51K-567.89"}).status_code == 403
    admin = client_factory(clock=_clock)
    http_login(admin, "admin")
    assert admin.post("/rides/RIDE_1024/accept").status_code == 403
    guest = client_factory(clock=_clock)
    r = guest.post("/rides/RIDE_1024/accept")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["status"] == "REQUESTED" and ride["driver_id"] is None


def test_http_other_customer_cannot_view_requested_ride_but_owner_can(client_factory):
    owner = client_factory(clock=_clock)
    http_login(owner, "cust006")
    assert owner.get("/rides/RIDE_1024").status_code == 200
    other = client_factory(clock=_clock)
    http_login(other, "cust002")
    assert other.get("/rides/RIDE_1024").status_code == 403


def test_http_driver_flow_online_waiting_accept_offline(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "drv555")
    assert "Ngoại tuyến" in c.get("/driver").text
    r = c.post("/driver/online", data={"city": "HCM", "district": "TAN_PHU", "plate": "51K-567.89",
                                       "lat": "10.80", "lng": "106.63"})
    assert r.status_code == 303 and r.headers["location"] == "/driver"
    home = c.get("/driver")
    assert home.status_code == 200 and "Sẵn sàng" in home.text and "TAN_PHU" in home.text
    assert "ma trận ghi của sự kiện “Tài xế bật nhận chuyến”" in home.text and "thiếu" not in home.text
    wrong = c.post("/driver/online", data={"city": "HCM", "district": "Q1", "plate": "51G-234.56"})
    assert wrong.status_code == 400
    assert driver_presence.find_area_rows(db, "DRV_555") and len(driver_presence.find_area_rows(db, "DRV_555")) == 1
    waiting = c.get("/driver/waiting", params={"city": "HCM", "district": "TAN_PHU", "day": "2026-10-04"})
    assert waiting.status_code == 200 and "RIDE_1024" in waiting.text and "/rides/RIDE_1024/accept" in waiting.text
    assert c.get("/driver/waiting", params={"city": "HCM", "district": "TAN_PHU", "day": "2026-10-03"}).text.count("RIDE_1024") == 0
    assert c.get("/driver/waiting", params={"city": "XX", "district": "Q1", "day": "2026-10-04"}).status_code == 400
    assert c.get("/driver/waiting", params={"city": "HCM", "district": "Q1", "day": "khong-phai-ngay"}).status_code == 400
    assert c.post("/driver/offline").status_code == 303
    assert _status(db, "DRV_555") == "OFFLINE" and driver_presence.find_area_rows(db, "DRV_555") == []


def test_http_busy_driver_offline_is_refused(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "drv552")
    r = c.post("/driver/offline")
    assert r.status_code == 303
    assert _status(db, "DRV_552") == "BUSY"
    assert "Đang chở khách" in c.get("/driver").text
