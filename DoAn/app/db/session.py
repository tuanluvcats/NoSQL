"""Kết nối Cassandra dùng chung cho ứng dụng, tools và test integration."""
from __future__ import annotations

from cassandra import ConsistencyLevel
from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.query import dict_factory

from config import Settings


def connect(settings: Settings, keyspace: str | None = None):
    """Trả (Cluster, Session). Lỗi kết nối thì shutdown cluster rồi ném lại.

    Session dùng protocol v4, LOCAL_QUORUM / LOCAL_SERIAL, hàng trả về dạng dict.
    Lệnh DDL/TRUNCATE chậm phải truyền `timeout=` riêng khi gọi `session.execute`.
    """
    profile = ExecutionProfile(
        load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc=settings.local_dc)),
        consistency_level=ConsistencyLevel.LOCAL_QUORUM,
        serial_consistency_level=ConsistencyLevel.LOCAL_SERIAL,
        row_factory=dict_factory,
        request_timeout=15,
    )
    cluster = Cluster(
        list(settings.hosts),
        port=settings.port,
        protocol_version=4,
        connect_timeout=5,
        control_connection_timeout=5,
        execution_profiles={EXEC_PROFILE_DEFAULT: profile},
    )
    try:
        session = cluster.connect(keyspace) if keyspace else cluster.connect()
    except BaseException:
        cluster.shutdown()
        raise
    return cluster, session
