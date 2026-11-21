"""Bộ theo dõi bảng bẩn của fixture integration: phân tích CQL phải thiên về an toàn."""
import pytest

from tests.seed_state import written_tables

KS = "ride_booking_test"


@pytest.mark.parametrize("cql,expected", [
    ("INSERT INTO rides (ride_id) VALUES ('x')", {"rides"}),
    ("  insert into Customers (a) values (1)", {"customers"}),
    ("INSERT INTO ride_booking_test.drivers (a) VALUES (1)", {"drivers"}),
    ("UPDATE rides SET status = 'X' WHERE ride_id = ? IF status = 'A'", {"rides"}),
    ("DELETE FROM drivers_by_area WHERE city = ? AND district = ? AND driver_id = ?", {"drivers_by_area"}),
    ("DELETE rated_at FROM rides WHERE ride_id = ?", {"rides"}),
    ("TRUNCATE promotions", {"promotions"}),
    ("TRUNCATE TABLE promotions", {"promotions"}),
    ('INSERT INTO "customers" (a) VALUES (1)', {"customers"}),
])
def test_write_statements_report_their_table(cql, expected):
    assert written_tables(cql, KS) == frozenset(expected)


@pytest.mark.parametrize("cql", [
    "SELECT * FROM rides",
    "select count(*) from customers",
    "USE ride_booking_test",
    "SELECT release_version FROM system.local",
])
def test_reads_report_nothing(cql):
    assert written_tables(cql, KS) == frozenset()


def test_write_to_other_keyspace_is_not_ours():
    assert written_tables("INSERT INTO ride_booking.rides (ride_id) VALUES ('x')", KS) == frozenset()


@pytest.mark.parametrize("cql", [
    "CREATE TABLE IF NOT EXISTS x (a int PRIMARY KEY)",
    "ALTER TABLE rides ADD rated_at timestamp",
    "DROP KEYSPACE IF EXISTS ride_booking_test",
    "BEGIN BATCH INSERT INTO rides (ride_id) VALUES ('a'); APPLY BATCH",
    "bất kỳ thứ gì không hiểu",
])
def test_unknown_or_ddl_means_everything_dirty(cql):
    assert written_tables(cql, KS) is None
