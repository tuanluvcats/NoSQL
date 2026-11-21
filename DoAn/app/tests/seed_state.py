"""Reset keyspace test về đúng dữ liệu seed, chỉ làm lại những bảng thật sự đã bị ghi.

Vì sao: fixture `raw` cũ TRUNCATE 13 bảng rồi nạp lại ~240 dòng seed và chạy backfill_rated_at (~25 LWT) ở MỌI test,
mất khoảng 2 giây một test. Phần lớn test chỉ đụng 1-5 bảng (nhiều test chỉ đọc).

Cách làm: chặn `session.execute_async` (mọi `execute`, `execute_concurrent`, `CassandraDb` đều đi qua đây), phân tích
CQL để ghi nhận bảng bị ghi. Reset chỉ TRUNCATE (song song) và nạp lại seed của các bảng bẩn. Quy tắc luôn thiên về an toàn:
CQL ghi không phân tích được, DDL, BATCH, hoặc lỗi bất kỳ khi reset thì coi MỌI bảng là bẩn.

Dấu `rated_at` của chuyến seed đã có đánh giá (D9) lấy một lần từ `backfill_rated_at` thật ở lần reset đầu tiên rồi
UPDATE lại theo danh sách đó (cùng giá trị, không cần ~25 LWT mỗi test).

Công tắc môi trường:
- RIDE_TEST_FULL_RESET=1: luôn reset đủ 13 bảng (hành vi cũ, để đối chiếu).
- RIDE_TEST_VERIFY_RESET=1: sau mỗi lần reset, đọc lại 13 bảng và so với ảnh chụp sau lần reset đầy đủ đầu tiên;
  lệch là fail ngay (dùng để kiểm chứng việc theo dõi bảng bẩn không làm yếu cô lập).
"""
from __future__ import annotations

import os
import re
import threading
from collections import defaultdict

from config import BASE_TABLES

_INSERT = re.compile(r"^\s*INSERT\s+INTO\s+([\w.\"]+)", re.I)
_UPDATE = re.compile(r"^\s*UPDATE\s+([\w.\"]+)", re.I)
_DELETE = re.compile(r"^\s*DELETE\b.*?\bFROM\s+([\w.\"]+)", re.I | re.S)
_TRUNCATE = re.compile(r"^\s*TRUNCATE\s+(?:TABLE\s+)?([\w.\"]+)", re.I)
_READ_ONLY = re.compile(r"^\s*(SELECT|USE|LIST|DESCRIBE)\b", re.I)

ALL = None  # quy ước: "không rõ, coi như mọi bảng"


def written_tables(query: str, keyspace: str) -> frozenset[str] | None:
    """Bảng (không kèm keyspace) mà câu CQL ghi. `frozenset()` nếu chỉ đọc hoặc ghi ngoài keyspace này;
    `None` nếu không phân tích được (DDL, BATCH, ...) và phải coi là mọi bảng."""
    q = query.lstrip()
    if _READ_ONLY.match(q):
        return frozenset()
    for pattern in (_INSERT, _UPDATE, _DELETE, _TRUNCATE):
        m = pattern.match(q)
        if m:
            name = m.group(1).replace('"', "").lower()
            if "." in name:
                ks, _, name = name.partition(".")
                if ks != keyspace.lower():
                    return frozenset()
            return frozenset({name})
    return ALL


def _query_of(statement) -> str | None:
    if isinstance(statement, str):
        return statement
    prepared = getattr(statement, "prepared_statement", None)  # BoundStatement
    if prepared is not None:
        return prepared.query_string
    return getattr(statement, "query_string", None)  # SimpleStatement, PreparedStatement


class SeedState:
    def __init__(self, session, keyspace: str, seed_path):
        from tools.seed import seed_statements

        self.session = session
        self.keyspace = keyspace
        self.write_count = 0
        self._lock = threading.Lock()
        self._suspended = False
        self.dirty: set[str] = set(BASE_TABLES)  # trạng thái ban đầu chưa biết: coi mọi bảng là bẩn
        self._seed_by_table: dict[str, list[str]] = defaultdict(list)
        for stmt in seed_statements(seed_path):
            self._seed_by_table[_INSERT.match(stmt).group(1)].append(stmt)
        self._rated_marks: list[tuple] | None = None
        self._snapshot: dict[str, list[str]] | None = None
        self._full = os.environ.get("RIDE_TEST_FULL_RESET") == "1"
        self._verify = os.environ.get("RIDE_TEST_VERIFY_RESET") == "1"
        self._orig_execute_async = session.execute_async
        session.execute_async = self._tracking_execute_async  # chặn mọi đường ghi qua session này

    # -- theo dõi ---------------------------------------------------------
    def _tracking_execute_async(self, query, *args, **kwargs):
        if not self._suspended:
            q = _query_of(query)
            tables = written_tables(q, self.keyspace) if q is not None else ALL
            if tables is None or tables:
                with self._lock:
                    self.write_count += 1
                    self.dirty.update(BASE_TABLES if tables is None else (tables & set(BASE_TABLES)))
        return self._orig_execute_async(query, *args, **kwargs)

    def close(self) -> None:
        self.session.execute_async = self._orig_execute_async

    # -- reset ------------------------------------------------------------
    def reset(self) -> set[str]:
        """Đưa dữ liệu về seed; trả tập bảng đã làm lại."""
        with self._lock:
            todo = set(BASE_TABLES) if (self._full or self._rated_marks is None) else set(self.dirty)
        if todo:
            self._suspended = True
            try:
                try:
                    self._rebuild(todo)
                except BaseException:
                    with self._lock:
                        self.dirty = set(BASE_TABLES)
                    raise
            finally:
                self._suspended = False
            with self._lock:
                self.dirty -= todo
        if self._verify:
            self._verify_snapshot()
        return todo

    def _rebuild(self, todo: set[str]) -> None:
        from cassandra.concurrent import execute_concurrent

        s = self.session
        s.set_keyspace(self.keyspace)
        order = [t for t in BASE_TABLES if t in todo]
        futures = [self._orig_execute_async(f"TRUNCATE {t}", timeout=120) for t in order]  # TRUNCATE song song
        for f in futures:
            f.result()
        seeds = [(stmt, ()) for t in order for stmt in self._seed_by_table.get(t, [])]
        if seeds:
            execute_concurrent(s, seeds, concurrency=50, raise_on_first_error=True)
        if "rides" not in todo:
            return
        if self._rated_marks is None:
            self._rated_marks = self._learn_rated_marks()  # backfill_rated_at thật, một lần cho cả phiên test
            self._snapshot = None
        update = s.prepare("UPDATE rides SET rated_at = ? WHERE ride_id = ?")
        marks = [(rated_at, ride_id) for ride_id, rated_at in self._rated_marks]
        if marks:
            execute_concurrent(s, [(update, m) for m in marks], concurrency=50, raise_on_first_error=True)

    def _learn_rated_marks(self) -> list[tuple]:
        from db.repo import CassandraDb
        from services.rating import backfill_rated_at

        backfill_rated_at(CassandraDb(self.session, self.keyspace))
        rows = self.session.execute("SELECT ride_id, rated_at FROM rides")
        return sorted((r["ride_id"], r["rated_at"]) for r in rows if r["rated_at"] is not None)

    # -- kiểm chứng (RIDE_TEST_VERIFY_RESET=1) ------------------------------
    def _dump(self) -> dict[str, list[str]]:
        out = {}
        for t in BASE_TABLES:
            rows = self._orig_execute_async(f"SELECT * FROM {t}", timeout=60).result()
            out[t] = sorted(repr(sorted(r.items())) for r in rows)
        return out

    def _verify_snapshot(self) -> None:
        now = self._dump()
        if self._snapshot is None:
            self._snapshot = now
            return
        bad = [t for t in BASE_TABLES if now[t] != self._snapshot[t]]
        if bad:
            raise AssertionError(f"Reset theo dõi bảng bẩn để lại dữ liệu khác seed ở: {bad}")
