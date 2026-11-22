"""Thanh menu: mỗi trang chỉ sáng đúng một mục (không để /driver sáng chung với /driver/waiting)."""
import re

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

DRIVER_ROW = {"driver_id": "DRV_1", "full_name": "Tài Xế", "status": "OFFLINE", "rating": 4.9, "phone": "0900000002"}
ACTIVE = re.compile(r'<a class="nav-link-app is-active" href="([^"]+)" aria-current="page">')


def _client(role, ref_id):
    row = {"username": "u1", "role": role, "ref_id": ref_id, "full_name": "Người Dùng", "is_active": True,
           "password_hash": "x"}
    app = create_app(Settings.from_env({}), db=FakeDb({"B01_account_get": [row] * 20, "B03_driver_get": [DRIVER_ROW] * 5}))

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False, follow_redirects=False)
    c.post("/_login")
    return c


@pytest.mark.parametrize("role, ref_id, path, want", [
    ("DRIVER", "DRV_1", "/driver", "/driver"),
    ("DRIVER", "DRV_1", "/driver/waiting", "/driver/waiting"),
    ("DRIVER", "DRV_1", "/driver/income", "/driver/income"),
    ("CUSTOMER", "CUST001", "/customer/book", "/customer/book"),
    ("ADMIN", None, "/admin/backup", "/admin/backup"),
])
def test_exactly_one_nav_item_is_active(role, ref_id, path, want):
    r = _client(role, ref_id).get(path)
    assert r.status_code == 200, (path, r.status_code)
    assert ACTIVE.findall(r.text) == [want], path
    assert r.text.count("is-active") == 1 and r.text.count('aria-current="page"') == 1


def test_no_nav_item_is_active_on_a_page_outside_the_menu():
    r = _client("DRIVER", "DRV_1").get("/rides/RIDE_X")
    assert "is-active" not in r.text
