"""Trang chi tiết chuyến: tiêu đề theo trạng thái, biển số to, biên nhận, xác nhận tại chỗ, chấm sao, thông tin đầy đủ gập lại."""
import re
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from domain.tz import parse_vn
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
T = datetime(2026, 10, 4, 3, 5, tzinfo=timezone.utc)
RIDE = {"ride_id": "RIDE_X", "customer_id": "CUST001", "customer_name": "Khách A", "customer_phone": "0900000001",
        "driver_id": "DRV_1", "driver_name": "Trương Minh Quang", "vehicle_plate": "51K-567.89",
        "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1", "destination_address": "Sân bay Tân Sơn Nhất",
        "distance_km": 8.1, "fare": 81000.0, "discount": 16000.0, "promo_code": "GIAM20", "payment_method": "CASH",
        "status": "ACCEPTED", "ride_date": date(2026, 10, 4), "requested_at": T, "accepted_at": T, "started_at": None,
        "completed_at": None, "cancel_reason": None, "rated_at": None, "status_history": None}


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


def _page(role, ref_id, tech=False, **kw):
    c, _ = _client(role, ref_id, {"B06_ride_get": [{**RIDE, **kw}]}, tech=tech)
    r = c.get("/rides/RIDE_X")
    assert r.status_code == 200, r.text
    return r.text


def test_full_info_is_collapsed_unless_tech_mode():
    assert '<details class="disclosure ride-more">' in _page("CUSTOMER", "CUST001")
    assert '<details class="disclosure ride-more" open>' in _page("CUSTOMER", "CUST001", tech=True)


def test_customer_sees_payable_and_cash_note():
    html = _page("CUSTOMER", "CUST001")
    assert "Phải trả" in html and "65.000đ" in html
    assert "Trả tiền mặt cho tài xế khi đến nơi." in html
    assert "(đồng)" not in html


def test_completed_ride_says_paid():
    html = _page("CUSTOMER", "CUST001", status="COMPLETED", completed_at=T)
    assert "Đã thanh toán" in html and "Phải trả" not in html


def test_customer_sees_driver_and_big_plate_while_driver_is_coming():
    html = _page("CUSTOMER", "CUST001")
    assert re.search(r"<h1[^>]*>\s*Tài xế Trương Minh Quang đang đến\s*</h1>", html)
    assert '<p class="plate"><span class="visually-hidden">Biển số </span>51K-567.89</p>' in html
    assert "Đối chiếu biển số trước khi lên xe." in html


def test_cancel_asks_inline_before_posting():
    html = _page("CUSTOMER", "CUST001")
    block = html[html.index('<details class="confirm">'):]
    assert block.index("Hủy chuyến") < block.index('action="/rides/RIDE_X/cancel"') < block.index("Xác nhận hủy chuyến")


def test_driver_complete_button_names_cash_to_collect():
    html = _page("DRIVER", "DRV_1", status="ONGOING", started_at=T)
    assert "Hoàn thành · thu 65.000đ" in html and "Đã thu tiền, hoàn thành chuyến" in html
    assert 'name="drop_district"' in html
    momo = _page("DRIVER", "DRV_1", status="ONGOING", started_at=T, payment_method="MOMO")
    assert "Hoàn thành chuyến" in momo and "Xác nhận hoàn thành chuyến" in momo
    assert "Hoàn thành · thu" not in momo


def test_rating_offers_five_star_radios():
    html = _page("CUSTOMER", "CUST001", status="COMPLETED", completed_at=T)
    stars = re.findall(r'<input class="btn-check" type="radio" name="stars" id="star-(\d)" value="(\d)" required>', html)
    assert [v for _, v in stars] == ["1", "2", "3", "4", "5"]
    form = html.split('action="/rides/RIDE_X/rate"')[1].split("</form>")[0]
    assert "<select" not in form


def test_rating_keeps_the_same_tags_field():
    from config import RATING_TAGS

    html = _page("CUSTOMER", "CUST001", status="COMPLETED", completed_at=T)
    tags = re.findall(r'<input class="btn-check" type="checkbox" name="tags" id="tag-\d" value="([^"]+)">', html)
    assert tuple(tags) == RATING_TAGS


def test_driver_viewing_waiting_ride_sees_no_customer_contact():
    html = _page("DRIVER", "DRV_2", status="REQUESTED", driver_id=None, driver_name=None, vehicle_plate=None,
                 accepted_at=None)
    assert "Chuyến đang chờ tài xế" in html and 'action="/rides/RIDE_X/accept"' in html
    assert 'href="tel:' not in html


def test_own_driver_sees_customer_phone_and_start():
    html = _page("DRIVER", "DRV_1")
    assert 'href="tel:0900000001"' in html
    assert "Đến điểm đón khách" in html and "Bắt đầu chuyến" in html
    assert '<details class="disclosure gps-fields">' in html
