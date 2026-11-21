"""Bắt đầu / hoàn thành + thanh toán / hủy chuyến (unit, FakeDb)."""
from datetime import date

import pytest

from db.catalog import STATEMENTS
from db.repo import LwtResult
from domain.tz import parse_vn
from domain.write_matrix import WRITE_MATRIX
from services import rides_flow
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
REQ = parse_vn("2026-10-04 09:50")

ACCEPTED = dict(ride_id="RIDE_1023", customer_id="CUST005", driver_id="DRV_556", driver_name="Mai Xuân Trường",
                vehicle_plate="59T2-678.90", city="HCM", district="GO_VAP", pickup_address="Emart Gò Vấp",
                destination_address="Sân bay Tân Sơn Nhất", distance_km=4.5, fare=50000.0, discount=10000.0,
                promo_code="GIAM20", payment_method="MOMO", status="ACCEPTED", ride_date=date(2026, 10, 4),
                requested_at=REQ)
ONGOING = dict(ACCEPTED, status="ONGOING")
REQUESTED = dict(ACCEPTED, status="REQUESTED", driver_id=None, driver_name=None, vehicle_plate=None)
DRIVER = dict(driver_id="DRV_556", full_name="Mai Xuân Trường", phone="0912000556", rating=4.0, status="AVAILABLE")

CUSTOMER_ACTOR = {"role": "CUSTOMER", "ref_id": "CUST005", "username": "cust005"}


def _written_tables(db):
    return {STATEMENTS[n].table for n in db.names() if STATEMENTS[n].kind in ("write", "lwt")}


# ---------------- start ----------------
def test_start_win_branch_order_params_and_matrix():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", 10.827, 106.688, NOW)
    assert r.ok and r.code == "ok"
    assert db.names() == ["B06_ride_get", "T06_ride_start", "T06_rbc_status", "T06_rad_status",
                          "T06_rdm_status", "T03_location_insert"]
    calls = dict(db.calls)
    assert calls["T06_ride_start"] == (NOW, {NOW: "ONGOING"}, "RIDE_1023", "DRV_556")  # AND driver_id
    assert calls["T06_rbc_status"] == ("ONGOING", "CUST005", date(2026, 10, 4), "RIDE_1023")
    assert calls["T06_rad_status"] == ("ONGOING", "HCM", "GO_VAP", date(2026, 10, 4), REQ, "RIDE_1023")
    assert calls["T06_rdm_status"] == ("ONGOING", "DRV_556", 202610, REQ, "RIDE_1023")
    assert calls["T03_location_insert"] == ("DRV_556", date(2026, 10, 4), NOW, 10.827, 106.688, 0.0)
    assert set(WRITE_MATRIX["start"]["required"]) <= _written_tables(db)


def test_start_without_coordinates_skips_location():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)]})
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, NOW).ok
    assert "T03_location_insert" not in db.names()


def test_start_month_bucket_uses_plus07():
    late = dict(ACCEPTED, requested_at=parse_vn("2026-11-01 06:30"), ride_date=date(2026, 11, 1))
    db = FakeDb({"B06_ride_get": [late]})
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, parse_vn("2026-11-01 06:40")).ok
    assert dict(db.calls)["T06_rdm_status"][2] == 202611


def test_start_by_other_driver_forbidden():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_555", None, None, NOW)
    assert not r.ok and r.code == "forbidden"
    assert db.names() == ["B06_ride_get"]


def test_start_missing_wrong_status_and_lost():
    db = FakeDb({"B06_ride_get": [None]})
    assert rides_flow.start_ride(db, "RIDE_X", "DRV_556", None, None, NOW).code == "not_found"
    db = FakeDb({"B06_ride_get": [dict(ONGOING)]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, NOW)
    assert not r.ok and r.code == "invalid_transition" and db.names() == ["B06_ride_get"]
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)], "T06_ride_start": [LwtResult(False, {"status": "CANCELLED"})]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", 10.0, 106.0, NOW)
    assert not r.ok and r.code == "lwt_lost" and r.current == {"status": "CANCELLED"}
    assert db.names() == ["B06_ride_get", "T06_ride_start"]


def test_start_invalid_coordinates_rejected_before_lwt():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", 120.0, 106.0, NOW)
    assert not r.ok and r.code == "invalid_input" and "T06_ride_start" not in db.names()


def test_start_secondary_failure_is_partial():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)], "T06_rad_status": [RuntimeError("boom")]})
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, NOW)
    assert r.ok and r.code == "partial"
    assert "T06_rdm_status" in db.names()  # các bảng còn lại vẫn được cập nhật


# ---------------- complete ----------------
def _complete_db(ride=None, **extra):
    responses = {"B06_ride_get": [dict(ride or ONGOING)], "B03_driver_get": [dict(DRIVER)]}
    responses.update(extra)
    return FakeDb(responses)


def test_complete_invalid_drop_district_rejected_before_any_lwt():
    db = _complete_db()
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "XYZ", None, None, NOW)
    assert not r.ok and r.code == "invalid_input"
    assert "T08_ride_complete" not in db.names()
    assert not any(STATEMENTS[n].kind in ("write", "lwt") for n in db.names())


def test_complete_win_branch_order_money_and_matrix():
    db = _complete_db()
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", 10.8185, 106.6588, NOW)
    assert r.ok and r.code == "ok"
    assert db.names() == ["B06_ride_get", "T08_ride_complete", "T06_rbc_status", "T06_rad_status",
                          "T06_rdm_status", "T08_payment_insert", "APP08_driver_release", "B03_driver_get",
                          "T03_area_insert"]
    calls = dict(db.calls)
    assert calls["T08_ride_complete"] == (NOW, {NOW: "COMPLETED"}, "RIDE_1023", "DRV_556")
    assert calls["T06_rbc_status"][0] == "COMPLETED" and calls["T06_rdm_status"][0] == "COMPLETED"
    # amount = fare - discount lấy từ dòng rides; pay_date theo +07; city/district từ rides
    assert calls["T08_payment_insert"] == ("HCM", date(2026, 10, 4), "MOMO", NOW, "RIDE_1023", "CUST005",
                                           "DRV_556", "GO_VAP", 40000.0, 10000.0)
    assert calls["APP08_driver_release"] == ("DRV_556",)
    assert calls["T03_area_insert"] == ("HCM", "TAN_BINH", "DRV_556", "Mai Xuân Trường", "0912000556", 4.0,
                                        "59T2-678.90", 10.8185, 106.6588, NOW)
    assert set(WRITE_MATRIX["complete"]["required"]) <= _written_tables(db)


def test_complete_payment_date_is_plus07_not_utc():
    late = dict(ONGOING, requested_at=parse_vn("2026-11-01 06:30"), ride_date=date(2026, 11, 1))
    db = _complete_db(late)
    assert rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None,
                                    parse_vn("2026-11-01 06:40")).ok  # 2026-10-31 23:40 UTC
    assert dict(db.calls)["T08_payment_insert"][1] == date(2026, 11, 1)


def test_complete_null_discount_pays_full_fare():
    db = _complete_db(dict(ONGOING, discount=None))
    assert rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, NOW).ok
    pay = dict(db.calls)["T08_payment_insert"]
    assert pay[8] == 50000.0 and pay[9] == 0.0


def test_complete_forbidden_wrong_status_missing_and_lost():
    db = _complete_db()
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_555", "TAN_BINH", None, None, NOW)
    assert not r.ok and r.code == "forbidden" and "T08_ride_complete" not in db.names()
    db = _complete_db(ACCEPTED)
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, NOW)
    assert not r.ok and r.code == "invalid_transition" and "T08_ride_complete" not in db.names()
    db = FakeDb({"B06_ride_get": [None]})
    assert rides_flow.complete_ride(db, "RIDE_X", "DRV_556", "TAN_BINH", None, None, NOW).code == "not_found"
    db = _complete_db(T08_ride_complete=[LwtResult(False, {"status": "COMPLETED"})])
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, NOW)
    assert not r.ok and r.code == "lwt_lost"
    assert db.names() == ["B06_ride_get", "T08_ride_complete"]  # thua LWT: không ghi gì thêm, không trả tài xế


def test_complete_secondary_failure_is_partial_but_still_releases_driver():
    db = _complete_db(T08_payment_insert=[RuntimeError("boom")])
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, NOW)
    assert r.ok and r.code == "partial"
    assert "APP08_driver_release" in db.names() and "T03_area_insert" in db.names()


# ---------------- cancel ----------------
def test_cancel_rereads_when_status_changed_and_releases_driver():
    """Review Focus 2: hủy chạy đua với nhận chuyến không để tài xế kẹt BUSY."""
    db = FakeDb({
        "B06_ride_get": [dict(REQUESTED), dict(ACCEPTED)],
        "T10_ride_cancel": [LwtResult(False, {"status": "ACCEPTED"}), LwtResult(True, None)],
        "B03_driver_get": [dict(DRIVER)],
        "B16_promo_get": [{"used_count": 5}],
    })
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "đổi ý", NOW)
    assert r.ok and r.code == "ok"
    t10 = [p for n, p in db.calls if n == "T10_ride_cancel"]
    assert len(t10) == 2
    assert t10[0][-1] == "REQUESTED" and t10[1][-1] == "ACCEPTED"  # IF status = <trạng thái vừa đọc>
    assert t10[1][0] == "đổi ý" and t10[1][1] == {NOW: "CANCELLED"} and t10[1][2] == "RIDE_1023"
    names = db.names()
    assert "APP08_driver_release" in names and "T03_area_insert" in names
    assert dict(db.calls)["APP08_driver_release"] == ("DRV_556",)  # driver_id lấy từ lần đọc lại
    assert dict(db.calls)["T06_rdm_status"] == ("CANCELLED", "DRV_556", 202610, REQ, "RIDE_1023")
    assert dict(db.calls)["T03_area_insert"] == ("HCM", "GO_VAP", "DRV_556", "Mai Xuân Trường", "0912000556",
                                                 4.0, "59T2-678.90", None, None, NOW)
    assert names.index("T10_ride_cancel") < names.index("APP08_driver_release")


def test_cancel_accepted_releases_promo_and_matches_matrix():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)], "B03_driver_get": [dict(DRIVER)],
                 "B16_promo_get": [{"used_count": 5}]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "", NOW)
    assert r.ok
    calls = dict(db.calls)
    assert calls["T10_ride_cancel"][0] == "Khách hủy"  # lý do rỗng -> mặc định
    assert calls["T07_promo_use"] == (4, "GIAM20", 5)  # trả lượt
    assert calls["T06_rbc_status"] == ("CANCELLED", "CUST005", date(2026, 10, 4), "RIDE_1023")
    assert calls["T06_rad_status"] == ("CANCELLED", "HCM", "GO_VAP", date(2026, 10, 4), REQ, "RIDE_1023")
    written = _written_tables(db)
    assert set(WRITE_MATRIX["cancel"]["required"]) <= written
    assert {"rides_by_driver_month", "drivers", "drivers_by_area", "promotions"} <= written


def test_cancel_requested_touches_no_driver_tables():
    db = FakeDb({"B06_ride_get": [dict(REQUESTED, promo_code=None)]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "x", NOW)
    assert r.ok
    assert db.names() == ["B06_ride_get", "T10_ride_cancel", "T06_rbc_status", "T06_rad_status"]
    assert _written_tables(db) == {"rides", "rides_by_customer", "rides_by_area_date"}


def test_cancel_ongoing_and_completed_rejected_before_lwt():
    for status in ("ONGOING", "COMPLETED", "CANCELLED"):
        db = FakeDb({"B06_ride_get": [dict(ACCEPTED, status=status)]})
        r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "x", NOW)
        assert not r.ok and r.code == "invalid_transition" and r.current == {"status": status}
        assert db.names() == ["B06_ride_get"]


def test_cancel_authorization():
    other = {"role": "CUSTOMER", "ref_id": "CUST001", "username": "cust001"}
    db = FakeDb({"B06_ride_get": [dict(REQUESTED)]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", other, "x", NOW)
    assert not r.ok and r.code == "forbidden" and db.names() == ["B06_ride_get"]
    # tài xế khác không được hủy; tài xế của chuyến hủy được khi ACCEPTED
    stranger = {"role": "DRIVER", "ref_id": "DRV_551", "username": "drv551"}
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)]})
    assert rides_flow.cancel_ride(db, "RIDE_1023", stranger, "x", NOW).code == "forbidden"
    owner_driver = {"role": "DRIVER", "ref_id": "DRV_556", "username": "drv556"}
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)], "B03_driver_get": [dict(DRIVER)],
                 "B16_promo_get": [{"used_count": 1}]})
    assert rides_flow.cancel_ride(db, "RIDE_1023", owner_driver, "x", NOW).ok
    admin = {"role": "OPERATOR", "ref_id": None, "username": "dieuphoi"}  # OPERATOR gộp vào ADMIN
    db = FakeDb({"B06_ride_get": [dict(REQUESTED, promo_code=None)]})
    assert rides_flow.cancel_ride(db, "RIDE_1023", admin, "x", NOW).ok


def test_cancel_missing_and_invalid_reason():
    db = FakeDb({"B06_ride_get": [None]})
    assert rides_flow.cancel_ride(db, "RIDE_X", CUSTOMER_ACTOR, "x", NOW).code == "not_found"
    db = FakeDb({"B06_ride_get": [dict(REQUESTED)]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "a" * 201, NOW)
    assert not r.ok and r.code == "invalid_input" and "T10_ride_cancel" not in db.names()


def test_cancel_lost_twice_returns_lwt_lost_without_secondary_writes():
    db = FakeDb({"B06_ride_get": [dict(REQUESTED), dict(REQUESTED)],
                 "T10_ride_cancel": [LwtResult(False, {"status": "ACCEPTED"}), LwtResult(False, {"status": "ACCEPTED"})]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "x", NOW)
    assert not r.ok and r.code == "lwt_lost" and r.current == {"status": "ACCEPTED"}
    assert db.names() == ["B06_ride_get", "T10_ride_cancel", "B06_ride_get", "T10_ride_cancel"]


def test_cancel_secondary_failure_is_partial_but_driver_is_still_released():
    db = FakeDb({"B06_ride_get": [dict(ACCEPTED)], "B03_driver_get": [dict(DRIVER)],
                 "T06_rbc_status": [RuntimeError("boom")], "B16_promo_get": [{"used_count": 5}]})
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUSTOMER_ACTOR, "x", NOW)
    assert r.ok and r.code == "partial"
    assert "APP08_driver_release" in db.names() and "T07_promo_use" in db.names()
