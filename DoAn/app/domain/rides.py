"""Máy trạng thái chuyến đi."""
from __future__ import annotations

from datetime import datetime
from typing import Mapping

from domain.tz import to_vn

STATUSES = ('REQUESTED', 'ACCEPTED', 'ONGOING', 'COMPLETED', 'CANCELLED')
TRANSITIONS = {
    'REQUESTED': {'ACCEPTED', 'CANCELLED'},
    'ACCEPTED': {'ONGOING', 'CANCELLED'},
    'ONGOING': {'COMPLETED'},
}
CANCELLABLE = ('REQUESTED', 'ACCEPTED')


def can_transition(src: str | None, dst: str) -> bool:
    if src is None:
        return dst == 'REQUESTED'
    return dst in TRANSITIONS.get(src, set())


def history_entries(m: Mapping | None) -> list[tuple[datetime, str]]:
    if not m:
        return []
    return sorted(((to_vn(t), s) for t, s in m.items()), key=lambda x: x[0])
