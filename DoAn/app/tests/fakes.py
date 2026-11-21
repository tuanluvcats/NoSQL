"""FakeDb: thay CassandraDb trong unit test (không cần Cassandra)."""
from __future__ import annotations

from db.repo import LwtResult


class FakeDb:
    def __init__(self, responses: dict[str, list] | None = None, keyspace: str = "ride_booking_test"):
        self.keyspace = keyspace
        self._responses: dict[str, list] = {k: list(v) for k, v in (responses or {}).items()}
        self.calls: list[tuple[str, tuple]] = []

    def queue(self, name: str, *responses) -> "FakeDb":
        self._responses.setdefault(name, []).extend(responses)
        return self

    def names(self) -> list[str]:
        return [n for n, _ in self.calls]

    def _next(self, name: str, params, default):
        self.calls.append((name, tuple(params)))
        queue = self._responses.get(name)
        if not queue:
            return default
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def rows(self, name, params=()) -> list[dict]:
        item = self._next(name, params, [])
        if item is None:
            return []
        if isinstance(item, dict):
            return [item]
        return list(item)

    def one(self, name, params=()) -> dict | None:
        item = self._next(name, params, None)
        if isinstance(item, list):
            return item[0] if item else None
        return item

    def exec(self, name, params=()) -> None:
        self._next(name, params, None)

    def lwt(self, name, params=()) -> LwtResult:
        item = self._next(name, params, LwtResult(True, None))
        if isinstance(item, bool):
            return LwtResult(item, None)
        return item

    def raw(self, code, table, cql, params=(), kind="read") -> list[dict]:
        item = self._next(code, params, [])
        return [] if item is None else list(item)
