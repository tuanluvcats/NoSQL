"""Trang đặt xe: một nút Xem giá, giá hiện ngay trên nút Đặt xe, mã khuyến mãi lỗi nói bằng tiếng Việt, giá cũ thì không đặt."""
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from domain.tz import parse_vn
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
FORM = {"ride_id": "RIDE_20261004100500_00AA", "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1",
        "destination_address": "Sân bay Tân Sơn Nhất", "distance_km": "8.1", "payment_method": "CASH", "promo_code": ""}
PROMO = {"code": "GIAM20", "discount_percent": 20, "max_discount": 16000.0, "min_fare": 0.0, "cities": {"HCM"},
         "valid_from": None, "valid_to": None, "usage_limit": None, "used_count": 0}
CUSTOMER = {"customer_id": "CUST001", "full_name": "Khách A", "phone": "0900000001"}


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


def _form_html(html):
    start = html.index('id="book-form"')
    return html[start:html.index("</form>", start)]


def test_empty_form_has_one_price_button():
    c, _ = _customer()
    html = c.get("/customer/book").text
    assert 'action="/customer/book/quote#price"' in html
    form = _form_html(html)
    assert form.count("<button") == 1
    assert ">Xem giá</button>" in form
    assert 'formaction="/customer/book"' not in form


def test_quote_puts_price_right_above_book_button():
    c, _ = _customer()
    html = c.post("/customer/book/quote", data=FORM).text
    assert "alert-info" not in html
    assert html.index('id="price"') < html.index("Đặt xe · 81.000đ")
    assert 'name="quoted_payable" value="81000"' in html
    assert 'formaction="/customer/book"' in html


def test_quote_with_promo_shows_breakdown():
    c, _ = _customer({"B16_promo_get": [PROMO]})
    html = c.post("/customer/book/quote", data={**FORM, "promo_code": "GIAM20"}).text
    assert "Đặt xe · 65.000đ" in html
    assert "Cước 81.000đ − 16.000đ (GIAM20) · 8.1 km · Tiền mặt" in html
    assert "Mã khuyến mãi chỉ bị trừ lượt khi bạn đặt xe." in html


def test_promo_problem_is_plain_text_and_offers_no_booking():
    c, _ = _customer()
    html = c.post("/customer/book/quote", data={**FORM, "promo_code": "SAI"}).text
    assert "Mã khuyến mãi không tồn tại." in html
    assert "not_found" not in html
    assert 'formaction="/customer/book"' not in html
    assert 'name="quoted_payable"' not in html
    assert '<button class="btn btn-primary btn-lg" type="submit" data-requote>Xem lại giá</button>' in html


def test_booking_with_outdated_price_is_refused_without_writing():
    c, db = _customer()
    r = c.post("/customer/book", data={**FORM, "quoted_payable": "70000"})
    assert r.status_code == 409
    assert "Giá đã thay đổi" in r.text and "Đặt xe · 81.000đ" in r.text
    assert "T04_ride_insert" not in db.names() and "B02_customer_get" not in db.names()


def test_booking_with_current_price_books():
    c, db = _customer({"B02_customer_get": [CUSTOMER]})
    r = c.post("/customer/book", data={**FORM, "quoted_payable": "81000"})
    assert r.status_code == 303
    assert r.headers["location"] == "/rides/RIDE_20261004100500_00AA"
    assert "T04_ride_insert" in db.names()


def test_booking_without_quote_field_keeps_old_behaviour():
    c, db = _customer({"B02_customer_get": [CUSTOMER]})
    r = c.post("/customer/book", data=FORM)
    assert r.status_code == 303
    assert "T04_ride_insert" in db.names()
