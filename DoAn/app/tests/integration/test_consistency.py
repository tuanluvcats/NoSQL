"""Kiểm tra nhất quán + reconcile, tài xế kẹt BUSY, trang /admin/consistency. Cassandra thật (_test)."""
from datetime import date

import pytest

from db import trace
from domain.tz import parse_vn
from services import consistency, driver_presence, rides_flow
from services.consistency import Diff
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.nosql]

NOW = parse_vn("2026-10-04 10:00")
T_DONE = parse_vn("2026-10-04 10:40")
D = date(2026, 10, 4)


def test_seed_rides_are_consistent(db):
    """Các bảng phụ của dữ liệu seed khớp rides (nếu seed lệch thì kiểm tra nhất quán báo oan)."""
    bad = {}
    for ride_id in [f"RIDE_{n}" for n in range(1001, 1037)]:
        if db.one("B06_ride_get", [ride_id]) is None:
            continue
        diffs = consistency.check_ride(db, ride_id)
        if diffs:
            bad[ride_id] = diffs
    assert bad == {}


def test_check_ride_missing_ride_reports_row_missing(db):
    assert consistency.check_ride(db, "RIDE_NOPE") == [Diff("rides", "(row)", "present", "missing")]


def test_check_detects_wrong_status_and_reconcile_fixes(db, raw):
    raw.execute("UPDATE rides_by_customer SET status='REQUESTED' "
                "WHERE customer_id='CUST001' AND ride_date='2026-10-03' AND ride_id='RIDE_1001'")
    diffs = consistency.check_ride(db, "RIDE_1001")
    assert Diff("rides_by_customer", "status", "COMPLETED", "REQUESTED") in diffs
    written = consistency.reconcile(db, "RIDE_1001")
    assert written == ["rides_by_customer", "rides_by_area_date", "rides_by_driver_month", "payments_by_city_date"]
    assert consistency.check_ride(db, "RIDE_1001") == []
    # rides vẫn là nguồn đúng, không bị bảng phụ ghi đè
    assert db.one("B06_ride_get", ["RIDE_1001"])["status"] == "COMPLETED"


def test_check_detects_missing_rows_in_every_secondary_table_and_reconcile_restores(db, raw):
    raw.execute("DELETE FROM rides_by_customer WHERE customer_id='CUST001' AND ride_date='2026-10-03' "
                "AND ride_id='RIDE_1001'")
    raw.execute("DELETE FROM rides_by_area_date WHERE city='HCM' AND district='Q1' AND ride_date='2026-10-03' "
                "AND requested_at='2026-10-03 08:15:00+0700' AND ride_id='RIDE_1001'")
    raw.execute("DELETE FROM rides_by_driver_month WHERE driver_id='DRV_555' AND yyyymm=202610 "
                "AND requested_at='2026-10-03 08:15:00+0700' AND ride_id='RIDE_1001'")
    raw.execute("DELETE FROM payments_by_city_date WHERE city='HCM' AND pay_date='2026-10-03' "
                "AND payment_method='CASH' AND paid_at='2026-10-03 08:49:00+0700' AND ride_id='RIDE_1001'")
    diffs = consistency.check_ride(db, "RIDE_1001")
    assert {d.table for d in diffs if d.column == "(row)"} == {
        "rides_by_customer", "rides_by_area_date", "rides_by_driver_month", "payments_by_city_date"}
    assert all(d.expected == "present" and d.actual == "missing" for d in diffs)
    consistency.reconcile(db, "RIDE_1001")
    assert consistency.check_ride(db, "RIDE_1001") == []
    pays = [p for p in db.rows("B15_payments_day", ["HCM", date(2026, 10, 3)]) if p["ride_id"] == "RIDE_1001"]
    assert len(pays) == 1 and pays[0]["amount"] == 85000.0


def test_check_detects_payment_amount_mismatch(db, raw):
    raw.execute("UPDATE payments_by_city_date SET amount=1 WHERE city='HCM' AND pay_date='2026-10-03' "
                "AND payment_method='CASH' AND paid_at='2026-10-03 08:49:00+0700' AND ride_id='RIDE_1001'")
    assert Diff("payments_by_city_date", "amount", 85000.0, 1.0) in consistency.check_ride(db, "RIDE_1001")
    consistency.reconcile(db, "RIDE_1001")
    assert consistency.check_ride(db, "RIDE_1001") == []


class _FailingExecDb:
    """Bọc CassandraDb: một câu exec nào đó ném lỗi (tự tạo lỗi giữa chừng sau khi LWT rides đã applied)."""

    def __init__(self, inner, fail_names):
        self._inner, self._fail = inner, set(fail_names)
        self.keyspace = inner.keyspace

    def exec(self, name, params=()):
        if name in self._fail:
            raise RuntimeError(f"giả lập lỗi ở {name}")
        return self._inner.exec(name, params)

    def __getattr__(self, item):
        return getattr(self._inner, item)


def test_reconcile_repairs_partial_failure_in_the_middle_of_complete(db):
    assert rides_flow.start_ride(db, "RIDE_1023", "DRV_556", None, None, parse_vn("2026-10-04 10:10")).ok
    broken = _FailingExecDb(db, {"T06_rad_status", "T08_payment_insert"})
    r = rides_flow.complete_ride(broken, "RIDE_1023", "DRV_556", "Q1", None, None, T_DONE)
    assert r.ok and r.code == "partial"  # D10: không rollback
    assert db.one("B06_ride_get", ["RIDE_1023"])["status"] == "COMPLETED"  # rides là nguồn đúng
    diffs = consistency.check_ride(db, "RIDE_1023")
    assert Diff("rides_by_area_date", "status", "COMPLETED", "ONGOING") in diffs
    assert Diff("payments_by_city_date", "(row)", "present", "missing") in diffs
    consistency.reconcile(db, "RIDE_1023")
    assert consistency.check_ride(db, "RIDE_1023") == []
    pay = [p for p in db.rows("B15_payments_day", ["HCM", D]) if p["ride_id"] == "RIDE_1023"]
    assert len(pay) == 1 and pay[0]["amount"] == 40000.0  # 50000 - 10000


def test_reconcile_repairs_partial_failure_in_the_middle_of_accept(db):
    """accept: LWT rides applied rồi mà bảng phụ lỗi -> thiếu rides_by_driver_month, rides_by_* còn REQUESTED."""
    broken = _FailingExecDb(db, {"T05_rbc_accept"})
    r = rides_flow.accept_ride(broken, "RIDE_1024", "DRV_551", parse_vn("2026-10-04 10:05"))
    assert r.ok and r.code == "partial", r
    diffs = consistency.check_ride(db, "RIDE_1024")
    assert Diff("rides_by_customer", "status", "ACCEPTED", "REQUESTED") in diffs
    consistency.reconcile(db, "RIDE_1024")
    assert consistency.check_ride(db, "RIDE_1024") == []


def test_check_driver_areas_flags_extra_row_and_status_mismatch(db, raw):
    assert consistency.check_driver_areas(db, "DRV_551") == []
    raw.execute("INSERT INTO drivers_by_area (city, district, driver_id, full_name, rating) "
                "VALUES ('HCM', 'Q1', 'DRV_551', 'Lý Văn Phúc', 4.8)")
    problems = consistency.check_driver_areas(db, "DRV_551")
    assert problems and any("hơn 1" in p for p in problems)
    r = driver_presence.go_offline(db, "DRV_551", NOW)
    assert r.ok
    assert consistency.check_driver_areas(db, "DRV_551") == []
    # một dòng nhưng tài xế không AVAILABLE
    raw.execute("INSERT INTO drivers_by_area (city, district, driver_id, full_name, rating) "
                "VALUES ('HCM', 'Q1', 'DRV_555', 'Nguyễn Hữu Thắng', 4.5)")
    problems = consistency.check_driver_areas(db, "DRV_555")
    assert len(problems) == 1 and "OFFLINE" in problems[0]


# ---------------- tài xế kẹt BUSY ----------------
def test_seed_has_no_stuck_busy_driver(db):
    assert consistency.find_stuck_busy_drivers(db, NOW) == []


def test_busy_driver_without_ride_is_detected_and_released_safely(db):
    """Mô phỏng WriteTimeout kiểu CAS khi nhận chuyến: lệnh claim đã chạy nhưng ride LWT chưa/không chạy."""
    assert db.lwt("APP07_driver_claim", ["DRV_551"]).applied
    stuck = consistency.find_stuck_busy_drivers(db, NOW)
    assert [s["driver_id"] for s in stuck] == ["DRV_551"]
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert r.ok and r.code == "ok", r
    assert db.one("B03_driver_get", ["DRV_551"])["status"] == "AVAILABLE"
    assert consistency.find_stuck_busy_drivers(db, NOW) == []


def test_busy_driver_with_running_ride_is_never_released(db):
    assert db.one("B03_driver_get", ["DRV_556"])["status"] == "BUSY"  # RIDE_1023 đang ACCEPTED
    r = consistency.release_stuck_driver(db, "DRV_556", NOW)
    assert not r.ok and r.code == "driver_busy"
    assert db.one("B03_driver_get", ["DRV_556"])["status"] == "BUSY"
    r = consistency.release_stuck_driver(db, "DRV_552", NOW)  # BUSY có chuyến ONGOING trong seed
    assert not r.ok and r.code == "driver_busy"


def test_missing_driver_month_row_does_not_make_driver_look_stuck(db, raw):
    raw.execute("DELETE FROM rides_by_driver_month WHERE driver_id='DRV_556' AND yyyymm=202610 "
                "AND requested_at='2026-10-04 09:50:00+0700' AND ride_id='RIDE_1023'")
    assert consistency.find_stuck_busy_drivers(db, NOW) == []
    assert not consistency.release_stuck_driver(db, "DRV_556", NOW).ok
    assert db.one("B03_driver_get", ["DRV_556"])["status"] == "BUSY"


def test_release_refused_for_non_busy_driver(db):
    r = consistency.release_stuck_driver(db, "DRV_551", NOW)
    assert not r.ok and r.code == "invalid_transition"
    assert db.one("B03_driver_get", ["DRV_551"])["status"] == "AVAILABLE"


# ---------------- HTTP: phân quyền, trace, thao tác ----------------
def _client(client_factory, user):
    c = client_factory(clock=lambda: NOW)
    assert http_login(c, user).status_code == 303
    return c


def test_consistency_pages_only_for_admin_and_operator(client_factory, db):
    for user in ("cust001", "drv551"):
        c = _client(client_factory, user)
        assert c.get("/admin/consistency").status_code == 403
        for path, data in (("check", {"ride_id": "RIDE_1001"}), ("reconcile", {"ride_id": "RIDE_1001"}),
                           ("backfill", {}), ("driver", {"driver_id": "DRV_551", "action": "release"})):
            assert c.post(f"/admin/consistency/{path}", data=data).status_code == 403
    g = client_factory(clock=lambda: NOW)
    assert g.get("/admin/consistency").status_code == 303
    assert g.post("/admin/consistency/backfill").headers["location"].startswith("/login")
    for user in ("admin", "dieuphoi"):
        assert _client(client_factory, user).get("/admin/consistency").status_code == 200


def test_consistency_page_lists_stuck_driver_and_release_button(client_factory, db):
    db.lwt("APP07_driver_claim", ["DRV_551"])
    c = _client(client_factory, "admin")
    page = c.get("/admin/consistency")
    assert page.status_code == 200 and "DRV_551" in page.text
    r = c.post("/admin/consistency/driver", data={"driver_id": "DRV_551", "action": "release"})
    assert r.status_code == 303
    assert db.one("B03_driver_get", ["DRV_551"])["status"] == "AVAILABLE"
    # tài xế đang chạy không bị giải phóng qua HTTP
    c.post("/admin/consistency/driver", data={"driver_id": "DRV_556", "action": "release"})
    assert db.one("B03_driver_get", ["DRV_556"])["status"] == "BUSY"


def test_consistency_check_and_reconcile_over_http_write_trace(client_factory, db, raw):
    raw.execute("UPDATE rides_by_customer SET status='REQUESTED' "
                "WHERE customer_id='CUST001' AND ride_date='2026-10-03' AND ride_id='RIDE_1001'")
    c = _client(client_factory, "dieuphoi")
    page = c.post("/admin/consistency/check", data={"ride_id": "RIDE_1001"})
    assert page.status_code == 200 and "rides_by_customer" in page.text and "REQUESTED" in page.text
    r = c.post("/admin/consistency/reconcile", data={"ride_id": "RIDE_1001"})
    assert r.status_code == 303 and r.headers["location"].startswith("/admin/consistency")
    assert consistency.check_ride(db, "RIDE_1001") == []
    after = c.get("/admin/consistency")  # trace của thao tác vừa rồi được giữ qua PRG
    assert "CQL của thao tác vừa rồi" in after.text and "T04" in after.text and "rides_by_customer" in after.text
    assert c.post("/admin/consistency/reconcile", data={"ride_id": "RIDE_NOPE"}).status_code == 303


def test_consistency_actions_record_trace_entries(db):
    trace.start_request()
    consistency.reconcile(db, "RIDE_1001")
    names = {e.name for e in trace.current()}
    assert {"B06_ride_get", "T04_rbc_insert", "T04_rad_insert", "T05_rdm_insert", "T08_payment_insert"} <= names
    trace.start_request()
    db.lwt("APP07_driver_claim", ["DRV_551"])
    consistency.release_stuck_driver(db, "DRV_551", NOW)
    names = [e.name for e in trace.current()]
    assert "APP08_driver_release" in names and "APP27_rides_by_driver_scan" in names


def test_backfill_button_over_http(client_factory, db, raw):
    raw.execute("UPDATE rides SET rated_at = null WHERE ride_id = 'RIDE_1001'")
    c = _client(client_factory, "admin")
    r = c.post("/admin/consistency/backfill")
    assert r.status_code == 303
    assert db.one("B06_ride_get", ["RIDE_1001"])["rated_at"] is not None
