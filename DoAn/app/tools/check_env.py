"""Kiểm môi trường Cassandra của máy hiện tại (chỉ dùng driver, không cần cqlsh)."""
from __future__ import annotations

import sys

from config import Settings


def connect(settings: Settings, timeout: float = 5.0):
    from cassandra.cluster import Cluster
    from cassandra.policies import DCAwareRoundRobinPolicy

    cluster = Cluster(
        list(settings.hosts),
        port=settings.port,
        protocol_version=4,
        connect_timeout=timeout,
        control_connection_timeout=timeout,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=settings.local_dc),
    )
    try:
        session = cluster.connect()
    except BaseException:
        cluster.shutdown()
        raise
    session.default_timeout = 30
    return session


def check_env(settings: Settings) -> dict:
    result = {
        "connected": False,
        "release_version": None,
        "keyspace_exists": False,
        "tables": 0,
        "has_rated_at": False,
        "error": None,
    }
    session = None
    try:
        session = connect(settings)
        result["connected"] = True
        row = session.execute("SELECT release_version FROM system.local").one()
        result["release_version"] = row.release_version if row else None
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
        if session is not None:
            session.cluster.shutdown()
    return result


def main() -> int:
    settings = Settings.from_env()
    r = check_env(settings)
    print(f"Máy chủ: {','.join(settings.hosts)}:{settings.port}  keyspace: {settings.keyspace}")
    for k, v in r.items():
        print(f"{k}: {v}")
    return 0 if r["connected"] and r["keyspace_exists"] else 1


if __name__ == "__main__":
    sys.exit(main())
