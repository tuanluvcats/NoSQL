import re

import pytest

from domain.ids import RIDE_ID_RE
from domain.tz import parse_vn
from services import accounts
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.auth]

NOW = parse_vn("2026-10-04 10:05")


def _clock():
    return NOW


def _payload(ride_id, **kw):
    base = {"ride_id": ride_id, "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1",
            "destination_address": "Sân bay Tân Sơn Nhất, Tân Bình", "distance_km": "8.1",
            "payment_method": "MOMO", "promo_code": "GIAM20"}
    base.update(kw)
    return base


def _ride_id_from(html: str) -> str:
    m = re.search(r'name="ride_id"[^>]*value="([^"]+)"', html) or re.search(r'value="([^"]+)"[^>]*name="ride_id"', html)
    assert m, "form phải có input ẩn ride_id"
    return m.group(1)


def test_book_form_has_hidden_ride_id_matching_pattern(client_factory):
    c = client_factory(clock=_clock)
    assert http_login(c, "cust001").status_code == 303
    r = c.get("/customer/book")
    assert r.status_code == 200 and 'name="ride_id"' in r.text
    assert re.match(RIDE_ID_RE, _ride_id_from(r.text))


def test_locked_customer_cannot_book_over_http(client_factory, db):
    c = client_factory(clock=_clock)
    assert http_login(c, "cust002").status_code == 303
    assert accounts.set_account_active(db, "cust002", False, "admin", NOW).ok
    r = c.post("/customer/book", data=_payload("RIDE_20261004100500_0002"))
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    assert len(db.rows("B07_customer_history", ["CUST002"])) == 5
    assert db.one("B06_ride_get", ["RIDE_20261004100500_0002"]) is None


def test_guest_and_non_customer_cannot_book(client_factory, db):
    guest = client_factory(clock=_clock)
    r = guest.post("/customer/book", data=_payload("RIDE_20261004100500_0003"))
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    admin = client_factory(clock=_clock)
    http_login(admin, "admin")
    assert admin.get("/customer/book").status_code == 403
    assert admin.post("/customer/book", data=_payload("RIDE_20261004100500_0003")).status_code == 403
    assert db.one("B06_ride_get", ["RIDE_20261004100500_0003"]) is None


def test_post_book_redirects_to_detail_and_shows_trace(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "cust001")
    rid = _ride_id_from(c.get("/customer/book").text)
    r = c.post("/customer/book", data=_payload(rid))
    assert r.status_code == 303 and r.headers["location"] == f"/rides/{rid}"
    page = c.get(f"/rides/{rid}")
    assert page.status_code == 200
    assert rid in page.text and "REQUESTED" in page.text and "GIAM20" in page.text
    assert "CQL của thao tác vừa rồi" in page.text and "T04" in page.text
    assert "ma trận ghi của sự kiện “Đặt xe”" in page.text and "thiếu" not in page.text  # ma trận áp cho thao tác POST
    # F5 gửi lại đúng form: không thêm chuyến, không trừ thêm lượt
    again = c.post("/customer/book", data=_payload(rid))
    assert again.status_code == 303
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6
    assert len(db.rows("B07_customer_history", ["CUST001"])) == 5


def test_post_book_invalid_returns_400_without_ride(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "cust001")
    r = c.post("/customer/book", data=_payload("RIDE_20261004100500_0004", city="DN"))
    assert r.status_code == 400
    assert db.one("B06_ride_get", ["RIDE_20261004100500_0004"]) is None
    r = c.post("/customer/book", data=_payload("RIDE_20261004100500_0005", distance_km="abc"))
    assert r.status_code == 400
    r = c.post("/customer/book", data=_payload("RIDE_20261004100500_0006", promo_code="HCMXANH",
                                               city="HN", district="HOAN_KIEM"))
    assert r.status_code == 400 and "RIDE_20261004100500_0006" in r.text  # giữ nguyên ride_id khi lỗi
    assert db.one("B06_ride_get", ["RIDE_20261004100500_0006"]) is None


def test_quote_keeps_ride_id_and_shows_amounts(client_factory, db):
    c = client_factory(clock=_clock)
    http_login(c, "cust001")
    r = c.post("/customer/book/quote", data=_payload("RIDE_20261004100500_0007"))
    assert r.status_code == 200
    assert "RIDE_20261004100500_0007" in r.text and "81" in r.text and "65" in r.text
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 5  # quote không giữ lượt


def test_other_customer_cannot_view_ride_detail(client_factory):
    owner = client_factory(clock=_clock)
    http_login(owner, "cust001")
    rid = _ride_id_from(owner.get("/customer/book").text)
    assert owner.post("/customer/book", data=_payload(rid)).status_code == 303
    other = client_factory(clock=_clock)
    http_login(other, "cust002")
    assert other.get(f"/rides/{rid}").status_code == 403
    admin = client_factory(clock=_clock)
    http_login(admin, "admin")
    assert admin.get(f"/rides/{rid}").status_code == 200
    assert owner.get("/rides/RIDE_NOPE").status_code == 404
