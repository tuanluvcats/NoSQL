"""Cấu hình ứng dụng, hằng số nghiệp vụ dùng chung và guard keyspace _test."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

APP_DIR: Path = Path(__file__).resolve().parent
CASSANDRA_DIR: Path = APP_DIR.parent / "cassandra"

# Lấy từ PLACES của DoAn/cassandra/tools/gen_data.py
AREAS = {
    "HCM": ("Q1", "Q3", "TAN_PHU", "TAN_BINH", "BINH_THANH", "GO_VAP"),
    "HN": ("HOAN_KIEM", "CAU_GIAY", "DONG_DA", "NAM_TU_LIEM", "SOC_SON"),
}
PAYMENT_METHODS = ("CASH", "MOMO", "ZALOPAY", "CARD")
RATING_TAGS = ("Đúng giờ", "Lịch sự", "Xe sạch", "Nhiệt tình", "Đường vòng", "Mất tập trung")

# Thứ tự theo 99_reset_data.cql (13 bảng, không gồm MV vehicles_by_plate)
BASE_TABLES = (
    "customers",
    "drivers",
    "vehicles",
    "rides_by_customer",
    "user_accounts",
    "rides",
    "rides_by_driver_month",
    "rides_by_area_date",
    "drivers_by_area",
    "driver_locations",
    "ratings_by_driver",
    "payments_by_city_date",
    "promotions",
)

def ensure_utf8_stdout() -> None:
    """Để CLI in được tiếng Việt trên console Windows cp1252 mà không cần đặt biến môi trường."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


_TRUTHY = frozenset({"1", "true", "yes", "on"})
_KEYSPACE_RE = re.compile(r"^[a-z][a-z0-9_]{0,47}$")


class UnsafeKeyspaceError(RuntimeError):
    """Keyspace không kết thúc bằng _test nên không được phép xóa/ghi đè."""


def assert_test_keyspace(name: str) -> None:
    if not name.endswith("_test"):
        raise UnsafeKeyspaceError(f"Từ chối chạy: keyspace '{name}' không kết thúc bằng _test")


@dataclass(frozen=True)
class Settings:
    hosts: tuple[str, ...]
    port: int
    keyspace: str
    local_dc: str
    secret_key: str
    backup_dir: Path
    first_month: int = 202609
    debug: bool = False  # APP_DEBUG=1: trang lỗi 500 mới hiện loại lỗi và thông điệp (mặc định ẩn)
    tech_mode: bool = False  # APP_TECH_MODE=1: mặc định hiện CQL và ghi chú kỹ thuật (người dùng vẫn đổi được bằng cookie ở chân trang)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        hosts = tuple(h.strip() for h in e.get("CASSANDRA_HOSTS", "127.0.0.1").split(",") if h.strip())
        if not hosts:
            raise ValueError("CASSANDRA_HOSTS rỗng")
        port = int(e.get("CASSANDRA_PORT", "9042"))
        keyspace = e.get("CASSANDRA_KEYSPACE", "ride_booking_demo").strip()
        if not _KEYSPACE_RE.match(keyspace):
            raise ValueError(f"Tên keyspace không hợp lệ: {keyspace!r}")
        return cls(
            hosts=hosts,
            port=port,
            keyspace=keyspace,
            local_dc=e.get("CASSANDRA_LOCAL_DC", "datacenter1"),
            secret_key=e.get("APP_SECRET_KEY", "dev-secret-change-me"),
            backup_dir=Path(e.get("APP_BACKUP_DIR", str(APP_DIR / "backups"))),
            debug=e.get("APP_DEBUG", "").strip().lower() in _TRUTHY,
            tech_mode=e.get("APP_TECH_MODE", "").strip().lower() in _TRUTHY,
        )
