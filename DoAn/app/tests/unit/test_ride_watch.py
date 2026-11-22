"""Trang chi tiết chuyến tự cập nhật: dấu phiên bản `ride_stamp`, đường dẫn hỏi `/rides/{id}/status`, thanh và script ở trang."""
import re
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from db import trace
from db.trace import TraceEntry
from domain.tz import parse_vn
from main import create_app
from routes.deps import flash_trace, set_flash
from services.reports import ACTIVE_RIDE_STATUSES, WATCH_EVERY_SECONDS, ride_stamp
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
T = datetime(2026, 10, 4, 3, 5, tzinfo=timezone.utc)
RIDE = {"ride_id": "RIDE_X", "customer_id": "CUST001", "customer_name": "Khách A", "customer_phone": "0900000001",
        "driver_id": "DRV_1", "driver_name": "Trương Minh Quang", "vehicle_plate": "51K-567.89",
        "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1", "destination_address": "Sân bay Tân Sơn Nhất",
        "distance_km": 8.1, "fare": 81000.0, "discount": 0.0, "promo_code": None, "payment_method": "CASH",
        "status": "ACCEPTED", "ride_date": date(2026, 10, 4), "requested_at": T, "accepted_at": T, "started_at": None,
        "completed_at": None, "cancel_reason": None, "rated_at": None,
        "status_history": {T: "REQUESTED", T + timedelta(seconds=30): "ACCEPTED"}}


def _client(role=None, ref_id=None, ride=None, tech=False):
    responses = {"B06_ride_get": [{**RIDE, **(ride or {})}] * 10}
    if role:
        responses["B01_account_get"] = [{"username": "u1", "role": role, "ref_id": ref_id, "full_name": "Người Dùng",
                                         "is_active": True, "password_hash": "x"}] * 20
    db = FakeDb(responses)
    app = create_app(Settings.from_env({}), db=db, clock=lambda: NOW)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    @app.post("/_after_post")
    def fake_post(request: Request):
        """Giả lập một thao tác POST vừa xong: flash và trace chờ trang kế tiếp (như _finish trong routes/rides.py)."""
        entry = TraceEntry(name="T10_ride_cancel", code="T10", q="T10", table="rides",
                           cql="UPDATE rides SET status = 'CANCELLED' WHERE ride_id = ? IF status = ?",
                           params=["RIDE_X", "ACCEPTED"], partition_key={"ride_id": "RIDE_X"}, consistency="SERIAL",
                           kind="lwt", applied=True, current=None, row_count=1, elapsed_ms=1.0, error=None)
        trace.current().append(entry)
        set_flash(request, True, "Đã hủy chuyến.")
        flash_trace(request, "cancel")
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False, follow_redirects=False)
    if role:
        c.post("/_login")
    if tech:
        c.cookies.set("tech_mode", "1")
    return c, db


# ------------------------------------------------------------------ ride_stamp
def test_stamp_is_stable_for_the_same_row():
    assert ride_stamp(RIDE) == ride_stamp(dict(RIDE))
    assert ride_stamp(RIDE) == "ACCEPTED|2026-10-04T10:05:30+07:00|DRV_1"


def test_stamp_changes_with_status_history_or_driver():
    base = ride_stamp(RIDE)
    assert ride_stamp({**RIDE, "status": "ONGOING"}) != base
    more = {**RIDE["status_history"], T + timedelta(minutes=5): "ONGOING"}
    assert ride_stamp({**RIDE, "status_history": more}) != base
    assert ride_stamp({**RIDE, "driver_id": "DRV_2"}) != base
    assert ride_stamp({**RIDE, "driver_id": None}) != base


def test_stamp_handles_missing_history():
    for h in (None, {}):
        assert ride_stamp({**RIDE, "status_history": h}) == "ACCEPTED||DRV_1"
    assert ride_stamp({"status": "REQUESTED"}) == "REQUESTED||"


def test_watch_rhythm_matches_active_statuses():
    assert set(WATCH_EVERY_SECONDS) == set(ACTIVE_RIDE_STATUSES)
    assert [WATCH_EVERY_SECONDS[s] for s in ("REQUESTED", "ACCEPTED", "ONGOING")] == [5, 10, 15]


# ------------------------------------------------------------------ /rides/{id}/status
def test_owner_customer_gets_status_json_without_cache():
    c, db = _client("CUSTOMER", "CUST001")
    r = c.get("/rides/RIDE_X/status")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert r.headers["cache-control"] == "no-store"
    assert r.json() == {"status": "ACCEPTED", "stamp": ride_stamp(RIDE), "active": True}
    assert [n for n in db.names() if n.startswith("B06")] == ["B06_ride_get"]  # đúng 1 lệnh đọc chuyến


def test_finished_ride_is_not_active():
    c, _ = _client("CUSTOMER", "CUST001", {"status": "COMPLETED"})
    assert c.get("/rides/RIDE_X/status").json()["active"] is False


def test_other_customer_is_forbidden():
    c, _ = _client("CUSTOMER", "CUST999")
    r = c.get("/rides/RIDE_X/status")
    assert r.status_code == 403 and r.json() == {"error": "forbidden"}


def test_unknown_ride_is_404_json():
    c, db = _client("CUSTOMER", "CUST001")
    db._responses["B06_ride_get"] = []
    r = c.get("/rides/NOPE/status")
    assert r.status_code == 404 and r.json() == {"error": "not_found"}


def test_guest_gets_401_json_not_redirect():
    c, _ = _client()
    r = c.get("/rides/RIDE_X/status")
    assert r.status_code == 401 and r.json() == {"error": "login"}
    assert "location" not in r.headers


def test_locked_account_gets_401_json():
    c, db = _client("CUSTOMER", "CUST001")
    db._responses["B01_account_get"] = [{"username": "u1", "role": "CUSTOMER", "ref_id": "CUST001", "full_name": "x",
                                         "is_active": False, "password_hash": "x"}]
    r = c.get("/rides/RIDE_X/status")
    assert r.status_code == 401 and r.json() == {"error": "login"}


@pytest.mark.parametrize("ref_id, ride, want", [
    ("DRV_1", {}, 200),                                                   # tài xế của chuyến
    ("DRV_2", {}, 403),                                                   # tài xế khác, chuyến đã nhận
    ("DRV_2", {"status": "REQUESTED", "driver_id": None}, 200),           # chuyến chờ: tài xế nào cũng xem được
])
def test_driver_access_follows_can_view_ride(ref_id, ride, want):
    c, _ = _client("DRIVER", ref_id, ride)
    assert c.get("/rides/RIDE_X/status").status_code == want


def test_admin_can_watch_any_ride():
    c, _ = _client("ADMIN", None)
    assert c.get("/rides/RIDE_X/status").status_code == 200


# ------------------------------------------------------------------ trang chi tiết
@pytest.mark.parametrize("status, every", [("REQUESTED", 5), ("ACCEPTED", 10), ("ONGOING", 15)])
def test_active_ride_page_has_watch_bar_with_same_stamp_as_status(status, every):
    c, _ = _client("CUSTOMER", "CUST001", {"status": status})
    html = c.get("/rides/RIDE_X").text
    assert 'data-ride-watch="/rides/RIDE_X/status"' in html
    assert f'data-every="{every}"' in html
    stamp = re.search(r'data-stamp="([^"]*)"', html).group(1)
    assert stamp == c.get("/rides/RIDE_X/status").json()["stamp"]
    assert "data-manual" not in html
    assert "data-watch-reload" in html and "new AbortController" in html


@pytest.mark.parametrize("status", ["COMPLETED", "CANCELLED"])
def test_finished_ride_page_has_no_watch(status):
    c, _ = _client("CUSTOMER", "CUST001", {"status": status})
    html = c.get("/rides/RIDE_X").text
    assert "data-ride-watch" not in html and "AbortController" not in html


def test_tech_mode_makes_the_bar_manual():
    c, _ = _client("CUSTOMER", "CUST001", tech=True)
    assert "data-manual" in c.get("/rides/RIDE_X").text


# ------------------------------------------------------------------ lần hỏi không đụng flash và trace
def test_status_poll_keeps_flash_and_last_trace_for_next_page():
    c, _ = _client("CUSTOMER", "CUST001", tech=True)
    assert c.post("/_after_post").status_code == 200
    for _ in range(3):
        assert c.get("/rides/RIDE_X/status").status_code == 200
    html = c.get("/rides/RIDE_X").text
    assert "Đã hủy chuyến." in html
    assert "CQL của thao tác vừa rồi" in html
    # đã hiển thị một lần thì hết (cơ chế PRG vẫn như cũ)
    again = c.get("/rides/RIDE_X").text
    assert "Đã hủy chuyến." not in again and "CQL của thao tác vừa rồi" not in again
