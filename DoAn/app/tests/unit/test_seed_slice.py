import pytest

from config import CASSANDRA_DIR
from db.cql_loader import split_statements
from tools.seed import EXPECTED_SEED_COUNTS, SeedFormatError, count_by_table, seed_statements

DATA = CASSANDRA_DIR / "02_data.cql"


def test_seed_counts_match_expected():
    assert count_by_table(seed_statements(DATA)) == EXPECTED_SEED_COUNTS


def test_seed_statements_are_pure_inserts():
    stmts = seed_statements(DATA)
    for s in stmts:
        assert s.startswith("INSERT INTO ")
        assert "'CUST016'" not in s
        assert "TRUNCATE" not in s.upper()
        assert "DELETE" not in s.upper()


def test_truncate_before_driver_locations_block_is_rejected(tmp_path):
    p = tmp_path / "bad.cql"
    p.write_text(
        "USE ride_booking;\n"
        "INSERT INTO customers (customer_id) VALUES ('C1');\n"
        "TRUNCATE x;\n"
        "INSERT INTO driver_locations (driver_id) VALUES ('D1');\n",
        encoding="utf-8",
    )
    with pytest.raises(SeedFormatError):
        seed_statements(p)


def test_02_data_has_only_inserts():
    stmts = split_statements(DATA.read_text(encoding="utf-8"))
    stmts = [s for s in stmts if not s.upper().startswith("USE ")]
    assert stmts
    for s in stmts:
        assert s.startswith("INSERT INTO ")
        up = s.upper()
        assert "TRUNCATE" not in up and "DELETE" not in up and not up.startswith("SELECT")
