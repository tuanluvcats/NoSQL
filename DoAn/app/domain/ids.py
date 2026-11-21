"""Sinh mã chuyến/khách. Thời điểm luôn đổi sang +07."""
from __future__ import annotations

import re
import secrets
from datetime import datetime
from typing import Callable

from domain.tz import to_vn

RIDE_ID_RE = r'^RIDE_\d{14}_[0-9A-F]{4}$'


def _rand_default() -> str:
    return secrets.token_hex(2).upper()


def _stamp(now: datetime) -> str:
    return to_vn(now).strftime('%Y%m%d%H%M%S')


def new_ride_id(now: datetime, rand: Callable[[], str] | None = None) -> str:
    return f'RIDE_{_stamp(now)}_{(rand or _rand_default)()}'


def is_new_ride_id(s: str) -> bool:
    return bool(re.match(RIDE_ID_RE, s or ''))


def new_customer_id(now: datetime, rand: Callable[[], str] | None = None) -> str:
    return f'CUST_{_stamp(now)}_{(rand or _rand_default)()}'
