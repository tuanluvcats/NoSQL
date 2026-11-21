"""Nạp dữ liệu seed từ 02_data.cql bằng bộ cắt (dừng sau khối driver_locations)."""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from config import BASE_TABLES, CASSANDRA_DIR, Settings, ensure_utf8_stdout
from db.cql_loader import split_statements

EXPECTED_SEED_COUNTS = {
    "customers": 10,
    "drivers": 10,
    "vehicles": 10,
    "user_accounts": 22,
    "rides": 36,
    "rides_by_customer": 36,
    "rides_by_area_date": 36,
    "rides_by_driver_month": 34,
    "payments_by_city_date": 27,
    "ratings_by_driver": 23,
    "drivers_by_area": 6,
    "driver_locations": 18,
    "promotions": 3,
}

_INSERT_RE = re.compile(r"^INSERT INTO (\w+)")


class SeedFormatError(RuntimeError):
    pass


def seed_statements(path: Path) -> list[str]:
    stmts = split_statements(Path(path).read_text(encoding="utf-8"))
    out: list[str] = []
    seen_loc = False
    for s in stmts:
        if s.upper().startswith("USE "):
            continue
        is_loc = s.startswith("INSERT INTO driver_locations")
        if seen_loc and not is_loc:
            break
        if not s.startswith("INSERT INTO "):
            raise SeedFormatError(f"Lệnh không phải INSERT trong phần seed: {s[:60]!r}")
        seen_loc = seen_loc or is_loc
        out.append(s)
    got = count_by_table(out)
    if got != EXPECTED_SEED_COUNTS:
        raise SeedFormatError(f"Số dòng seed không khớp. Thực tế: {got}; mong đợi: {EXPECTED_SEED_COUNTS}")
    return out


def count_by_table(stmts) -> dict[str, int]:
    c: Counter = Counter()
    for s in stmts:
        m = _INSERT_RE.match(s)
        if m:
            c[m.group(1)] += 1
    return dict(c)


def reset_tables(session, keyspace: str) -> None:
    session.set_keyspace(keyspace)
    for t in BASE_TABLES:
        session.execute(f"TRUNCATE {t}", timeout=120)


def load_seed(session, keyspace: str, path: Path) -> dict[str, int]:
    from cassandra.concurrent import execute_concurrent

    stmts = seed_statements(path)
    session.set_keyspace(keyspace)
    execute_concurrent(session, [(s, ()) for s in stmts], concurrency=50, raise_on_first_error=True)
    return count_by_table(stmts)


def main(argv=None) -> int:
    ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="TRUNCATE 13 bảng rồi nạp seed từ 02_data.cql")
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--yes", action="store_true", help="xác nhận xóa dữ liệu hiện có")
    args = ap.parse_args(argv)
    if not args.yes:
        print("Từ chối: lệnh này TRUNCATE dữ liệu. Thêm --yes để xác nhận.", file=sys.stderr)
        return 2
    from db.session import connect

    cluster, session = connect(Settings.from_env())
    try:
        reset_tables(session, args.keyspace)
        counts = load_seed(session, args.keyspace, CASSANDRA_DIR / "02_data.cql")
    finally:
        cluster.shutdown()
    for t, n in counts.items():
        print(f"{t}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
