import pytest

from config import Settings
from tools.check_env import check_env


def test_check_env_closed_port_does_not_raise():
    s = Settings.from_env({"CASSANDRA_HOSTS": "127.0.0.1", "CASSANDRA_PORT": "1"})
    r = check_env(s)
    assert r["connected"] is False
    assert r["error"]


def _boom(*a, **k):
    raise AssertionError("không được chạy kiểm tra khi chỉ in trợ giúp")


def test_help_prints_usage_without_checking(monkeypatch, capsys):
    import pytest

    from tools import check_env as mod

    monkeypatch.setattr(mod, "check_env", _boom)
    with pytest.raises(SystemExit) as e:
        mod.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower() and "--keyspace" in out


def test_unknown_option_exits_2_without_checking(monkeypatch):
    import pytest

    from tools import check_env as mod

    monkeypatch.setattr(mod, "check_env", _boom)
    with pytest.raises(SystemExit) as e:
        mod.main(["--khong-co"])
    assert e.value.code == 2


@pytest.mark.parametrize("result,code", [
    ({"connected": True, "keyspace_exists": True}, 0),
    ({"connected": True, "keyspace_exists": False}, 1),
    ({"connected": False, "keyspace_exists": False}, 1),
])
def test_default_behaviour_and_exit_code_unchanged(monkeypatch, capsys, result, code):
    from tools import check_env as mod

    seen = {}

    def fake(settings):
        seen["keyspace"] = settings.keyspace
        return {**result, "release_version": None, "tables": 0, "has_rated_at": False, "error": None}

    monkeypatch.setattr(mod, "check_env", fake)
    monkeypatch.setenv("CASSANDRA_KEYSPACE", "ride_booking_demo")
    assert mod.main([]) == code
    assert seen["keyspace"] == "ride_booking_demo"
    assert "connected:" in capsys.readouterr().out


def test_keyspace_option_overrides_environment(monkeypatch):
    from tools import check_env as mod

    seen = {}
    monkeypatch.setattr(mod, "check_env", lambda s: seen.setdefault("ks", s.keyspace) and
                        {"connected": True, "keyspace_exists": True})
    monkeypatch.setenv("CASSANDRA_KEYSPACE", "ride_booking_demo")
    assert mod.main(["--keyspace", "ride_booking_test"]) == 0
    assert seen["ks"] == "ride_booking_test"
