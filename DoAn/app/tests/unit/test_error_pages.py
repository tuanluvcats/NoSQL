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
    assert r.status_code == 500 and "Lỗi 500" in r.text
    assert "lỗi giả lập" not in r.text
    assert "HOST-BI-MAT" not in r.text


def _secret_client(env, db=None):
    app = create_app(Settings.from_env(env), db=db or FakeDb({"B01_account_get": [ADMIN_ROW] * 3}))

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "admin"
        return {"ok": True}

    @app.get("/_secret")
    def secret():
        raise RuntimeError("SECRET_DB_ERR C:\\duong\\bi\\mat NoHostAvailable")

    c = TestClient(app, raise_server_exceptions=False)
    assert c.post("/_login").status_code == 200
    return c


def test_500_hides_error_type_and_message_by_default():
    r = _secret_client({}).get("/_secret")
    assert r.status_code == 500
    assert "SECRET_DB_ERR" not in r.text and "RuntimeError" not in r.text and "NoHostAvailable" not in r.text
    assert "Lỗi 500" in r.text
    assert "Quản Trị" in r.text and "(ADMIN)" in r.text  # menu vẫn đúng người dùng


def test_500_is_logged_in_full_on_the_server(caplog):
    with caplog.at_level("ERROR", logger="ride_booking"):
        _secret_client({}).get("/_secret")
    records = [r for r in caplog.records if r.name == "ride_booking"]
    assert records, "lỗi 500 phải được ghi vào log"
    text = " ".join(r.getMessage() for r in records)
    rec = records[0]
    assert rec.exc_info and "SECRET_DB_ERR" in str(rec.exc_info[1])
    assert "/_secret" in text


def test_500_shows_detail_only_when_app_debug_is_on():
    r = _secret_client({"APP_DEBUG": "1"}).get("/_secret")
    assert r.status_code == 500
    assert "SECRET_DB_ERR" in r.text and "RuntimeError" in r.text
    assert "(ADMIN)" in r.text


@pytest.mark.parametrize("value", ["0", "", "false", "no"])
def test_500_app_debug_falsy_values_stay_hidden(value):
    r = _secret_client({"APP_DEBUG": value}).get("/_secret")
    assert r.status_code == 500 and "SECRET_DB_ERR" not in r.text


def test_503_maintenance_page_shows_logged_in_user_in_menu():
    db = FakeDb({"B01_account_get": [ADMIN_ROW] * 5})
    app = create_app(Settings.from_env({}), db=db)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "admin"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False)
    assert c.post("/_login").status_code == 200
    assert app.state.maintenance.begin() is True
    r = c.post("/_login")
    assert r.status_code == 503 and "Đang khôi phục dữ liệu" in r.text
    assert "Quản Trị" in r.text and "(ADMIN)" in r.text
    assert "Chưa đăng nhập" not in r.text


def test_503_maintenance_page_for_guest_still_says_not_logged_in():
    app = create_app(Settings.from_env({}), db=FakeDb())
    app.state.maintenance.begin()
    r = TestClient(app).post("/login", data={"username": "x", "password": "y"})
    assert r.status_code == 503 and "Chưa đăng nhập" in r.text


def test_error_page_without_db_is_guest():
    app = create_app(Settings.from_env({}), db=None)
    r = TestClient(app).get("/khong-co")
    assert r.status_code == 404 and "Chưa đăng nhập" in r.text
