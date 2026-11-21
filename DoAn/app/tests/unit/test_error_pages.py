"""Trang lỗi khi tra cứu người dùng thất bại (DB hỏng): vẫn render trang lỗi gốc, coi như khách, không lộ chi tiết lỗi DB."""
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.auth

ADMIN_ROW = {"username": "admin", "role": "ADMIN", "ref_id": None, "full_name": "Quản Trị", "is_active": True,
             "password_hash": "x"}


def _client(db):
    app = create_app(Settings.from_env({}), db=db)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "admin"
        return {"ok": True}

    @app.get("/_boom")
    def boom():
        raise RuntimeError("lỗi giả lập")

    c = TestClient(app, raise_server_exceptions=False)
    assert c.post("/_login").status_code == 200
    return c


def test_404_shows_user_loaded_from_session():
    db = FakeDb({"B01_account_get": [ADMIN_ROW]})
    r = _client(db).get("/khong-co")
    assert r.status_code == 404 and "Quản Trị" in r.text and "(ADMIN)" in r.text
    assert "Chưa đăng nhập" not in r.text
    assert "password_hash" not in r.text


def test_user_lookup_db_error_does_not_leak_and_error_page_still_renders():
    db = FakeDb({"B01_account_get": [RuntimeError("HOST-BI-MAT-10.9.8.7 NoHostAvailable")]})
    r = _client(db).get("/khong-co")
    assert r.status_code == 404
    assert "Chưa đăng nhập" in r.text
    assert "HOST-BI-MAT" not in r.text and "10.9.8.7" not in r.text


def test_500_when_db_down_hides_nothing_new_and_renders():
    db = FakeDb({"B01_account_get": [RuntimeError("HOST-BI-MAT-10.9.8.7")] * 3})
    r = _client(db).get("/_boom")
    assert r.status_code == 500 and "lỗi giả lập" in r.text
    assert "HOST-BI-MAT" not in r.text


def test_error_page_without_db_is_guest():
    app = create_app(Settings.from_env({}), db=None)
    r = TestClient(app).get("/khong-co")
    assert r.status_code == 404 and "Chưa đăng nhập" in r.text
