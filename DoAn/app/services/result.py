"""Kết quả chuẩn của mọi thao tác nghiệp vụ (service trả về, route hiển thị)."""
from __future__ import annotations

from dataclasses import dataclass, field

CODES = (
    "ok", "duplicate_ok", "partial", "not_found", "forbidden", "invalid_input", "invalid_transition",
    "lwt_lost", "driver_not_online", "driver_not_available", "driver_busy", "promo_invalid",
    "promo_exhausted", "promo_busy", "duplicate", "duplicate_plate", "already_rated", "has_rides",
    "in_use", "bad_credentials", "account_locked", "username_taken", "self_lock", "last_admin",
    "maintenance", "backup_invalid",
)


@dataclass
class ActionResult:
    ok: bool
    code: str
    message: str
    ride_id: str | None = None
    current: dict | None = None
    data: dict = field(default_factory=dict)
