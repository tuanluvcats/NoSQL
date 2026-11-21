import dataclasses
import os

import pytest

from config import CASSANDRA_DIR, Settings, UnsafeKeyspaceError, assert_test_keyspace
from db.migrate import create_test_keyspace, ensure_app_migration
from tools.seed import load_seed, reset_tables


@pytest.fixture(scope="session")
def settings_test():
    ks = os.environ.get("CASSANDRA_TEST_KEYSPACE", "ride_booking_test")
    try:
        assert_test_keyspace(ks)
    except UnsafeKeyspaceError:
        pytest.exit(f"Từ chối chạy: keyspace '{ks}' không kết thúc bằng _test", returncode=4)
    return dataclasses.replace(Settings.from_env(), keyspace=ks)


def connect(settings, timeout: float = 5.0):
    # Tạm viết ở đây; Task 3 chuyển sang db/session.py
    from cassandra.cluster import Cluster
    from cassandra.policies import DCAwareRoundRobinPolicy

    cluster = Cluster(
        list(settings.hosts),
        port=settings.port,
        protocol_version=4,
        connect_timeout=timeout,
        control_connection_timeout=timeout,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=settings.local_dc),
    )
    try:
        session = cluster.connect()
    except BaseException:
        cluster.shutdown()
        raise
    session.default_timeout = 30
    return session


@pytest.fixture(scope="session")
def cassandra_session(settings_test):
    from cassandra.cluster import NoHostAvailable

    try:
        session = connect(settings_test, timeout=5.0)
    except (NoHostAvailable, OSError):
        pytest.skip(f"Không có Cassandra ở {','.join(settings_test.hosts)}:{settings_test.port}")
    yield session
    session.cluster.shutdown()


@pytest.fixture(scope="session")
def test_keyspace(settings_test, cassandra_session):
    create_test_keyspace(cassandra_session, settings_test.keyspace, CASSANDRA_DIR / "01_schema.cql")
    ensure_app_migration(cassandra_session, settings_test.keyspace)
    return settings_test.keyspace


@pytest.fixture
def raw(cassandra_session, test_keyspace):
    reset_tables(cassandra_session, test_keyspace)
    load_seed(cassandra_session, test_keyspace, CASSANDRA_DIR / "02_data.cql")
    cassandra_session.set_keyspace(test_keyspace)
    return cassandra_session
