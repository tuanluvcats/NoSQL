"""Smoke HTTP: đặt xe qua form, thấy báo giá, chuyển hướng, trang chi tiết có trace T04 và [applied]."""
import re

import pytest

from domain.tz import parse_vn
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:05")


def test_book_quote_submit_and_detail_with_trace(client_factory, db):
    c = client_factory(clock=lambda: NOW)
    assert http_login(c, "cust001").status_code == 303
    form = c.get("/customer/book")
    assert form.status_code == 200
    ride_id = re.search(r'name="ride_id"[^>]*value="([^"]+)"', form.text).group(1)
    data = {"ride_id": ride_id, "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1",
            "destination_address": "Sân bay Tân Sơn Nhất, Tân Bình", "distance_km": "8.1",
            "payment_method": "MOMO", "promo_code": "GIAM20"}
    quote = c.post("/customer/book/quote", data=data)
    assert quote.status_code == 200 and "65000" in quote.text.replace(".", "").replace(",", "")
    r = c.post("/customer/book", data=data)
    assert r.status_code == 303 and r.headers["location"] == f"/rides/{ride_id}"
    page = c.get(f"/rides/{ride_id}")
    assert page.status_code == 200
    assert "REQUESTED" in page.text and "T04" in page.text and "[applied]" in page.text
    assert db.one("B06_ride_get", [ride_id])["status"] == "REQUESTED"
