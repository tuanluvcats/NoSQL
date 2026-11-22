import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from main import create_app
from tests.fakes import FakeDb

pytestmark = pytest.mark.nosql


def _client(db=None):
    # các test ở đây kiểm panel CQL nên chạy ở chế độ kỹ thuật (mặc định giao diện ẩn panel, xem test_tech_mode.py)
    return TestClient(create_app(Settings.from_env({"APP_TECH_MODE": "1"}), db=db or FakeDb()))


def test_health():
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_home_has_trace_panel_and_static_css():
    c = _client()
    r = c.get("/")
    assert r.status_code == 200
    assert "CQL đã chạy" in r.text
    assert c.get("/static/app.css").status_code == 200
    assert c.get("/static/bootstrap.min.css").status_code == 200


def test_unknown_page_renders_html_error():
    r = _client().get("/khong-co")
    assert r.status_code == 404
    assert "text/html" in r.headers["content-type"]


def test_db_error_banner_when_connect_fails(monkeypatch):
    def failing(settings, keyspace=None):
        raise OSError("no host")

    monkeypatch.setattr("db.session.connect", failing)
    app = create_app(Settings.from_env({"APP_TECH_MODE": "1"}), db=None)
    with TestClient(app) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "no host" in r.text  # chi tiết lỗi chỉ hiện ở chế độ kỹ thuật
        assert "no host" in app.state.db_error
        c.cookies.set("tech_mode", "0")
        plain = c.get("/")
        assert "tạm gián đoạn" in plain.text and "no host" not in plain.text


def test_trace_of_previous_post_is_shown_once():
    """flash_trace giữ trace vào TraceStore, trang kế tiếp hiển thị 'CQL của thao tác vừa rồi'."""
    from db.trace import TraceEntry

    app = create_app(Settings.from_env({"APP_TECH_MODE": "1"}), db=FakeDb())
    entry = TraceEntry(name="T02_account_lock", code="T02", q="Q1", table="user_accounts",
                       cql="UPDATE user_accounts SET is_active = false WHERE username = ? IF is_active = true",
                       params=["u1"], partition_key={"username": "u1"}, consistency="LOCAL_QUORUM",
                       kind="lwt", applied=False, current={"is_active": False}, row_count=1,
                       elapsed_ms=1.5, error=None)

    @app.post("/_flash")
    def flash(request: Request):
        from db import trace
        from routes.deps import flash_trace

        trace.record(entry)
        flash_trace(request)
        return {"ok": True}

    with TestClient(app) as c:
        assert c.post("/_flash").status_code == 200
        first = c.get("/")
        assert "CQL của thao tác vừa rồi" in first.text
        assert "T02" in first.text
        assert "[applied]" in first.text
        second = c.get("/")
        assert "CQL của thao tác vừa rồi" not in second.text
