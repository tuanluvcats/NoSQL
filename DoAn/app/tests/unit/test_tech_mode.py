"""Chế độ kỹ thuật: mặc định giao diện sạch (không CQL, không ghi chú kỹ thuật), bật bằng cookie hoặc APP_TECH_MODE."""
import re

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import PAYMENT_METHODS, Settings
from domain import labels
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.auth

FORBIDDEN = ("rides_by_", "drivers_by_area", "partition", "LWT", "APP0", "spec §", "keyspace", "materialized",
             "Dữ liệu mẫu")

CUSTOMER_ROW = {"customer_id": "CUST001", "full_name": "Khách A", "phone": "0900000001", "email": "a@x.vn", "address": "Q1"}
DRIVER_ROW = {"driver_id": "DRV_1", "full_name": "Tài Xế", "status": "AVAILABLE", "rating": 4.9, "phone": "0900000002"}

EXTRA = {
    "APP02_customers_scan": [[CUSTOMER_ROW]] * 3,
    "B03_driver_get": [DRIVER_ROW] * 3,
}


def _client(role=None, ref_id=None, env=None, extra=None, cookie=None):
    responses = dict(extra or {})
    if role:
        responses["B01_account_get"] = [{"username": "u1", "role": role, "ref_id": ref_id, "full_name": "Người Dùng",
                                         "is_active": True, "password_hash": "x"}] * 20
    app = create_app(Settings.from_env(env or {}), db=FakeDb(responses))

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False, follow_redirects=False)
    if role:
        c.post("/_login")
    if cookie is not None:
        c.cookies.set("tech_mode", cookie)
    return c


def _assert_clean(html, where):
    assert "cql-panel" not in html, where
    assert "tech-note" not in html, where
    for word in FORBIDDEN:
        assert word not in html, (where, word)


@pytest.mark.parametrize("role,ref", [(None, None), ("ADMIN", None), ("CUSTOMER", "CUST001"), ("DRIVER", "DRV_1")])
def test_default_home_is_clean(role, ref):
    r = _client(role, ref, extra=EXTRA).get("/")
    assert r.status_code == 200
    _assert_clean(r.text, f"/ ({role})")


@pytest.mark.parametrize("role,ref,path", [
    ("CUSTOMER", "CUST001", "/customer/book"),
    ("ADMIN", None, "/admin/backup"),
    ("ADMIN", None, "/admin/customers"),
    ("DRIVER", "DRV_1", "/driver"),
])
def test_default_pages_are_clean(role, ref, path):
    r = _client(role, ref, extra=EXTRA).get(path)
    assert r.status_code == 200, (path, r.status_code)
    _assert_clean(r.text, path)


def test_cookie_on_shows_panel_and_notes():
    html = _client("ADMIN", extra=EXTRA, cookie="1").get("/admin/customers").text
    assert "cql-panel" in html and "tech-note" in html
    assert "Tắt chế độ kỹ thuật" in html and "Đang hiện lệnh CQL và ghi chú kỹ thuật" in html


def test_default_footer_offers_to_turn_on():
    html = _client("ADMIN", extra=EXTRA).get("/admin/customers").text
    assert "Bật chế độ kỹ thuật" in html and 'name="on" value="1"' in html


def test_env_default_on_shows_panel_and_cookie_zero_wins():
    on = _client("ADMIN", env={"APP_TECH_MODE": "1"}, extra=EXTRA).get("/admin/customers").text
    assert "cql-panel" in on
    off = _client("ADMIN", env={"APP_TECH_MODE": "1"}, extra=EXTRA, cookie="0").get("/admin/customers").text
    assert "cql-panel" not in off and "tech-note" not in off


def test_settings_tech_mode_env_parsing():
    assert Settings.from_env({}).tech_mode is False
    assert Settings.from_env({"APP_TECH_MODE": "true"}).tech_mode is True
    assert Settings.from_env({"APP_TECH_MODE": "0"}).tech_mode is False


def test_post_tech_mode_sets_cookie_and_redirects_back():
    r = _client().post("/tech-mode", data={"on": "1", "next": "/admin/backup"})
    assert r.status_code == 303 and r.headers["location"] == "/admin/backup"
    cookie = r.headers["set-cookie"]
    assert "tech_mode=1" in cookie and "httponly" in cookie.lower() and "samesite=lax" in cookie.lower()
    assert "Max-Age=2592000" in cookie
    off = _client().post("/tech-mode", data={"on": "0", "next": "/"})
    assert "tech_mode=0" in off.headers["set-cookie"]


@pytest.mark.parametrize("target", ["//evil.com", "https://evil.com", "/\\evil.com", "", "evil.com"])
def test_post_tech_mode_blocks_open_redirect(target):
    r = _client().post("/tech-mode", data={"on": "1", "next": target})
    assert r.status_code == 303 and r.headers["location"] == "/"


def test_post_tech_mode_works_during_maintenance():
    app = create_app(Settings.from_env({}), db=FakeDb())
    app.state.maintenance.begin()
    c = TestClient(app, follow_redirects=False)
    assert c.post("/tech-mode", data={"on": "1", "next": "/"}).status_code == 303
    assert c.post("/login", data={"username": "x", "password": "y"}).status_code == 503


def test_toggle_round_trip_changes_page():
    c = _client("ADMIN", extra=EXTRA)
    assert "cql-panel" not in c.get("/admin/customers").text
    c.post("/tech-mode", data={"on": "1", "next": "/admin/customers"})
    assert "cql-panel" in c.get("/admin/customers").text
    c.post("/tech-mode", data={"on": "0", "next": "/admin/customers"})
    assert "cql-panel" not in c.get("/admin/customers").text


def test_labels_map_codes_and_fall_back_to_raw_value():
    assert labels.ride_status("REQUESTED") == "Đang tìm tài xế"
    assert labels.ride_status("ACCEPTED") == "Tài xế đang đến"
    assert labels.ride_status("ONGOING") == "Đang trong chuyến"
    assert labels.ride_status("COMPLETED") == "Hoàn thành"
    assert labels.ride_status("CANCELLED") == "Đã hủy"
    assert labels.driver_status("AVAILABLE") == "Sẵn sàng"
    assert labels.driver_status("BUSY") == "Đang chở khách"
    assert labels.driver_status("OFFLINE") == "Ngoại tuyến"
    assert labels.pay_method("CASH") == "Tiền mặt" and labels.pay_method("MOMO") == "MoMo"
    assert labels.role_label("ADMIN") == "Quản trị viên" and labels.role_label("OPERATOR") == "Điều phối viên"
    assert labels.role_label("CUSTOMER") == "Khách hàng" and labels.role_label("DRIVER") == "Tài xế"
    for fn in (labels.ride_status, labels.driver_status, labels.pay_method, labels.role_label):
        assert fn("LA_LUNG") == "LA_LUNG"
        assert fn(None) is None


def test_every_configured_payment_method_has_a_label():
    for m in PAYMENT_METHODS:
        assert m in labels.PAY_METHOD, m


def test_jinja_filters_are_registered():
    from routes.deps import templates

    for name in ("ride_status", "driver_status", "pay_method", "role_label"):
        assert name in templates.env.filters


def _hrefs(html):
    return set(re.findall(r'href="([^"]+)"', html))


@pytest.mark.parametrize("role,ref", [(None, None), ("CUSTOMER", "CUST001"), ("DRIVER", "DRV_1")])
def test_navbar_hides_system_group_for_non_admin(role, ref):
    hrefs = _hrefs(_client(role, ref, extra=EXTRA).get("/").text)
    assert "/nosql" not in hrefs and "/connection" not in hrefs


def test_navbar_shows_system_group_for_admin_and_operator():
    for role in ("ADMIN", "OPERATOR"):
        hrefs = _hrefs(_client(role, extra=EXTRA).get("/").text)
        assert "/nosql" in hrefs and "/connection" in hrefs


def test_navbar_shows_name_and_vietnamese_role_and_guest_has_no_status_span():
    html = _client("ADMIN", extra=EXTRA).get("/").text
    assert "Người Dùng &middot; Quản trị viên" in html
    guest = _client(extra=EXTRA).get("/").text
    assert "Chưa đăng nhập" not in guest
    assert 'href="/login"' in guest and 'href="/register"' in guest


def test_db_error_banner_is_plain_by_default_and_detailed_in_tech_mode():
    app = create_app(Settings.from_env({}), db=FakeDb())
    app.state.db_error = "NoHostAvailable: 10.0.0.9"
    c = TestClient(app)
    plain = c.get("/")
    assert "Hệ thống đang tạm gián đoạn, vui lòng thử lại sau." in plain.text and "10.0.0.9" not in plain.text
    c.cookies.set("tech_mode", "1")
    assert "10.0.0.9" in c.get("/").text


def test_no_database_error_says_system_interrupted_not_cassandra():
    app = create_app(Settings.from_env({}), db=None)
    r = TestClient(app, raise_server_exceptions=False).get("/customer/book")
    assert "Cassandra" not in r.text


def test_every_configured_area_has_vietnamese_label():
    from config import AREAS
    for city, districts in AREAS.items():
        assert labels.city_label(city) != city
        for d in districts:
            assert labels.district_label(d) != d, d
    assert labels.district_label("KHONG_CO") == "KHONG_CO"


def test_booking_form_shows_area_names_not_codes():
    html = _client("CUSTOMER", "CUST001").get("/customer/book").text
    assert ">Tân Phú</option>" in html and ">TAN_PHU</option>" not in html
    assert ">TP. Hồ Chí Minh</option>" in html
