"""Bắt đầu / hoàn thành + thanh toán / hủy chuyến trên Cassandra thật (ride_booking_test)."""
from datetime import date

import pytest

from db import trace
from domain.ids import new_ride_id
from domain.tz import parse_vn
from domain.write_matrix import WRITE_MATRIX
from services import booking, driver_presence, rides_flow
from services.booking import BookingForm

pytestmark = [pytest.mark.business, pytest.mark.nosql]

T_START = parse_vn("2026-10-04 10:10")
T_DONE = parse_vn("2026-10-04 10:40")
D = date(2026, 10, 4)
CUST5 = {"role": "CUSTOMER", "ref_id": "CUST005", "username": "cust005"}
CUST3 = {"role": "CUSTOMER", "ref_id": "CUST003", "username": "cust003"}
CUST6 = {"role": "CUSTOMER", "ref_id": "CUST006", "username": "cust006"}


def _driver_status(db, driver_id):
    return db.one("B03_driver_get", [driver_id])["status"]


def _rbc(db, customer_id, ride_id, day=D):
    return [r for r in db.rows("B07_customer_history", [customer_id])
            if r["ride_id"] == ride_id and r["ride_date"] == day][0]


def _rad(db, city, district, ride_id, day=D):
    return [r for r in db.rows("B11_area_day", [city, district, day]) if r["ride_id"] == ride_id][0]


def _rdm(db, driver_id, ym, ride_id):
    rows = [r for r in db.rows("B10_driver_month", [driver_id, ym]) if r["ride_id"] == ride_id]
    return rows[0] if rows else None


def _payments(db, city, day, ride_id):
    return [p for p in db.rows("B15_payments_day", [city, day]) if p["ride_id"] == ride_id]


def _drivers_snapshot(db):
    return {d: _driver_status(db, d) for d in ("DRV_551", "DRV_552", "DRV_553", "DRV_554", "DRV_555", "DRV_556")}


def _book(db, customer_id, clock, rand="AAAA", promo=None, distance=3.0, district="TAN_PHU"):
    f = BookingForm(ride_id=new_ride_id(clock, rand=lambda: rand), city="HCM", district=district,
                    pickup_address="456 Lê Duẩn, Q1", destination_address="Sân bay Tân Sơn Nhất, Tân Bình",
                    distance_km=distance, payment_method="MOMO", promo_code=promo)
    r = booking.book_ride(db, customer_id, f, clock)
    assert r.ok, r
    return f.ride_id


class _FirstReadStaleDb:
    """Bọc CassandraDb: lần B06 đầu trả bản chụp cũ (REQUESTED), các lần sau đọc thật (ép hủy chạy đua với nhận)."""

    def __init__(self, inner, stale):
        self._inner, self._stale, self._used = inner, stale, False
        self.keyspace = inner.keyspace

    def one(self, name, params=()):
        if name == "B06_ride_get" and not self._used:
            self._used = True
            return dict(self._stale)
        return self._inner.one(name, params)

    def __getattr__(self, item):
        return getattr(self._inner, item)


# ---------------- start ----------------
def test_start_by_other_driver_forbidden(db):
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_555", None, None, T_START)
    assert not r.ok and r.code == "forbidden"
    assert db.one("B06_ride_get", ["RIDE_1023"])["status"] == "ACCEPTED"


def test_start_updates_every_table_per_matrix(db):
    trace.start_request()
    r = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", 10.8270, 106.6880, T_START)
    written = set(trace.tables_written(trace.current()))
    assert r.ok and r.code == "ok", r
    assert set(WRITE_MATRIX["start"]["required"]) <= written
    ride = db.one("B06_ride_get", ["RIDE_1023"])
    assert ride["status"] == "ONGOING" and ride["started_at"] is not None and len(ride["status_history"]) == 3
    assert _rbc(db, "CUST005", "RIDE_1023")["status"] == "ONGOING"
    assert _rad(db, "HCM", "GO_VAP", "RIDE_1023")["status"] == "ONGOING"
    assert _rdm(db, "DRV_556", 202610, "RIDE_1023")["status"] == "ONGOING"
    assert db.one("B13_location_latest", ["DRV_556", D])["lat"] == 10.827
    assert _driver_status(db, "DRV_556") == "BUSY"


def test_start_twice_second_is_invalid_transition(db):
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, T_START).ok
    again = rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, T_START)
    assert not again.ok and again.code == "invalid_transition"
    assert len(db.one("B06_ride_get", ["RIDE_1023"])["status_history"]) == 3


# ---------------- complete ----------------
def test_complete_updates_every_table_and_driver_back_in_one_area(db):
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", 10.8270, 106.6880, T_START).ok
    trace.start_request()
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", 10.8185, 106.6588, T_DONE)
    written = set(trace.tables_written(trace.current()))
    assert r.ok and r.code == "ok", r
    assert set(WRITE_MATRIX["complete"]["required"]) <= written
    ride = db.one("B06_ride_get", ["RIDE_1023"])
    assert ride["status"] == "COMPLETED" and ride["completed_at"] is not None and len(ride["status_history"]) == 4
    assert _rbc(db, "CUST005", "RIDE_1023")["status"] == "COMPLETED"
    assert _rad(db, "HCM", "GO_VAP", "RIDE_1023")["status"] == "COMPLETED"
    assert _rdm(db, "DRV_556", 202610, "RIDE_1023")["status"] == "COMPLETED"
    pays = _payments(db, "HCM", D, "RIDE_1023")
    assert len(pays) == 1 and pays[0]["payment_method"] == "MOMO"
    assert pays[0]["amount"] == ride["fare"] - ride["discount"] == 40000.0 and pays[0]["discount"] == 10000.0
    assert pays[0]["district"] == "GO_VAP" and pays[0]["driver_id"] == "DRV_556" and pays[0]["customer_id"] == "CUST005"
    assert _driver_status(db, "DRV_556") == "AVAILABLE"
    rows = driver_presence.find_area_rows(db, "DRV_556")
    assert [(x["city"], x["district"]) for x in rows] == [("HCM", "TAN_BINH")]  # đúng một khu vực
    assert [x["driver_id"] for x in db.rows("B12_area_drivers", ["HCM", "TAN_BINH"])] == ["DRV_556"]


def test_full_flow_fare_81000_discount_16000_pays_65000(db):
    clock = parse_vn("2026-10-04 10:05")
    rid = _book(db, "CUST001", clock, rand="F081", promo="GIAM20", distance=8.1, district="Q1")
    assert rides_flow.accept_ride(db, rid, "DRV_551", parse_vn("2026-10-04 10:06")).ok
    assert rides_flow.start_ride(db, rid, "DRV_551", None, None, T_START).ok
    assert rides_flow.complete_ride(db, rid, "DRV_551", "Q3", None, None, T_DONE).ok
    ride = db.one("B06_ride_get", [rid])
    assert (ride["fare"], ride["discount"]) == (81000.0, 16000.0)
    pays = _payments(db, "HCM", D, rid)
    assert len(pays) == 1 and pays[0]["amount"] == 65000.0 and pays[0]["discount"] == 16000.0
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6  # hoàn thành không trả lượt
    rows = driver_presence.find_area_rows(db, "DRV_551")
    assert [(x["city"], x["district"]) for x in rows] == [("HCM", "Q3")]


def test_complete_payment_date_and_month_use_plus07(db):
    clock = parse_vn("2026-11-01 06:30")
    rid = _book(db, "CUST002", clock, rand="BEEF")
    assert rides_flow.accept_ride(db, rid, "DRV_551", parse_vn("2026-11-01 06:32")).ok
    assert rides_flow.start_ride(db, rid, "DRV_551", None, None, parse_vn("2026-11-01 06:35")).ok
    assert rides_flow.complete_ride(db, rid, "DRV_551", "Q1", None, None, parse_vn("2026-11-01 06:40")).ok
    assert len(_payments(db, "HCM", date(2026, 11, 1), rid)) == 1
    assert _payments(db, "HCM", date(2026, 10, 31), rid) == []  # theo UTC sẽ là 31/10
    assert _rdm(db, "DRV_551", 202611, rid)["status"] == "COMPLETED"
    assert _rdm(db, "DRV_551", 202610, rid) is None
    assert _rbc(db, "CUST002", rid, date(2026, 11, 1))["status"] == "COMPLETED"


def test_complete_only_from_ongoing_and_only_once(db):
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, T_DONE)  # đang ACCEPTED
    assert not r.ok and r.code == "invalid_transition"
    assert db.one("B06_ride_get", ["RIDE_1023"])["status"] == "ACCEPTED"
    assert _payments(db, "HCM", D, "RIDE_1023") == [] and _driver_status(db, "DRV_556") == "BUSY"
    r = rides_flow.complete_ride(db, "RIDE_1001", "DRV_551", "Q1", None, None, T_DONE)  # đã COMPLETED
    assert not r.ok and r.code in ("invalid_transition", "forbidden")
    # hoàn thành hai lần: chỉ một khoản thanh toán
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, T_START).ok
    assert rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, T_DONE).ok
    again = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "TAN_BINH", None, None, T_DONE)
    assert not again.ok and again.code == "invalid_transition"
    assert len(_payments(db, "HCM", D, "RIDE_1023")) == 1


def test_complete_by_other_driver_and_bad_district_change_nothing(db):
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, T_START).ok
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_555", "TAN_BINH", None, None, T_DONE)
    assert not r.ok and r.code == "forbidden"
    r = rides_flow.complete_ride(db, "RIDE_1023", "DRV_556", "XYZ", None, None, T_DONE)
    assert not r.ok and r.code == "invalid_input"
    assert db.one("B06_ride_get", ["RIDE_1023"])["status"] == "ONGOING"
    assert _payments(db, "HCM", D, "RIDE_1023") == [] and _driver_status(db, "DRV_556") == "BUSY"


# ---------------- cancel ----------------
def test_cancel_ongoing_rejected(db):
    before = db.one("B06_ride_get", ["RIDE_1022"])
    r = rides_flow.cancel_ride(db, "RIDE_1022", CUST3, "đổi ý", T_START)
    assert not r.ok and r.code == "invalid_transition" and r.current["status"] == "ONGOING"
    assert db.one("B06_ride_get", ["RIDE_1022"]) == before
    assert _driver_status(db, "DRV_552") == "BUSY"


def test_cancel_accepted_releases_driver_and_promo_slot(db):
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 5
    trace.start_request()
    r = rides_flow.cancel_ride(db, "RIDE_1023", CUST5, "Đổi kế hoạch", T_START)
    written = set(trace.tables_written(trace.current()))
    assert r.ok and r.code == "ok", r
    assert set(WRITE_MATRIX["cancel"]["required"]) <= written
    assert {"rides_by_driver_month", "drivers", "drivers_by_area", "promotions"} <= written
    ride = db.one("B06_ride_get", ["RIDE_1023"])
    assert ride["status"] == "CANCELLED" and ride["cancel_reason"] == "Đổi kế hoạch"
    assert _rbc(db, "CUST005", "RIDE_1023")["status"] == "CANCELLED"
    assert _rad(db, "HCM", "GO_VAP", "RIDE_1023")["status"] == "CANCELLED"
    assert _rdm(db, "DRV_556", 202610, "RIDE_1023")["status"] == "CANCELLED"
    assert _driver_status(db, "DRV_556") == "AVAILABLE"
    assert [x["driver_id"] for x in db.rows("B12_area_drivers", ["HCM", "GO_VAP"])] == ["DRV_556"]
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 4
    assert _payments(db, "HCM", D, "RIDE_1023") == []


def test_cancel_requested_touches_no_driver(db):
    before = _drivers_snapshot(db)
    r = rides_flow.cancel_ride(db, "RIDE_1024", CUST6, "", T_START)
    assert r.ok
    ride = db.one("B06_ride_get", ["RIDE_1024"])
    assert ride["status"] == "CANCELLED" and ride["cancel_reason"] == "Khách hủy"
    assert _rbc(db, "CUST006", "RIDE_1024")["status"] == "CANCELLED"
    assert _rad(db, "HCM", "TAN_PHU", "RIDE_1024")["status"] == "CANCELLED"
    assert _drivers_snapshot(db) == before
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 5  # chuyến không có mã
    assert driver_presence.waiting_rides(db, "HCM", "TAN_PHU", D) == []


def test_cancel_requested_with_promo_gives_slot_back(db):
    rid = _book(db, "CUST001", parse_vn("2026-10-04 10:05"), rand="C0DE", promo="GIAM20", distance=8.1,
                district="Q1")
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6
    actor = {"role": "CUSTOMER", "ref_id": "CUST001", "username": "cust001"}
    assert rides_flow.cancel_ride(db, rid, actor, "x", T_START).ok
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 5


def test_cancel_race_with_accept_does_not_leave_driver_busy(db):
    """Hủy chạy đua với nhận chuyến trên dữ liệu thật: khách đọc REQUESTED, tài xế nhận xong, rồi LWT hủy thua và đọc lại."""
    stale = db.one("B06_ride_get", ["RIDE_1024"])
    assert rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", parse_vn("2026-10-04 10:04")).ok
    assert _driver_status(db, "DRV_551") == "BUSY"
    r = rides_flow.cancel_ride(_FirstReadStaleDb(db, stale), "RIDE_1024", CUST6, "x", T_START)
    assert r.ok, r
    assert db.one("B06_ride_get", ["RIDE_1024"])["status"] == "CANCELLED"
    assert _driver_status(db, "DRV_551") == "AVAILABLE"
    assert [x["district"] for x in driver_presence.find_area_rows(db, "DRV_551")] == ["TAN_PHU"]
    assert _rdm(db, "DRV_551", 202610, "RIDE_1024")["status"] == "CANCELLED"


def test_cancel_twice_second_is_invalid_transition(db):
    assert rides_flow.cancel_ride(db, "RIDE_1023", CUST5, "x", T_START).ok
    again = rides_flow.cancel_ride(db, "RIDE_1023", CUST5, "x", T_START)
    assert not again.ok and again.code == "invalid_transition"
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 4  # chỉ trả một lần


def test_cancel_by_other_customer_forbidden(db):
    actor = {"role": "CUSTOMER", "ref_id": "CUST001", "username": "cust001"}
    r = rides_flow.cancel_ride(db, "RIDE_1024", actor, "x", T_START)
    assert not r.ok and r.code == "forbidden"
    assert db.one("B06_ride_get", ["RIDE_1024"])["status"] == "REQUESTED"
