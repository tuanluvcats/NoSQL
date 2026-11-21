"""Chạy migration ứng dụng (ADD rated_at). Chạy lại nhiều lần được."""
from __future__ import annotations

import argparse

from config import Settings, ensure_utf8_stdout


def main(argv=None) -> int:
    ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Áp dụng 06_app_migration (ALTER TABLE rides ADD rated_at)")
    ap.add_argument("--keyspace", required=True)
    args = ap.parse_args(argv)
    from db.migrate import ensure_app_migration
    from db.repo import CassandraDb
    from db.session import connect
    from services.rating import backfill_rated_at

    cluster, session = connect(Settings.from_env())
    try:
        changed = ensure_app_migration(session, args.keyspace)
        session.set_keyspace(args.keyspace)
        marked = backfill_rated_at(CassandraDb(session, args.keyspace))  # D9: chuyến seed đã có đánh giá
    finally:
        cluster.shutdown()
    print("Đã thêm cột rides.rated_at" if changed else "Cột rides.rated_at đã có, không làm gì")
    print(f"Backfill rated_at: đã đánh dấu {marked} chuyến đã có đánh giá")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
