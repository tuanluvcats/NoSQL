from config import Settings
from tools.check_env import check_env


def test_check_env_closed_port_does_not_raise():
    s = Settings.from_env({"CASSANDRA_HOSTS": "127.0.0.1", "CASSANDRA_PORT": "1"})
    r = check_env(s)
    assert r["connected"] is False
    assert r["error"]
