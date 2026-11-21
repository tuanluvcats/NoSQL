"""Phân quyền HTTP cho start/complete/cancel: IDOR, khóa tài khoản, PRG."""
import pytest

from domain.tz import parse_vn
from services import accounts
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.auth]

NOW = parse_vn("2026-10-04 10:10")


def _clock():
    return NOW


def _status(db, ride_id):
    return db.one("B06_ride_get", [ride_id])["status"]


def test_other_customer_cannot_view_or_cancel_ride(client_factory, db):
    """Review Focus 5 (IDOR)."""
    c = client_factory(clock=_clock)
    assert http_login(c, "cust001").status_code == 303
    assert c.get("/rides/RIDE_1024").status_code == 403
    r = c.post("/rides/RIDE_1024/cancel", data={"reason": "phá"})
    assert r.status_code == 403
    assert _status(db, "RIDE_1024") == "REQUESTED"
    d = client_factory(clock=_clock)
    assert http_login(d, "drv551").status_code == 303
    r = d.post("/rides/RIDE_1023/start", data={"lat": "", "lng": ""})
    assert r.status_code == 403
    assert _status(db, "RIDE_1023") == "ACCEPTED"


def test_other_driver_cannot_complete_and_customer_cannot_start(client_factory, db):
    d = client_factory(clock=_clock)
    http_login(d, "drv556")
    assert d.post("/rides/RIDE_1023/start", data={}).status_code == 303
    assert _status(db, "RIDE_1023") == "ONGOING"
    other = client_factory(clock=_clock)
    http_login(other, "drv551")
    r = other.post("/rides/RIDE_1023/complete", data={"drop_district": "Q1"})
    assert r.status_code == 403 and _status(db, "RIDE_1023") == "ONGOING"
    cust = client_factory(clock=_clock)
    http_login(cust, "cust005")
    assert cust.post("/rides/RIDE_1023/complete", data={"drop_district": "Q1"}).status_code == 403
    assert cust.post("/rides/RIDE_1023/start", data={}).status_code == 403
    assert _status(db, "RIDE_1023") == "ONGOING"


def test_guest_is_redirected_to_login(client_factory, db):
    g = client_factory(clock=_clock)
    for path in ("start", "complete", "cancel"):
        r = g.post(f"/rides/RIDE_1023/{path}", data={"drop_district": "Q1"})
        assert r.status_code == 303 and r.headers["location"].startswith("/login")
    assert _status(db, "RIDE_1023") == "ACCEPTED"


def test_locked_customer_cannot_cancel(client_factory, db):
    c = client_factory(clock=_clock)
    assert http_login(c, "cust006").status_code == 303
    assert accounts.set_account_active(db, "cust006", False, "admin", NOW).ok
    r = c.post("/rides/RIDE_1024/cancel", data={"reason": "x"})
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    assert _status(db, "RIDE_1024") == "REQUESTED"


def test_locked_driver_cannot_start(client_factory, db, raw):
    c = client_factory(clock=_clock)
    assert http_login(c, "drv556").status_code == 303
    # tài xế đang BUSY thì service từ chối khóa, nên khóa trực tiếp bản ghi tài khoản để kiểm tra chặn mỗi request
    raw.execute("UPDATE user_accounts SET is_active = false WHERE username = 'drv556'")
    r = c.post("/rides/RIDE_1023/start", data={})
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    assert _status(db, "RIDE_1023") == "ACCEPTED"


def test_customer_cancels_own_ride_via_http_and_sees_trace(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "cust006")
    r = c.post("/rides/RIDE_1024/cancel", data={"reason": "Đổi ý"})
    assert r.status_code == 303 and r.headers["location"] == "/rides/RIDE_1024"
    page = c.get("/rides/RIDE_1024")
    assert page.status_code == 200 and "CANCELLED" in page.text and "Đổi ý" in page.text
    assert "CQL của thao tác vừa rồi" in page.text and "T10" in page.text
    assert "WRITE_MATRIX[cancel]" in page.text and "thiếu" not in page.text
    again = c.post("/rides/RIDE_1024/cancel", data={"reason": "lần hai"})
    assert again.status_code == 303  # không còn hủy được: flash lỗi, không đổi gì
    assert db.one("B06_ride_get", ["RIDE_1024"])["cancel_reason"] == "Đổi ý"


def test_driver_flow_over_http_start_then_complete(client_factory, db):
    d = client_factory(clock=_clock)
    http_login(d, "drv556")
    page = d.get("/rides/RIDE_1023")
    assert page.status_code == 200 and "/rides/RIDE_1023/start" in page.text
    r = d.post("/rides/RIDE_1023/start", data={"lat": "10.827", "lng": "106.688"})
    assert r.status_code == 303 and r.headers["location"] == "/rides/RIDE_1023"
    page = d.get("/rides/RIDE_1023")
    assert "ONGOING" in page.text and "WRITE_MATRIX[start]" in page.text and "thiếu" not in page.text
    assert "/rides/RIDE_1023/complete" in page.text and "drop_district" in page.text
    bad = d.post("/rides/RIDE_1023/complete", data={"drop_district": "XYZ"})
    assert bad.status_code in (303, 400) and _status(db, "RIDE_1023") == "ONGOING"
    r = d.post("/rides/RIDE_1023/complete", data={"drop_district": "TAN_BINH", "lat": "10.8185", "lng": "106.6588"})
    assert r.status_code == 303 and r.headers["location"] == "/rides/RIDE_1023"
    page = d.get("/rides/RIDE_1023")
    assert "COMPLETED" in page.text and "WRITE_MATRIX[complete]" in page.text and "thiếu" not in page.text
    assert db.one("B03_driver_get", ["DRV_556"])["status"] == "AVAILABLE"


def test_start_with_non_numeric_coordinates_is_rejected(client_factory, db):
    d = client_factory(clock=_clock)
    http_login(d, "drv556")
    r = d.post("/rides/RIDE_1023/start", data={"lat": "abc", "lng": "1"})
    assert r.status_code in (303, 400)
    assert _status(db, "RIDE_1023") == "ACCEPTED"
