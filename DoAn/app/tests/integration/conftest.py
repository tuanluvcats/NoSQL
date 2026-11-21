import dataclasses
import os

import pytest

from config import CASSANDRA_DIR, Settings, UnsafeKeyspaceError, assert_test_keyspace
from db.migrate import create_test_keyspace, ensure_app_migration
from db.repo import CassandraDb
from db.session import connect
from tools.seed import load_seed, reset_tables


@pytest.fixture(scope="session")
def settings_test():
    ks = os.environ.get("CASSANDRA_TEST_KEYSPACE", "ride_booking_test")
    try:
        assert_test_keyspace(ks)
    except UnsafeKeyspaceError:
        pytest.exit(f"Từ chối chạy: keyspace '{ks}' không kết thúc bằng _test", returncode=4)
    return dataclasses.replace(Settings.from_env(), keyspace=ks)


@pytest.fixture(scope="session")
def cassandra_session(settings_test):
    from cassandra.cluster import NoHostAvailable

    try:
        cluster, session = connect(settings_test)
    except (NoHostAvailable, OSError):
        pytest.skip(f"Không có Cassandra ở {','.join(settings_test.hosts)}:{settings_test.port}")
    yield session
    cluster.shutdown()


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


@pytest.fixture
def db(raw, test_keyspace):
    return CassandraDb(raw, test_keyspace)
