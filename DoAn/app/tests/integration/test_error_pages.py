"""Trang lỗi 404/403/500 phải hiện đúng người dùng đã đăng nhập trong menu (trước đây luôn là 'Chưa đăng nhập')."""
import pytest
from fastapi.testclient import TestClient

from main import create_app
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.auth


def test_404_page_shows_logged_in_user_in_menu(client_factory):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    r = c.get("/khong-co-trang-nay")
    assert r.status_code == 404
    assert "Chưa đăng nhập" not in r.text
    assert "(ADMIN)" in r.text and "Đăng xuất" in r.text and "/admin/accounts" in r.text


def test_403_page_shows_logged_in_user_in_menu(client_factory):
    c = client_factory()
    http_login(c, "cust001")
    r = c.get("/admin/accounts")
    assert r.status_code == 403
    assert "Chưa đăng nhập" not in r.text and "(CUSTOMER)" in r.text and "/customer/book" in r.text


def test_404_page_for_guest_still_says_not_logged_in(client_factory):
    r = client_factory().get("/khong-co-trang-nay")
    assert r.status_code == 404 and "Chưa đăng nhập" in r.text and "/login" in r.text


def test_500_page_shows_logged_in_user_in_menu(settings_test, db):
    app = create_app(settings_test, db=db)

    @app.get("/_boom")
    def boom():
        raise RuntimeError("lỗi giả lập")

    c = TestClient(app, follow_redirects=False, raise_server_exceptions=False)
    http_login(c, "drv551")
    r = c.get("/_boom")
    assert r.status_code == 500
    assert "Chưa đăng nhập" not in r.text and "(DRIVER)" in r.text and "/driver/income" in r.text


def test_error_page_of_locked_user_is_treated_as_guest(client_factory, db):
    from domain.tz import parse_vn
    from services import accounts

    c = client_factory()
    http_login(c, "cust002")
    assert accounts.set_account_active(db, "cust002", False, "admin", parse_vn("2026-10-04 10:00")).ok
    r = c.get("/khong-co-trang-nay")
    assert r.status_code == 404 and "Chưa đăng nhập" in r.text and "(CUSTOMER)" not in r.text
