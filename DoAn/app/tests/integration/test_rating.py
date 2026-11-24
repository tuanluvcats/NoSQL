"""Đánh giá một lần bằng LWT rated_at, backfill dữ liệu seed, kết quả khớp CASSANDRA.MD §8 (T09). Cassandra thật (_test)."""
from datetime import timezone

import pytest

from domain.tz import parse_vn
from services import driver_presence, rating
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.nosql]

NOW = parse_vn("2026-10-04 10:50")


def _count_ratings(db, driver_id):
    return len(db.rows("B14_ratings", [driver_id]))


def test_backfill_marks_seed_ratings_and_is_idempotent(db):
    assert rating.backfill_rated_at(db) == 0  # fixture đã chạy backfill sau seed
    assert db.one("B06_ride_get", ["RIDE_1001"])["rated_at"] is not None
    assert db.one("B06_ride_get", ["RIDE_1010"])["rated_at"] is None  # chưa có đánh giá


def test_backfill_applies_to_unmarked_seed_ride_once(db, raw):
    raw.execute("UPDATE rides SET rated_at = null WHERE ride_id = 'RIDE_1001'")
    assert db.one("B06_ride_get", ["RIDE_1001"])["rated_at"] is None
    assert rating.backfill_rated_at(db) == 1
    assert rating.backfill_rated_at(db) == 0
    assert db.one("B06_ride_get", ["RIDE_1001"])["rated_at"] is not None


def test_rerating_seed_rated_ride_rejected(db):
    r = rating.rate_ride(db, "RIDE_1001", "CUST001", 5, "Lại", [], NOW)
    assert not r.ok and r.code == "already_rated"
    assert _count_ratings(db, "DRV_555") == 2


def test_rating_offline_driver_creates_no_area_row(db):
    """Chống dòng ma: đánh giá tài xế OFFLINE không được tạo dòng ma trong drivers_by_area (UPDATE là upsert)."""
    assert db.one("B03_driver_get", ["DRV_555"])["status"] == "OFFLINE"
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "Tốt", ["Lịch sự"], NOW)
    assert r.ok and r.code == "ok", r
    d = db.one("B03_driver_get", ["DRV_555"])
    assert d["rating"] == 4.67  # (5 + 4 + 5) / 3 làm tròn 2 chữ số, khớp CASSANDRA.MD §8 / T09
    assert _count_ratings(db, "DRV_555") == 3
    assert driver_presence.find_area_rows(db, "DRV_555") == []  # không sinh dòng ma
    assert db.one("B06_ride_get", ["RIDE_1010"])["rated_at"] == NOW.astimezone(timezone.utc).replace(tzinfo=None)


def test_second_rating_rejected(db):
    assert rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "Tốt", ["Lịch sự"], NOW).ok
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 1, "Đổi ý", [], parse_vn("2026-10-04 11:00"))
    assert not r.ok and r.code == "already_rated"
    assert _count_ratings(db, "DRV_555") == 3
    assert db.one("B03_driver_get", ["DRV_555"])["rating"] == 4.67  # không đổi


def test_rating_only_when_completed_and_by_owner(db):
    assert db.one("B06_ride_get", ["RIDE_1022"])["status"] != "COMPLETED"
    assert rating.rate_ride(db, "RIDE_1022", "CUST003", 5, "", [], NOW).code == "invalid_transition"
    assert rating.rate_ride(db, "RIDE_1010", "CUST001", 5, "", [], NOW).code == "forbidden"
    assert rating.rate_ride(db, "RIDE_9999", "CUST003", 5, "", [], NOW).code == "not_found"
    assert db.one("B06_ride_get", ["RIDE_1010"])["rated_at"] is None
    assert _count_ratings(db, "DRV_555") == 2


def test_rating_online_driver_updates_both_rating_columns(db):
    r = rating.rate_ride(db, "RIDE_1034", "CUST003", 3, "Tạm", [], NOW)
    assert r.ok, r
    assert db.one("B03_driver_get", ["DRV_553"])["rating"] == 4.4  # (5+5+5+4+3)/5
    rows = db.rows("B12_area_drivers", ["HCM", "BINH_THANH"])
    assert [x["rating"] for x in rows if x["driver_id"] == "DRV_553"] == [4.4]
    assert len(driver_presence.find_area_rows(db, "DRV_553")) == 1


def test_rate_http_flow_and_authz(client_factory, db):
    c = client_factory(clock=lambda: NOW)
    assert http_login(c, "cust003").status_code == 303
    page = c.get("/rides/RIDE_1010")
    assert page.status_code == 200 and 'action="/rides/RIDE_1010/rate"' in page.text
    r = c.post("/rides/RIDE_1010/rate", data={"stars": "5", "comment": "Tốt", "tags": ["Lịch sự", "Xe sạch"]})
    assert r.status_code == 303 and r.headers["location"] == "/rides/RIDE_1010"
    assert db.one("B03_driver_get", ["DRV_555"])["rating"] == 4.67
    again = c.get("/rides/RIDE_1010")
    assert 'action="/rides/RIDE_1010/rate"' not in again.text  # đã đánh giá thì hết form
    c.post("/rides/RIDE_1010/rate", data={"stars": "1"})
    assert _count_ratings(db, "DRV_555") == 3
    # khách khác không đánh giá hộ được (IDOR)
    other = client_factory(clock=lambda: NOW)
    http_login(other, "cust001")
    assert other.post("/rides/RIDE_1034/rate", data={"stars": "1"}).status_code == 403
    assert db.one("B06_ride_get", ["RIDE_1034"])["rated_at"] is None
    # tài xế không đánh giá được; khách chưa đăng nhập bị đưa về /login
    d = client_factory(clock=lambda: NOW)
    http_login(d, "drv555")
    assert d.post("/rides/RIDE_1010/rate", data={"stars": "5"}).status_code == 403
    g = client_factory(clock=lambda: NOW)
    assert g.post("/rides/RIDE_1010/rate", data={"stars": "5"}).headers["location"].startswith("/login")


def test_rate_http_invalid_stars_rejected(client_factory, db):
    c = client_factory(clock=lambda: NOW)
    http_login(c, "cust003")
    for bad in ("0", "6", "abc", ""):
        r = c.post("/rides/RIDE_1010/rate", data={"stars": bad})
        assert r.status_code == 303
    assert db.one("B06_ride_get", ["RIDE_1010"])["rated_at"] is None
    assert _count_ratings(db, "DRV_555") == 2
