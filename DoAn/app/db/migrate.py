"""Migration ứng dụng (chỉ ALTER TABLE ... ADD) và dựng schema bằng driver."""
from __future__ import annotations

import re
from pathlib import Path

from config import assert_test_keyspace
from db.cql_loader import split_statements

MIGRATION_CQL = "ALTER TABLE rides ADD rated_at timestamp"

_KS_RE = re.compile(r"CREATE KEYSPACE IF NOT EXISTS \w+")


def has_column(session, keyspace: str, table: str, column: str) -> bool:
    rows = session.execute(
        "SELECT column_name FROM system_schema.columns "
        "WHERE keyspace_name = %s AND table_name = %s AND column_name = %s",
        (keyspace, table, column),
    )
    return rows.one() is not None


def ensure_app_migration(session, keyspace: str) -> bool:
    """Trả True nếu vừa chạy ALTER, False nếu cột đã có."""
    if has_column(session, keyspace, "rides", "rated_at"):
        return False
    session.set_keyspace(keyspace)
    session.execute(MIGRATION_CQL, timeout=60)
    return True


def apply_schema(session, keyspace: str, schema_path: Path) -> None:
    """Chạy 01_schema.cql (đổi tên keyspace) bằng driver. Chỉ CREATE ... IF NOT EXISTS, không DROP."""
    text = Path(schema_path).read_text(encoding="utf-8")
    stmts = []
    for s in split_statements(text):
        head = s.upper()
        if head.startswith("USE ") or head.startswith("SELECT"):
            continue
        stmts.append(_KS_RE.sub(f"CREATE KEYSPACE IF NOT EXISTS {keyspace}", s))
    create_ks = [s for s in stmts if s.upper().startswith("CREATE KEYSPACE")]
    rest = [s for s in stmts if not s.upper().startswith("CREATE KEYSPACE")]
    for s in create_ks:
        session.execute(s, timeout=60)
    session.set_keyspace(keyspace)
    for s in rest:
        session.execute(s, timeout=60)


def create_test_keyspace(session, keyspace: str, schema_path: Path) -> None:
    assert_test_keyspace(keyspace)
    session.execute(f"DROP KEYSPACE IF EXISTS {keyspace}", timeout=120)
    apply_schema(session, keyspace, schema_path)
