import pytest

from config import BASE_TABLES, CASSANDRA_DIR
from db.migrate import ensure_app_migration, has_column
from db.repo import CassandraDb
from domain.tz import parse_vn
from services.rating import backfill_rated_at, rate_ride
from tools.seed import EXPECTED_SEED_COUNTS
from tools.setup_db import setup_db


def test_tables_and_view(raw_readonly, test_keyspace):
    s = raw_readonly
    tables = {r["table_name"] for r in s.execute(
        "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", (test_keyspace,))}
    views = {r["view_name"] for r in s.execute(
        "SELECT view_name FROM system_schema.views WHERE keyspace_name = %s", (test_keyspace,))}
    assert tables == set(BASE_TABLES)
    assert views == {"vehicles_by_plate"}


def test_rated_at_column(raw_readonly, test_keyspace):
    assert has_column(raw_readonly, test_keyspace, "rides", "rated_at") is True


def test_seed_counts(raw_readonly):
    for table, expected in EXPECTED_SEED_COUNTS.items():
        n = raw_readonly.execute(f"SELECT COUNT(*) FROM {table}").one()["count"]
        assert n == expected, table


def test_ensure_app_migration_second_call_false(raw_readonly, test_keyspace):
    assert ensure_app_migration(raw_readonly, test_keyspace) is False


def test_setup_db_twice_keeps_data(raw, test_keyspace):
    schema = CASSANDRA_DIR / "01_schema.cql"
    setup_db(raw, test_keyspace, seed=False, schema_path=schema)
    raw.execute("INSERT INTO customers (customer_id, full_name) VALUES ('CUST_SMOKE', 'Smoke')")
    setup_db(raw, test_keyspace, seed=False, schema_path=schema)
    row = raw.execute("SELECT customer_id FROM customers WHERE customer_id = 'CUST_SMOKE'").one()
    assert row is not None


def test_setup_db_with_seed_marks_rated_rides_and_refuses_second_rating(raw, test_keyspace):
    """setup_db(seed=True) tự backfill rated_at: chuyến seed đã có đánh giá không được đánh giá lại."""
    schema = CASSANDRA_DIR / "01_schema.cql"
    counts = setup_db(raw, test_keyspace, seed=True, schema_path=schema)
    assert counts["rated_at_backfill"] >= 1
    db = CassandraDb(raw, test_keyspace)
    assert db.one("B06_ride_get", ["RIDE_1001"])["rated_at"] is not None
    assert db.one("B06_ride_get", ["RIDE_1010"])["rated_at"] is None  # chưa có đánh giá thì để trống
    assert backfill_rated_at(db) == 0  # đã backfill đủ, chạy lại không còn gì để đánh dấu
    r = rate_ride(db, "RIDE_1001", "CUST001", 5, "Lại", [], parse_vn("2026-10-04 10:50"))
    assert not r.ok and r.code == "already_rated"
