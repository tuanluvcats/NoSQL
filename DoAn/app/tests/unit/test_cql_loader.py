from config import CASSANDRA_DIR
from db.cql_loader import split_statements
from db.migrate import MIGRATION_CQL


def test_split_ignores_semicolon_in_string_and_comment():
    text = "INSERT INTO t (a) VALUES ('x;y');\n-- c; d\nSELECT 1;"
    assert split_statements(text) == ["INSERT INTO t (a) VALUES ('x;y')", "SELECT 1"]


def test_split_handles_escaped_quote():
    assert len(split_statements("INSERT INTO t (a) VALUES ('it''s; ok');")) == 1


def test_schema_file_statement_counts():
    stmts = split_statements((CASSANDRA_DIR / "01_schema.cql").read_text(encoding="utf-8"))
    assert sum(s.startswith("CREATE TABLE") for s in stmts) == 13
    assert sum(s.startswith("CREATE MATERIALIZED VIEW") for s in stmts) == 1
    assert sum(s.startswith("CREATE KEYSPACE") for s in stmts) == 1


def test_migration_file_is_single_alter():
    stmts = split_statements((CASSANDRA_DIR / "06_app_migration.cql").read_text(encoding="utf-8"))
    stmts = [s for s in stmts if not s.upper().startswith("USE ")]
    assert stmts == [MIGRATION_CQL]
