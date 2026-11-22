"""Kiểm tra nhất quán: phát hiện tài xế kẹt BUSY và giải phóng an toàn (unit, FakeDb)."""
import pytest

from db.repo import LwtResult
from domain.tz import parse_vn
from services import consistency
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:00")
BUSY = {"driver_id": "DRV_551", "full_name": "A", "status": "BUSY"}
AVAILABLE = {"driver_id": "DRV_551", "full_name": "A", "status": "AVAILABLE"}
SCAN = "APP27_rides_by_driver_scan"


def _scan_row(ride_id, driver_id, status):
    return {"ride_id": ride_id, "driver_id": driver_id, "status": status}


def test_has_active_ride_prefers_month_tables_then_confirms_with_rides():
    req = parse_vn("2026-10-04 09:00")
    db = FakeDb({
        "B10_driver_month": [[{"ride_id": "R1", "status": "ACCEPTED", "requested_at": req}], []],
        "B06_ride_get": [{"ride_id": "R1", "driver_id": "DRV_551", "status": "ACCEPTED"}],
    })
    assert consistency.active_ride_of(db, "DRV_551", NOW) == "R1"
    assert db.calls[0] == ("B10_driver_month", ("DRV_551", 202610))
    assert SCAN not in db.names()  # tìm thấy ở đường nhanh thì khỏi quét


def test_stale_month_row_is_not_trusted_without_rides_confirmation():
    db = FakeDb({
        "B10_driver_month": [[{"ride_id": "R1", "status": "ACCEPTED"}], []],
        "B06_ride_get": [{"ride_id": "R1", "driver_id": "DRV_551", "status": "CANCELLED"}],
        SCAN: [[]],
    })
    assert consistency.active_ride_of(db, "DRV_551", NOW) is None


def test_missing_month_row_still_found_by_rides_scan():
    """Ghi bảng phụ lỗi (partial): rides có ACCEPTED nhưng rides_by_driver_month thiếu dòng. Không được coi là kẹt."""
    db = FakeDb({"B10_driver_month": [[], []],
                 SCAN: [[_scan_row("R2", "DRV_551", "ONGOING"), _scan_row("R3", "DRV_552", "ACCEPTED")]]})
    assert consistency.active_ride_of(db, "DRV_551", NOW) == "R2"
    assert [c[1] for c in db.calls if c[0] == "B10_driver_month"] == [("DRV_551", 202610), ("DRV_551", 202609)]


def test_previous_month_of_january_rolls_back_a_year():
    db = FakeDb({SCAN: [[]]})
    consistency.active_ride_of(db, "DRV_551", parse_vn("2027-01-05 08:00"))
    assert [c[1] for c in db.calls if c[0] == "B10_driver_month"] == [("DRV_551", 202701), ("DRV_551", 202612)]


def test_find_stuck_busy_drivers_scans_once_and_reports_only_unmatched():
    d2 = {"driver_id": "DRV_552", "full_name": "B", "status": "BUSY"}
    db = FakeDb({
        "APP03_drivers_scan": [[BUSY, d2, {"driver_id": "DRV_553", "full_name": "C", "status": "AVAILABLE"}]],
        SCAN: [[_scan_row("R9", "DRV_552", "ACCEPTED")]],
    })
    stuck = consistency.find_stuck_busy_drivers(db, NOW)
    assert [s["driver_id"] for s in stuck] == ["DRV_551"]
    assert db.names().count(SCAN) == 1


def test_release_refused_when_driver_has_active_ride():
    db = FakeDb({"B03_driver_get": [dict(BUSY)], "B10_driver_month": [[], []],
                 SCAN: [[_scan_row("R2", "DRV_551", "ACCEPTED")]]})
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert not r.ok and r.code == "driver_busy"
    assert "APP08_driver_release" not in db.names()


def test_release_applies_lwt_only_after_verification_and_rechecks():
    db = FakeDb({"B03_driver_get": [dict(BUSY)], "B10_driver_month": [[], [], [], []], SCAN: [[], []]})
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert r.ok and r.code == "ok"
    names = db.names()
    assert names.index("APP08_driver_release") > names.index(SCAN)
    assert names.count(SCAN) == 2  # xác minh lại sau khi release (chống chạy đua với lệnh nhận chuyến)
    assert "APP07_driver_claim" not in names
    assert dict(db.calls)["APP08_driver_release"] == ("DRV_551",)


def test_release_reclaims_driver_if_ride_appears_during_release():
    db = FakeDb({"B03_driver_get": [dict(BUSY)], "B10_driver_month": [[], [], [], []],
                 SCAN: [[], [_scan_row("R7", "DRV_551", "ACCEPTED")]]})
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert not r.ok and r.code == "lwt_lost"
    names = db.names()
    assert names.index("APP07_driver_claim") > names.index("APP08_driver_release")


def test_release_requires_busy_status_and_known_driver():
    assert consistency.release_stuck_driver(FakeDb(), "DRV_X", NOW).code == "not_found"
    db = FakeDb({"B03_driver_get": [dict(AVAILABLE)]})
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert not r.ok and r.code == "invalid_transition"
    assert "APP08_driver_release" not in db.names()


def test_release_lwt_lost_when_status_changed_meanwhile():
    db = FakeDb({"B03_driver_get": [dict(BUSY)], "B10_driver_month": [[], []], SCAN: [[]],
                 "APP08_driver_release": [LwtResult(False, {"status": "AVAILABLE"})]})
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert not r.ok and r.code == "lwt_lost"


def test_reconcile_writes_secondary_tables_from_rides_only():
    req = parse_vn("2026-10-04 09:00")
    done = parse_vn("2026-10-04 09:40")
    ride = dict(ride_id="R1", customer_id="C1", driver_id="DRV_551", city="HCM", district="Q1", status="COMPLETED",
                ride_date=None, requested_at=req, completed_at=done, fare=50000.0, discount=10000.0,
                payment_method="CASH", pickup_address="a", destination_address="b", distance_km=3.0)
    db = FakeDb({"B06_ride_get": [ride]})
    assert consistency.reconcile(db, "R1") == ["rides_by_customer", "rides_by_area_date",
                                               "rides_by_driver_month", "payments_by_city_date"]
    pay = dict(db.calls)["T08_payment_insert"]
    assert pay[8] == 40000.0 and pay[9] == 10000.0  # amount = fare - discount
    ride2 = dict(ride, driver_id=None, status="REQUESTED", completed_at=None)
    db2 = FakeDb({"B06_ride_get": [ride2]})
    assert consistency.reconcile(db2, "R1") == ["rides_by_customer", "rides_by_area_date"]
    assert consistency.reconcile(FakeDb(), "R_NOPE") == []


def test_recent_active_ride_row_returns_loaded_ride_without_extra_reads():
    db = FakeDb({"B10_driver_month": [[{"ride_id": "RIDE_X", "status": "ONGOING"}]],
                 "B06_ride_get": [{"ride_id": "RIDE_X", "driver_id": "DRV_1", "status": "ONGOING",
                                   "pickup_address": "A"}]})
    row = consistency.recent_active_ride_row(db, "DRV_1", NOW)
    assert row["pickup_address"] == "A"
    assert db.names() == ["B10_driver_month", "B06_ride_get"]
