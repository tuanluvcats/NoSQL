import pytest

from config import BASE_TABLES, CASSANDRA_DIR
from db.migrate import ensure_app_migration, has_column
from tools.seed import EXPECTED_SEED_COUNTS
from tools.setup_db import setup_db


def test_tables_and_view(raw, test_keyspace):
    s = raw
    tables = {r.table_name for r in s.execute(
        "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", (test_keyspace,))}
    views = {r.view_name for r in s.execute(
        "SELECT view_name FROM system_schema.views WHERE keyspace_name = %s", (test_keyspace,))}
    assert tables == set(BASE_TABLES)
    assert views == {"vehicles_by_plate"}


def test_rated_at_column(raw, test_keyspace):
    assert has_column(raw, test_keyspace, "rides", "rated_at") is True


def test_seed_counts(raw):
    for table, expected in EXPECTED_SEED_COUNTS.items():
        n = raw.execute(f"SELECT COUNT(*) FROM {table}").one()[0]
        assert n == expected, table


def test_ensure_app_migration_second_call_false(raw, test_keyspace):
    assert ensure_app_migration(raw, test_keyspace) is False


def test_setup_db_twice_keeps_data(raw, test_keyspace):
    schema = CASSANDRA_DIR / "01_schema.cql"
    setup_db(raw, test_keyspace, seed=False, schema_path=schema)
    raw.execute("INSERT INTO customers (customer_id, full_name) VALUES ('CUST_SMOKE', 'Smoke')")
    setup_db(raw, test_keyspace, seed=False, schema_path=schema)
    row = raw.execute("SELECT customer_id FROM customers WHERE customer_id = 'CUST_SMOKE'").one()
    assert row is not None
