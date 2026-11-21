"""CassandraDb: chạy câu CQL trong catalog (prepare lười, cache theo tên) và ghi trace."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Protocol, Sequence

from cassandra import ConsistencyLevel

from db import trace
from db.catalog import STATEMENTS, Stmt


@dataclass(frozen=True)
class LwtResult:
    applied: bool
    current: dict | None


class Db(Protocol):
    keyspace: str

    def rows(self, name: str, params: Sequence = ()) -> list[dict]: ...
    def one(self, name: str, params: Sequence = ()) -> dict | None: ...
    def exec(self, name: str, params: Sequence = ()) -> None: ...
    def lwt(self, name: str, params: Sequence = ()) -> LwtResult: ...
    def raw(self, code: str, table: str, cql: str, params: Sequence = (), kind: str = "read") -> list[dict]: ...


def _fmt(v, limit: int = 200) -> str:
    s = v if isinstance(v, str) else str(v)
    return s if len(s) <= limit else s[: limit - 3] + "..."


class CassandraDb:
    def __init__(self, session, keyspace: str, consistency_name: str = "LOCAL_QUORUM"):
        self.session = session
        self.keyspace = keyspace
        self.consistency_name = consistency_name
        self._cl = ConsistencyLevel.name_to_value[consistency_name]
        self._prepared: dict[str, object] = {}
        self._lock = threading.Lock()

    # -- nội bộ ---------------------------------------------------------
    def _prepare(self, key: str, cql: str):
        with self._lock:
            p = self._prepared.get(key)
            if p is None:
                p = self.session.prepare(cql)
                p.consistency_level = self._cl
                self._prepared[key] = p
            return p

    def _run(self, *, name: str, code: str, q: str, table: str, cql: str, kind: str,
             pk: tuple, params: Sequence, prepared) -> list[dict]:
        params = list(params)
        entry = trace.TraceEntry(
            name=name, code=code, q=q, table=table, cql=cql,
            params=[_fmt(p) for p in params],
            partition_key={col: _fmt(params[i]) for col, i in pk if i < len(params)},
            consistency=self.consistency_name, kind=kind, applied=None, current=None,
            row_count=0, elapsed_ms=0.0, error=None,
        )
        t0 = time.perf_counter()
        try:
            if prepared is None:  # lệnh không tham số (vd TRUNCATE): TRUNCATE có thể chậm hơn 15 giây
                if cql.lstrip().upper().startswith("TRUNCATE"):
                    result = self.session.execute(cql, (), timeout=120)
                else:
                    result = self.session.execute(cql, ())
            else:
                result = self.session.execute(prepared, params)
            rows = list(result) if result is not None else []
        except BaseException as e:
            entry.elapsed_ms = (time.perf_counter() - t0) * 1000
            entry.error = f"{type(e).__name__}: {e}"
            trace.record(entry)
            raise
        entry.elapsed_ms = (time.perf_counter() - t0) * 1000
        if kind == "lwt":
            if rows and "[applied]" in rows[0]:
                entry.applied = bool(rows[0]["[applied]"])
                cur = {k: v for k, v in rows[0].items() if k != "[applied]"}
                entry.current = cur or None
            entry.row_count = len(rows)
        else:
            entry.row_count = len(rows)
        trace.record(entry)
        return rows

    def _stmt(self, name: str) -> Stmt:
        return STATEMENTS[name]  # KeyError nếu sai tên: lỗi lập trình, để nổ sớm

    def _run_named(self, name: str, params: Sequence) -> tuple[Stmt, list[dict]]:
        s = self._stmt(name)
        rows = self._run(name=s.name, code=s.code, q=s.q, table=s.table, cql=s.cql, kind=s.kind,
                         pk=s.pk, params=params, prepared=self._prepare(name, s.cql))
        return s, rows

    # -- API công khai --------------------------------------------------
    def rows(self, name: str, params: Sequence = ()) -> list[dict]:
        return self._run_named(name, params)[1]

    def one(self, name: str, params: Sequence = ()) -> dict | None:
        rows = self.rows(name, params)
        return rows[0] if rows else None

    def exec(self, name: str, params: Sequence = ()) -> None:
        self._run_named(name, params)

    def lwt(self, name: str, params: Sequence = ()) -> LwtResult:
        s = self._stmt(name)
        if s.kind != "lwt":
            raise ValueError(f"{name} không phải câu LWT (kind={s.kind})")
        _, rows = self._run_named(name, params)
        if not rows or "[applied]" not in rows[0]:
            raise RuntimeError(f"{name}: kết quả LWT không có cột [applied]")
        row = rows[0]
        current = {k: v for k, v in row.items() if k != "[applied]"}
        return LwtResult(bool(row["[applied]"]), current or None)

    def raw(self, code: str, table: str, cql: str, params: Sequence = (), kind: str = "read") -> list[dict]:
        """Chạy CQL ngoài catalog (backup/restore, thông tin schema). Có tham số thì prepare và cache theo cql."""
        params = list(params)
        prepared = self._prepare("raw:" + cql, cql) if params else None
        return self._run(name=code, code=code, q="", table=table, cql=cql, kind=kind,
                         pk=(), params=params, prepared=prepared)
