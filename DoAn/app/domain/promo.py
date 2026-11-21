"""Kiểm hợp lệ mã khuyến mãi (thuần, không ghi DB)."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

from domain.tz import to_vn


def promo_error(promo: Mapping | None, city: str, fare: float, now: datetime) -> str | None:
    """Thứ tự kiểm: not_found, not_started, expired, city, min_fare, exhausted."""
    if not promo:
        return 'not_found'
    now_v = to_vn(now)
    valid_from = promo.get('valid_from')
    valid_to = promo.get('valid_to')
    if valid_from is not None and now_v < to_vn(valid_from):
        return 'not_started'
    if valid_to is not None and now_v > to_vn(valid_to):
        return 'expired'
    if city not in (promo.get('cities') or ()):
        return 'city'
    if fare < (promo.get('min_fare') or 0):
        return 'min_fare'
    limit = promo.get('usage_limit')
    if limit is not None and (promo.get('used_count') or 0) >= limit:
        return 'exhausted'
    return None
