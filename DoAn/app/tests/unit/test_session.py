import pytest

from config import Settings
from db import session as sess

pytestmark = pytest.mark.nosql


def test_connect_unreachable_raises():
    s = Settings.from_env({"CASSANDRA_HOSTS": "127.0.0.1", "CASSANDRA_PORT": "1"})
    from cassandra.cluster import NoHostAvailable

    with pytest.raises(NoHostAvailable):
        sess.connect(s)


def test_connect_uses_protocol_v4_and_local_quorum(monkeypatch):
    seen = {}

    class FakeCluster:
        def __init__(self, hosts, **kw):
            seen["hosts"], seen["kw"] = hosts, kw

        def connect(self, keyspace=None):
            seen["keyspace"] = keyspace
            return "SESSION"

        def shutdown(self):
            pass

    monkeypatch.setattr(sess, "Cluster", FakeCluster)
    s = Settings.from_env({"CASSANDRA_HOSTS": "a,b", "CASSANDRA_PORT": "9999", "CASSANDRA_LOCAL_DC": "dc9"})
    cluster, session = sess.connect(s, keyspace="ks_test")
    assert session == "SESSION" and seen["keyspace"] == "ks_test"
    assert isinstance(cluster, FakeCluster)
    assert seen["hosts"] == ["a", "b"]
    kw = seen["kw"]
    assert kw["port"] == 9999 and kw["protocol_version"] == 4 and kw["connect_timeout"] == 5
    from cassandra import ConsistencyLevel
    from cassandra.cluster import EXEC_PROFILE_DEFAULT
    from cassandra.query import dict_factory

    prof = kw["execution_profiles"][EXEC_PROFILE_DEFAULT]
    assert prof.consistency_level == ConsistencyLevel.LOCAL_QUORUM
    assert prof.serial_consistency_level == ConsistencyLevel.LOCAL_SERIAL
    assert prof.row_factory is dict_factory
    assert prof.request_timeout == 15
    assert prof.load_balancing_policy.__class__.__name__ == "TokenAwarePolicy"


def test_connect_without_keyspace_calls_connect_plain(monkeypatch):
    seen = {}

    class FakeCluster:
        def __init__(self, hosts, **kw):
            pass

        def connect(self, *args):
            seen["args"] = args
            return "S"

        def shutdown(self):
            pass

    monkeypatch.setattr(sess, "Cluster", FakeCluster)
    sess.connect(Settings.from_env({}))
    assert seen["args"] == ()


def test_connect_shuts_cluster_down_on_failure(monkeypatch):
    holder = {}

    class FakeCluster:
        def __init__(self, hosts, **kw):
            holder["c"] = self
            self.down = False

        def connect(self, *args):
            raise OSError("x")

        def shutdown(self):
            self.down = True

    monkeypatch.setattr(sess, "Cluster", FakeCluster)
    with pytest.raises(OSError):
        sess.connect(Settings.from_env({}))
    assert holder["c"].down is True
