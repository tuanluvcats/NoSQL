"""Trang chủ: hiển thị keyspace thật, phiên bản Cassandra nếu có, và lối vào nhanh theo vai trò."""
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.auth


def _row(username, role):
    return {"username": username, "role": role, "ref_id": None, "full_name": username.upper(), "is_active": True,
            "password_hash": "x"}


def _client(role=None, keyspace="ride_booking_test", version=None):
    responses = {}
    if role:
        responses["B01_account_get"] = [_row("u1", role)] * 5
    if version:
        responses["SYS_local"] = [{"release_version": version}] * 5
    db = FakeDb(responses)
    app = create_app(Settings.from_env({"CASSANDRA_KEYSPACE": keyspace}), db=db)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False)
    if role:
        assert c.post("/_login").status_code == 200
    return c


def _home(**kw):
    r = _client(**kw).get("/")
    assert r.status_code == 200
    return r.text


def test_home_shows_real_keyspace_not_hardcoded():
    text = _home(keyspace="ride_booking_test")
    assert "<code>ride_booking_test</code>" in text
    assert "<code>ride_booking</code>" not in text


def test_home_shows_cassandra_version_when_known():
    assert "3.11.4" in _home(version="3.11.4")


def test_home_without_version_does_not_invent_one():
    assert "3.11" not in _home()


def test_home_survives_version_lookup_failure():
    db = FakeDb({"SYS_local": [RuntimeError("HOST-BI-MAT-10.9.8.7")]})
    r = TestClient(create_app(Settings.from_env({}), db=db)).get("/")
    assert r.status_code == 200 and "HOST-BI-MAT" not in r.text


def test_guest_gets_login_register_connection_only():
    text = _home()
    for link in ("/login", "/register", "/connection"):
        assert f'href="{link}"' in text
    assert "/admin/" not in text and "/customer/" not in text and "/driver" not in text


@pytest.mark.parametrize("role", ["ADMIN", "OPERATOR"])
def test_admin_and_operator_get_admin_links(role):
    text = _home(role=role)
    for link in ("/admin/accounts", "/admin/customers", "/admin/drivers", "/admin/vehicles", "/admin/promotions",
                 "/admin/reports", "/admin/areas", "/admin/consistency", "/admin/backup"):
        assert f'href="{link}"' in text, link
    assert "/customer/book" not in text and "/driver/income" not in text


def test_customer_gets_booking_links_and_no_admin_link():
    text = _home(role="CUSTOMER")
    assert 'href="/customer/book"' in text and 'href="/customer/rides"' in text
    assert "/admin/" not in text and "/driver" not in text


def test_driver_gets_driver_links_and_no_admin_link():
    text = _home(role="DRIVER")
    for link in ("/driver", "/driver/waiting", "/driver/income", "/driver/ratings"):
        assert f'href="{link}"' in text, link
    assert "/admin/" not in text and "/customer/" not in text


def test_home_quick_links_are_real_routes():
    import re

    app = create_app(Settings.from_env({}), db=FakeDb())
    paths = set(app.openapi()["paths"])
    for role in (None, "ADMIN", "CUSTOMER", "DRIVER"):
        for link in re.findall(r'href="(/[^"?#]*)"', _home(role=role)):
            assert link in paths or link in ("/", "/static/app.css", "/static/bootstrap.min.css"), (role, link)
