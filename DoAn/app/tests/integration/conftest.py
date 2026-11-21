import dataclasses
import os

import pytest

from config import CASSANDRA_DIR, Settings, UnsafeKeyspaceError, assert_test_keyspace
from db.migrate import create_test_keyspace, ensure_app_migration
from db.repo import CassandraDb
from db.session import connect
from tests.seed_state import SeedState


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


@pytest.fixture(scope="session")
def seed_state(cassandra_session, test_keyspace):
    """Theo dõi bảng bị ghi để mỗi test chỉ phải reset phần bẩn (xem tests/seed_state.py)."""
    state = SeedState(cassandra_session, test_keyspace, CASSANDRA_DIR / "02_data.cql")
    yield state
    state.close()


@pytest.fixture
def raw(cassandra_session, seed_state):
    """Session đã set_keyspace, dữ liệu đúng seed + dấu rated_at (D9). Test được tự do ghi."""
    seed_state.reset()
    return cassandra_session


@pytest.fixture
def raw_readonly(cassandra_session, seed_state):
    """Như `raw` nhưng cam kết test CHỈ ĐỌC: nếu test ghi bất kỳ bảng nào thì fail ở teardown
    (để không ai chuyển nhầm test ghi sang fixture này)."""
    seed_state.reset()
    before = seed_state.write_count
    yield cassandra_session
    wrote = seed_state.write_count - before
    assert wrote == 0, f"Test dùng raw_readonly nhưng đã ghi {wrote} lệnh; hãy dùng fixture `raw`/`db`."


@pytest.fixture
def db(raw, test_keyspace):
    return CassandraDb(raw, test_keyspace)


@pytest.fixture
def db_readonly(raw_readonly, test_keyspace):
    return CassandraDb(raw_readonly, test_keyspace)


@pytest.fixture
def client_factory(settings_test, db):
    """client_factory(clock=None) -> TestClient gắn vào keyspace _test (mỗi client có cookie session riêng)."""
    from fastapi.testclient import TestClient

    from main import create_app

    def make(clock=None):
        return TestClient(create_app(settings_test, db=db, clock=clock), follow_redirects=False)

    return make


def login(client, username, password="123456"):
    """POST /login; trả response (303 nếu thành công)."""
    return client.post("/login", data={"username": username, "password": password})
