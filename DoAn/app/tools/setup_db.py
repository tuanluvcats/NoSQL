"""Dựng keyspace + 13 bảng + MV bằng driver (không cần cqlsh, không bao giờ DROP)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import CASSANDRA_DIR, Settings, ensure_utf8_stdout
from db.migrate import apply_schema, ensure_app_migration
from db.repo import CassandraDb
from services.rating import backfill_rated_at
from tools.seed import load_seed, reset_tables, seed_statements


def setup_db(session, keyspace: str, *, seed: bool, schema_path: Path) -> dict[str, int]:
    apply_schema(session, keyspace, schema_path)
    ensure_app_migration(session, keyspace)
    if not seed:
        return {}
    data_path = Path(schema_path).parent / "02_data.cql"
    seed_statements(data_path)  # kiểm định dạng trước khi TRUNCATE
    reset_tables(session, keyspace)
    counts = load_seed(session, keyspace, data_path)
    # Chuyến seed đã có đánh giá phải có rated_at, nếu không sẽ đánh giá lại được (giống tools.migrate).
    counts["rated_at_backfill"] = backfill_rated_at(CassandraDb(session, keyspace))
    return counts


def main(argv=None) -> int:
    ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Tạo keyspace/bảng/MV, tùy chọn nạp seed")
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--seed", action="store_true", help="TRUNCATE 13 bảng rồi nạp seed")
    ap.add_argument("--yes", action="store_true", help="xác nhận khi dùng --seed")
    args = ap.parse_args(argv)
    if args.seed and not args.yes:
        print("Từ chối: --seed sẽ TRUNCATE dữ liệu. Thêm --yes để xác nhận.", file=sys.stderr)
        return 2
    from db.session import connect

    cluster, session = connect(Settings.from_env())
    try:
        counts = setup_db(session, args.keyspace, seed=args.seed, schema_path=CASSANDRA_DIR / "01_schema.cql")
    finally:
        cluster.shutdown()
    print(f"Đã dựng keyspace {args.keyspace}" + (f"; seed: {counts}" if args.seed else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
