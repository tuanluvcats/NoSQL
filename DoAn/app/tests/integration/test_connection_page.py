"""Trang Kết nối (mục 8): host, port, DC, protocol v4, version từ system.local, keyspace, số bảng, cột rated_at."""
import dataclasses

import pytest

from config import Settings
from services.system_info import connection_info

pytestmark = pytest.mark.nosql


def test_connection_page_is_public_and_shows_cluster_facts(client_factory, settings_test):
    c = client_factory()
    r = c.get("/connection")
    assert r.status_code == 200
    assert "3.11" in r.text
    assert settings_test.keyspace in r.text
    assert "datacenter1" in r.text
    assert "protocol_version" in r.text and "vehicles_by_plate" in r.text
    assert "rated_at" in r.text


def test_connection_info_values(db, settings_test):
    info = connection_info(db, settings_test)
    assert info.get("error") is None
    assert info["protocol_version"] == 4
    assert info["release_version"].startswith("3.11")
    assert info["data_center"] == "datacenter1" and info["local_dc"] == settings_test.local_dc
    assert info["keyspace"] == settings_test.keyspace
    assert info["hosts"] == list(settings_test.hosts) and info["port"] == settings_test.port
    assert len(info["tables"]) == 13
    assert info["views"] == ["vehicles_by_plate"]
    assert info["migration_ok"] is True
    assert info["cql_version"] and info["cluster_name"]


def test_connection_page_never_prints_secrets(client_factory, settings_test):
    r = client_factory().get("/connection")
    assert settings_test.secret_key not in r.text
    assert "password_hash" not in r.text and "pbkdf2" not in r.text


def test_connection_info_reports_error_instead_of_raising(settings_test):
    class Broken:
        keyspace = settings_test.keyspace

        def rows(self, *a, **k):
            raise OSError("không có máy chủ")

        one = rows

    info = connection_info(Broken(), dataclasses.replace(settings_test))
    assert "OSError" in info["error"]
    assert info["keyspace"] == settings_test.keyspace and info["port"] == settings_test.port


def test_connection_page_without_db_shows_error_not_500():
    from fastapi.testclient import TestClient

    from main import create_app

    app = create_app(Settings.from_env({}), db=None)
    app.state.db_error = "NoHostAvailable: không kết nối được"
    r = TestClient(app).get("/connection")
    assert r.status_code == 200 and "NoHostAvailable" in r.text
