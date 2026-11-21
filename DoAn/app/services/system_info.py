"""Thông tin hệ thống cho trang Kết nối (mục 8) và trang NoSQL minh họa. Không bao giờ trả khóa phiên hay mật khẩu."""
from __future__ import annotations

from cassandra import InvalidRequest

from db.migrate import has_column

# Câu bị Cassandra từ chối vì thiếu partition key (Q17 / A10 trong CASSANDRA.MD §7)
MISSING_PK_CQL = "SELECT ride_id FROM rides WHERE customer_id = 'CUST001'"


def connection_info(db, settings) -> dict:
    """Thông tin kết nối hiện tại. Lỗi truy vấn/kết nối được ghi ở khóa `error` thay vì ném ra."""
    info: dict = {
        "hosts": list(settings.hosts), "port": settings.port, "local_dc": settings.local_dc,
        "keyspace": settings.keyspace, "protocol_version": None, "release_version": None, "cluster_name": None,
        "data_center": None, "cql_version": None, "tables": [], "views": [], "migration_ok": False,
        "consistency": getattr(db, "consistency_name", None), "error": None,
    }
    if db is None:
        info["error"] = "Chưa có kết nối Cassandra."
        return info
    try:
        session = getattr(db, "session", None)
        info["protocol_version"] = getattr(getattr(session, "cluster", None), "protocol_version", None)
        local = db.one("SYS_local") or {}
        for key in ("release_version", "cluster_name", "data_center", "cql_version"):
            info[key] = local.get(key)
        info["tables"] = sorted(r["table_name"] for r in db.rows("SYS_tables", [settings.keyspace]))
        info["views"] = sorted(r["view_name"] for r in db.rows("SYS_views", [settings.keyspace]))
        info["migration_ok"] = bool(session is not None and has_column(session, settings.keyspace, "rides", "rated_at"))
    except Exception as e:  # noqa: BLE001 - hiển thị lỗi thay vì sập trang
        info["error"] = f"{type(e).__name__}: {e}"
    return info


def missing_pk_demo(db) -> str:
    """Chạy câu thiếu partition key (A10) và trả NGUYÊN VĂN thông điệp lỗi do Cassandra trả về."""
    try:
        db.raw("A10", "rides", MISSING_PK_CQL)
    except InvalidRequest as e:
        return str(e)
    return "Cassandra không từ chối câu truy vấn này (bất thường): kiểm tra lại schema."


def collections_demo(db) -> dict:
    """Dữ liệu minh họa map/list/set và clustering DESC (A08, B10) lấy từ keyspace đang dùng."""
    return {
        "B06": db.one("B06_ride_get", ["RIDE_1007"]),  # map<timestamp,text> status_history
        "A08_rating_tags": db.rows("A08_rating_tags", ["DRV_551"]),  # list<text> tags
        "A08_rating_ride_1007": [r for r in db.rows("B14_ratings", ["DRV_552"]) if r.get("ride_id") == "RIDE_1007"],
        "A08_promo_cities": db.rows("A08_promo_cities", [["GIAM20", "HCMXANH", "HANOI10"]]),  # set<text> cities
        "B10": db.rows("B10_driver_month", ["DRV_551", 202610]),  # CLUSTERING ORDER BY (requested_at DESC, ...)
    }
