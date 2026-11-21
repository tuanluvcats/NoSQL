"""Quy tắc UX: không có hai nút cùng chức năng trên một màn hình, cùng một nhãn không dẫn tới hai nơi khác nhau,
thao tác xóa/khóa phải hỏi lại, tài xế đang BUSY thấy được chuyến của mình."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.auth

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
LINK = re.compile(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def _client(role=None, ref_id=None, extra=None):
    responses = dict(extra or {})
    if role:
        responses["B01_account_get"] = [{"username": "u1", "role": role, "ref_id": ref_id, "full_name": "U1",
                                         "is_active": True, "password_hash": "x"}] * 10
    app = create_app(Settings.from_env({}), db=FakeDb(responses))

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False)
    if role:
        c.post("/_login")
    return c


def _links(html):
    return [(href, " ".join(re.sub(r"<[^>]+>", "", text).split())) for href, text in LINK.findall(html)]


@pytest.mark.parametrize("role", [None, "ADMIN", "OPERATOR", "CUSTOMER", "DRIVER"])
def test_home_has_no_link_twice(role):
    html = _client(role, "CUST001" if role == "CUSTOMER" else "DRV_1").get("/").text
    hrefs = [h for h, _ in _links(html)]
    dup = {h for h in hrefs if hrefs.count(h) > 1}
    assert not dup, dup


@pytest.mark.parametrize("role", [None, "ADMIN", "CUSTOMER", "DRIVER"])
def test_same_label_never_points_to_two_places(role):
    html = _client(role, "CUST001" if role == "CUSTOMER" else "DRV_1").get("/").text
    seen = {}
    for href, label in _links(html):
        if label:
            assert seen.setdefault(label, href) == href, (label, seen[label], href)


def test_navbar_marks_current_page():
    html = _client("ADMIN").get("/admin/backup").text
    assert re.search(r'href="/admin/backup"[^>]*aria-current="page"', html)


def test_driver_navbar_has_waiting_rides_and_status():
    html = _client("DRIVER", "DRV_1").get("/").text
    labels = dict((h, t) for h, t in _links(html))
    assert "/driver/waiting" in labels and "/driver" in labels
    assert labels["/driver"] != "Nhận chuyến"


def test_buttons_on_one_page_have_distinct_labels():
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        # bỏ các nút nằm trong vòng lặp (mỗi dòng một nút là bình thường)
        outside = re.sub(r"{%\s*for\b.*?{%\s*endfor\s*%}", "", text, flags=re.S)
        labels = [" ".join(t.split()) for t in re.findall(r"<button\b[^>]*>(.*?)</button>", outside, re.S)]
        dup = {x for x in labels if labels.count(x) > 1}
        assert not dup, (path.name, dup)


def test_destructive_forms_ask_for_confirmation():
    for path in (TEMPLATES / "admin").glob("*.html"):
        text = path.read_text(encoding="utf-8")
        for form in re.findall(r"<form\b[^>]*>", text):
            if re.search(r'action="[^"]*/(delete|lock)"', form):
                assert "confirm(" in form, (path.name, form)


def test_busy_driver_sees_link_to_current_ride():
    extra = {
        "B03_driver_get": [{"driver_id": "DRV_1", "full_name": "Tai", "status": "BUSY", "rating": 5.0}],
        "B10_driver_month": [[{"ride_id": "RIDE_X", "status": "ACCEPTED"}]],
        "B06_ride_get": [{"ride_id": "RIDE_X", "driver_id": "DRV_1", "status": "ACCEPTED"}],
    }
    html = _client("DRIVER", "DRV_1", extra).get("/driver").text
    assert 'href="/rides/RIDE_X"' in html


def test_backup_page_does_not_show_absolute_server_path():
    from pathlib import Path as _P
    app_root = str(_P(__file__).resolve().parents[2])
    html = _client("ADMIN").get("/admin/backup").text
    assert app_root not in html
    assert "backups" in html
