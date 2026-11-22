"""Lịch sử chuyến của khách và thu nhập của tài xế: danh sách dạng thẻ, ô chọn ngày giữ giá trị ISO, chuyển tháng."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from domain.tz import parse_vn
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
HISTORY_ROW = {"ride_date": date(2026, 10, 4), "ride_id": "RIDE_A", "pickup_address": "A", "destination_address": "B",
               "driver_id": "DRV_1", "fare": 65000.0, "status": "COMPLETED"}


def _client(role=None, ref_id=None, extra=None, tech=False, cookies=None):
    responses = {}
    if role:
        responses["B01_account_get"] = [{"username": "u1", "role": role, "ref_id": ref_id, "full_name": "Người Dùng",
                                         "is_active": True, "password_hash": "x"}] * 20
    responses.update(extra or {})
    db = FakeDb(responses)
    app = create_app(Settings.from_env({}), db=db, clock=lambda: NOW)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False, follow_redirects=False)
    if role:
        c.post("/_login")
    for k, v in (cookies or {}).items():
        c.cookies.set(k, v)
    if tech:
        c.cookies.set("tech_mode", "1")
    return c, db


def _customer(extra=None, **kw):
    return _client("CUSTOMER", "CUST001", extra, **kw)


def _driver(extra=None, **kw):
    return _client("DRIVER", "DRV_1", extra, **kw)


# ------------------------------------------------------------------ lịch sử chuyến
def test_history_is_a_list_of_ride_cards():
    c, _ = _customer({"B07_customer_history": [[HISTORY_ROW]]})
    html = c.get("/customer/rides").text
    assert "<table" not in html
    for want in ('href="/rides/RIDE_A"', "65.000đ", "04/10/2026", "Hoàn thành"):
        assert want in html
    for gone in ("DRV_1", "(VND)"):
        assert gone not in html
    assert 'type="date"' not in html  # ô ngày gõ theo ngày/tháng/năm, khớp cách ghi ngày trên trang


def test_history_filter_takes_vietnamese_dates():
    c, db = _customer()
    r = c.get("/customer/rides?from=01/10/2026&to=04/10/2026")
    assert r.status_code == 200
    assert [p for n, p in db.calls if n == "B08_customer_history_range"] == [
        ("CUST001", date(2026, 10, 1), date(2026, 10, 4))]
    html = r.text
    assert 'value="01/10/2026"' in html and 'value="04/10/2026"' in html  # ô ngày hiện lại theo ngày/tháng/năm
    assert 'placeholder="ngày/tháng/năm"' in html
    assert '<details class="disclosure filter mb-3" open>' in html
    assert "Không có chuyến nào trong khoảng ngày này." in html


def test_empty_history_invites_first_booking():
    c, _ = _customer()
    html = c.get("/customer/rides").text
    assert "Bạn chưa có chuyến nào." in html
    assert '<a class="btn btn-primary" href="/customer/book">Đặt chuyến đầu tiên</a>' in html


# ------------------------------------------------------------------ thu nhập tài xế
def test_income_heading_names_month_and_links_neighbours():
    c, _ = _driver()
    html = c.get("/driver/income").text
    assert "Thu nhập tháng 10/2026" in html
    assert 'href="/driver/income?yyyymm=202609"' in html
    for gone in ("yyyymm=202611", 'name="yyyymm"', "(VND)"):
        assert gone not in html
    html = c.get("/driver/income?yyyymm=202609").text
    assert "yyyymm=202608" not in html  # trước tháng đầu tiên của dữ liệu
    assert 'href="/driver/income?yyyymm=202610"' in html
    assert "Chưa có chuyến nào trong tháng 09/2026." in html
