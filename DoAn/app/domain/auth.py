"""Quy tắc phân quyền thuần. OPERATOR (điều phối) gộp vào ADMIN."""
from __future__ import annotations

from typing import Mapping

from domain.rides import CANCELLABLE

ADMIN = 'ADMIN'
CUSTOMER = 'CUSTOMER'
DRIVER = 'DRIVER'


def effective_role(role: str | None) -> str | None:
    if role in ('ADMIN', 'OPERATOR'):
        return ADMIN
    if role == 'CUSTOMER':
        return CUSTOMER
    if role == 'DRIVER':
        return DRIVER
    return None


def lock_refusal(target: Mapping, actor_username: str, active_admin_count: int) -> str | None:
    if target.get('username') == actor_username:
        return 'self_lock'
    if (effective_role(target.get('role')) == ADMIN and target.get('is_active', True)
            and active_admin_count <= 1):
        return 'last_admin'
    return None


def can_view_ride(role: str | None, ref_id: str | None, ride: Mapping) -> bool:
    r = effective_role(role)
    if r == ADMIN:
        return True
    if r == CUSTOMER:
        return ref_id is not None and ride.get('customer_id') == ref_id
    if r == DRIVER:
        return ride.get('status') == 'REQUESTED' or (ref_id is not None and ride.get('driver_id') == ref_id)
    return False


def can_cancel_ride(role: str | None, ref_id: str | None, ride: Mapping) -> bool:
    r = effective_role(role)
    status = ride.get('status')
    if r == ADMIN:
        return status in CANCELLABLE
    if r == CUSTOMER:
        return ref_id is not None and ride.get('customer_id') == ref_id and status in CANCELLABLE
    if r == DRIVER:
        return ref_id is not None and ride.get('driver_id') == ref_id and status == 'ACCEPTED'
    return False
