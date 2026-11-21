"""Tài xế bật/tắt nhận chuyến: chỉ một khu vực trong drivers_by_area, kiểm biển số qua MV, không offline khi BUSY."""
from datetime import date

import pytest

from config import AREAS
from domain.ids import new_ride_id
from domain.tz import parse_vn, to_date
from services import booking, driver_presence
from services.booking import BookingForm

pytestmark = [pytest.mark.business, pytest.mark.nosql]

NOW = parse_vn("2026-10-04 10:04")


def _status(db, driver_id):
    return db.one("B03_driver_get", [driver_id])["status"]


def _area_rows(db, driver_id):
    return [(r["city"], r["district"]) for r in driver_presence.find_area_rows(db, driver_id)]


def test_go_online_offline_driver_writes_status_area_and_location(db):
    r = driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51K-567.89", 10.7815, 106.6985, NOW)
    assert r.ok and r.code == "ok", r
    assert _status(db, "DRV_555") == "AVAILABLE"
    rows = {x["driver_id"]: x for x in db.rows("B12_area_drivers", ["HCM", "Q1"])}
    assert rows["DRV_555"]["rating"] == 4.5 and rows["DRV_555"]["vehicle_plate"] == "51K-567.89"
    assert rows["DRV_555"]["full_name"] == "Nguyễn Hữu Thắng"
    latest = db.one("B13_location_latest", ["DRV_555", date(2026, 10, 4)])
    assert latest["lat"] == 10.7815 and latest["lng"] == 106.6985


def test_go_online_with_other_drivers_plate_is_rejected_without_writes(db):
    r = driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51G-234.56", 10.78, 106.69, NOW)  # biển của DRV_552
    assert not r.ok and r.code == "invalid_input"
    assert _status(db, "DRV_555") == "OFFLINE" and _area_rows(db, "DRV_555") == []
    r = driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "99Z-000.00", 10.78, 106.69, NOW)  # biển không tồn tại
    assert not r.ok and r.code == "invalid_input"
    assert _status(db, "DRV_555") == "OFFLINE"


def test_go_online_rejects_bad_area_unknown_driver_and_bad_coordinates(db):
    assert driver_presence.go_online(db, "DRV_555", "DN", "Q1", "51K-567.89", None, None, NOW).code == "invalid_input"
    assert driver_presence.go_online(db, "DRV_555", "HCM", "HOAN_KIEM", "51K-567.89", None, None, NOW).code == "invalid_input"
    assert driver_presence.go_online(db, "DRV_NOPE", "HCM", "Q1", "51K-567.89", None, None, NOW).code == "not_found"
    assert driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51K-567.89", 95.0, 106.0, NOW).code == "invalid_input"
    assert driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51K-567.89", 10.0, None, NOW).code == "invalid_input"
    assert _status(db, "DRV_555") == "OFFLINE"


def test_go_online_without_coordinates_writes_no_location(db):
    r = driver_presence.go_online(db, "DRV_555", "HCM", "Q1", "51K-567.89", None, None, NOW)
    assert r.ok
    assert db.one("B13_location_latest", ["DRV_555", date(2026, 10, 4)]) is None
    row = [x for x in db.rows("B12_area_drivers", ["HCM", "Q1"]) if x["driver_id"] == "DRV_555"][0]
    assert row["lat"] is None


def test_driver_has_single_area_after_moving(db):
    assert _area_rows(db, "DRV_551") == [("HCM", "TAN_PHU")]  # seed
    r = driver_presence.go_online(db, "DRV_551", "HCM", "Q1", "51F-123.45", 10.78, 106.69, NOW)
    assert r.ok
    assert _area_rows(db, "DRV_551") == [("HCM", "Q1")]  # đã rời TAN_PHU
    assert _status(db, "DRV_551") == "AVAILABLE"
    # chuyển sang thành phố khác vẫn chỉ còn một dòng trên toàn hệ thống
    assert driver_presence.go_online(db, "DRV_551", "HN", "CAU_GIAY", "51F-123.45", None, None, NOW).ok
    assert _area_rows(db, "DRV_551") == [("HN", "CAU_GIAY")]


def test_busy_driver_can_neither_go_offline_nor_online(db):
    off = driver_presence.go_offline(db, "DRV_552", NOW)
    assert not off.ok and off.code == "driver_busy"
    on = driver_presence.go_online(db, "DRV_552", "HCM", "Q1", "51G-234.56", 10.78, 106.69, NOW)
    assert not on.ok and on.code == "driver_busy"
    assert _status(db, "DRV_552") == "BUSY" and _area_rows(db, "DRV_552") == []


def test_go_offline_removes_from_every_area_and_marks_offline(db):
    r = driver_presence.go_offline(db, "DRV_551", NOW)
    assert r.ok and _status(db, "DRV_551") == "OFFLINE"
    assert driver_presence.find_area_rows(db, "DRV_551") == []
    # dòng cũ ở khu vực khác (do lỗi trước đó) cũng bị xóa
    for district in ("Q1", "GO_VAP"):
        db.exec("T03_area_insert", ["HCM", district, "DRV_551", "Lý Văn Phúc", "0912000551", 4.8,
                                    "51F-123.45", None, None, NOW])
    assert len(driver_presence.find_area_rows(db, "DRV_551")) == 2
    db.lwt("APP20_driver_online", ["DRV_551"])
    assert driver_presence.go_offline(db, "DRV_551", NOW).ok
    assert driver_presence.find_area_rows(db, "DRV_551") == []


def test_go_offline_when_already_offline_is_idempotent(db):
    r = driver_presence.go_offline(db, "DRV_555", NOW)
    assert r.ok and _status(db, "DRV_555") == "OFFLINE"
    assert driver_presence.go_offline(db, "DRV_NOPE", NOW).code == "not_found"


def test_online_offline_never_creates_area_row_outside_config(db):
    driver_presence.go_online(db, "DRV_555", "HN", "SOC_SON", "51K-567.89", None, None, NOW)
    driver_presence.go_offline(db, "DRV_555", NOW)
    for city, districts in AREAS.items():
        for d in districts:
            assert all(x["driver_id"] != "DRV_555" for x in db.rows("B12_area_drivers", [city, d]))


def test_waiting_rides_lists_requested_rides_of_the_day(db):
    waiting = driver_presence.waiting_rides(db, "HCM", "TAN_PHU", date(2026, 10, 4))
    assert [w["ride_id"] for w in waiting] == ["RIDE_1024"]
    assert driver_presence.waiting_rides(db, "HCM", "Q1", date(2026, 10, 4)) == []
    assert driver_presence.waiting_rides(db, "HCM", "TAN_PHU", date(2026, 10, 3)) == []


def test_waiting_rides_follow_plus7_day_and_status(db):
    clock = parse_vn("2026-11-01 06:30")  # 2026-10-31 23:30 UTC
    f = BookingForm(ride_id=new_ride_id(clock, rand=lambda: "BEEF"), city="HCM", district="TAN_PHU",
                    pickup_address="1 Lũy Bán Bích", destination_address="2 Tân Hương", distance_km=3.0,
                    payment_method="CASH", promo_code=None)
    assert booking.book_ride(db, "CUST002", f, clock).ok
    on_1st = driver_presence.waiting_rides(db, "HCM", "TAN_PHU", date(2026, 11, 1))
    assert [w["ride_id"] for w in on_1st] == [f.ride_id]
    assert driver_presence.waiting_rides(db, "HCM", "TAN_PHU", date(2026, 10, 31)) == []
    assert to_date(date(2026, 11, 1)) == date(2026, 11, 1)
