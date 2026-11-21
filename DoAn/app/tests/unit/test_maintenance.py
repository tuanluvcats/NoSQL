"""Chế độ bảo trì: cờ có khóa luồng và middleware chặn mọi ghi (POST) trừ lệnh restore."""
import threading

import pytest
from fastapi.testclient import TestClient

from config import Settings
from main import create_app
from services.maintenance import MaintenanceState
from tests.fakes import FakeDb

pytestmark = pytest.mark.backup


def test_begin_twice_and_end():
    s = MaintenanceState()
    assert s.active is False
    assert s.begin() is True
    assert s.active is True
    assert s.begin() is False  # đang bật thì không bật lần hai
    s.end()
    assert s.active is False
    assert s.begin() is True


def test_only_one_thread_wins_begin():
    s = MaintenanceState()
    wins = []
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        wins.append(s.begin())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert wins.count(True) == 1


def _client():
    app = create_app(Settings.from_env({}), db=FakeDb())
    return app, TestClient(app, follow_redirects=False)


def test_post_is_503_while_maintenance_and_ok_after():
    app, c = _client()
    assert isinstance(app.state.maintenance, MaintenanceState)
    assert app.state.maintenance.begin() is True
    r = c.post("/login", data={"username": "x", "password": "y"})
    assert r.status_code == 503
    assert "Đang khôi phục dữ liệu" in r.text
    app.state.maintenance.end()
    assert c.post("/login", data={"username": "x", "password": "y"}).status_code != 503


def test_get_still_works_and_shows_banner_while_maintenance():
    app, c = _client()
    app.state.maintenance.begin()
    r = c.get("/")
    assert r.status_code == 200
    assert "bảo trì" in r.text
    app.state.maintenance.end()
    assert "bảo trì" not in c.get("/").text


def test_other_write_methods_are_blocked_too():
    app, c = _client()
    app.state.maintenance.begin()
    assert c.put("/login").status_code == 503
    assert c.delete("/login").status_code == 503
    assert c.patch("/login").status_code == 503


def test_restore_route_is_exempt_from_the_block():
    """Route restore tự kiểm cờ (begin() False -> 'maintenance'), nên middleware không được chặn nó."""
    app, c = _client()
    app.state.maintenance.begin()
    r = c.post("/admin/backup/restore", data={"name": "x"})
    assert r.status_code != 503  # chưa đăng nhập -> 303 về /login
