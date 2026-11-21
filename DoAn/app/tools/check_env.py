"""Kiểm môi trường Cassandra của máy hiện tại (chỉ dùng driver, không cần cqlsh)."""
from __future__ import annotations

import sys

from config import Settings, ensure_utf8_stdout
from db.session import connect


def check_env(settings: Settings) -> dict:
    result = {
        "connected": False,
        "release_version": None,
        "keyspace_exists": False,
        "tables": 0,
        "has_rated_at": False,
        "error": None,
    }
    cluster = None
    try:
        cluster, session = connect(settings)
        result["connected"] = True
        row = session.execute("SELECT release_version FROM system.local").one()
        result["release_version"] = row["release_version"] if row else None
        ks = settings.keyspace
        result["keyspace_exists"] = (
            session.execute("SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = %s", (ks,)).one()
            is not None
        )
        if result["keyspace_exists"]:
            result["tables"] = len(
                list(session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", (ks,)))
            )
            from db.migrate import has_column

            result["has_rated_at"] = has_column(session, ks, "rides", "rated_at")
    except Exception as e:  # noqa: BLE001 - báo lỗi thay vì ném
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        if cluster is not None:
            cluster.shutdown()
    return result


def main() -> int:
    ensure_utf8_stdout()
    settings = Settings.from_env()
    r = check_env(settings)
    print(f"Máy chủ: {','.join(settings.hosts)}:{settings.port}  keyspace: {settings.keyspace}")
    for k, v in r.items():
        print(f"{k}: {v}")
    return 0 if r["connected"] and r["keyspace_exists"] else 1


if __name__ == "__main__":
    sys.exit(main())
