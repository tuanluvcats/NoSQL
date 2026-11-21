"""Chạy migration ứng dụng (ADD rated_at). Chạy lại nhiều lần được."""
from __future__ import annotations

import argparse

from config import Settings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Áp dụng 06_app_migration (ALTER TABLE rides ADD rated_at)")
    ap.add_argument("--keyspace", required=True)
    args = ap.parse_args(argv)
    from db.migrate import ensure_app_migration
    from tools.check_env import connect

    session = connect(Settings.from_env())
    try:
        changed = ensure_app_migration(session, args.keyspace)
    finally:
        session.cluster.shutdown()
    print("Đã thêm cột rides.rated_at" if changed else "Cột rides.rated_at đã có, không làm gì")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
