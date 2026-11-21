"""Ghi vết các lệnh CQL của từng request để hiển thị ở panel "CQL đã chạy"."""
from __future__ import annotations

import secrets
import threading
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class TraceEntry:
    name: str
    code: str
    q: str
    table: str
    cql: str
    params: list[str]
    partition_key: dict
    consistency: str
    kind: str
    applied: bool | None
    current: dict | None
    row_count: int
    elapsed_ms: float
    error: str | None


_entries: ContextVar[list | None] = ContextVar("cql_trace_entries", default=None)


def start_request() -> list:
    """Bắt đầu một danh sách trace mới cho request hiện tại."""
    lst: list[TraceEntry] = []
    _entries.set(lst)
    return lst


def current() -> list:
    lst = _entries.get()
    if lst is None:
        lst = start_request()
    return lst


def record(entry: TraceEntry) -> None:
    current().append(entry)


def tables_written(entries) -> list[str]:
    """Bảng đã ghi thật (write/lwt), theo thứ tự xuất hiện, bỏ lệnh LWT bị từ chối, không lặp."""
    out: list[str] = []
    for e in entries:
        if e.kind not in ("write", "lwt") or e.applied is False or e.error:
            continue
        if e.table not in out:
            out.append(e.table)
    return out


class TraceStore:
    """Giữ trace của thao tác POST để trang sau redirect hiển thị (LRU, trong bộ nhớ)."""

    def __init__(self, maxlen: int = 100):
        self._maxlen = maxlen
        self._data: OrderedDict[str, list] = OrderedDict()
        self._lock = threading.Lock()

    def put(self, entries) -> str:
        token = secrets.token_urlsafe(12)
        with self._lock:
            self._data[token] = list(entries)
            while len(self._data) > self._maxlen:
                self._data.popitem(last=False)
        return token

    def get(self, token: str | None) -> list | None:
        if not token:
            return None
        with self._lock:
            return self._data.get(token)

    def pop(self, token: str | None) -> list | None:
        if not token:
            return None
        with self._lock:
            return self._data.pop(token, None)
