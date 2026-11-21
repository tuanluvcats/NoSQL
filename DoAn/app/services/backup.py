"""Backup/restore JSON logical (9.2). Không dùng nodetool snapshot, không cần cqlsh.

Backup: SELECT JSON từng bảng THẬT (13 bảng, không MV) vào một file JSON kèm kiểu cột theo system_schema.columns.
Restore (Nhánh A của Task 1, vì TRUNCATE bảng gốc làm rỗng cả MV trên 3.11.4):
  1. kiểm TOÀN BỘ file (phiên bản, đủ 13 bảng, cột/kiểu khớp schema hiện tại, kiểu giá trị, số dòng) TRƯỚC mọi TRUNCATE;
  2. bật chế độ bảo trì (main.py chặn mọi POST khác), luôn tắt khi xong hoặc lỗi;
  3. tạo bản an toàn `*_prerestore.json` của dữ liệu hiện tại, TRUNCATE 13 bảng, INSERT ... JSON lại.
  Không ghi trực tiếp vào MV: MV tự có lại từ `vehicles`.
Backup đọc từng bảng riêng, không phải ảnh chụp nhất quán giữa các bảng: nên backup khi ít người ghi."""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from cassandra.concurrent import execute_concurrent

from config import BASE_TABLES
from db import capabilities, trace
from domain.tz import to_vn
from services.maintenance import MaintenanceState
from services.result import ActionResult

BACKUP_FORMAT = "ride_booking_json_v1"
BACKUP_NAME_RE = r"^[a-z0-9_]+_\d{8}_\d{6}(_[a-z]+)?\.json$"
_LABEL_RE = re.compile(r"[a-z]{1,20}")
_STAMP_RE = re.compile(r"_(\d{8}_\d{6})(?:_[a-z]+)?\.json$")
_COUNT_TABLES = BASE_TABLES + ("vehicles_by_plate",)
_MAX_CELL_ERRORS_PER_TABLE = 5

_TEXT_TYPES = {"text", "varchar", "ascii", "timestamp", "date", "time", "uuid", "timeuuid", "inet", "blob"}
_NUM_TYPES = {"double", "float", "decimal", "varint"}
_INT_TYPES = {"int", "bigint", "smallint", "tinyint", "counter"}


# ------------------------------------------------------------------ schema, đếm
def _norm_type(t: str) -> str:
    return re.sub(r"\s+", "", str(t))


def current_schema(db) -> dict[str, dict[str, str]]:
    """{bảng: {cột: kiểu}} của 13 bảng thật trong keyspace hiện tại (bỏ MV)."""
    out: dict[str, dict[str, str]] = {}
    for r in db.rows("SYS_columns", [db.keyspace]):
        if r["table_name"] in BASE_TABLES:
            out.setdefault(r["table_name"], {})[r["column_name"]] = r["type"]
    return out


def _count(db, table: str) -> int:
    if table not in _COUNT_TABLES:  # tên bảng chỉ lấy từ whitelist, không bao giờ từ người dùng
        raise ValueError(f"Bảng không hợp lệ: {table}")
    rows = db.raw("BK_count", table, f"SELECT COUNT(*) AS n FROM {table}")
    return int(rows[0]["n"]) if rows else 0


def table_counts(db) -> dict[str, int]:
    return {t: _count(db, t) for t in _COUNT_TABLES}


# ------------------------------------------------------------------ tên file, thư mục
def resolve_backup(dest_dir: Path, name: str) -> Path:
    """Đường dẫn file backup trong dest_dir. Tên sai mẫu hoặc trỏ ra ngoài thư mục thì ValueError (chống path traversal)."""
    if not isinstance(name, str) or not re.fullmatch(BACKUP_NAME_RE, name):
        raise ValueError("Tên file backup không hợp lệ.")
    base = Path(dest_dir).resolve()
    path = (base / name).resolve()
    if path.parent != base:
        raise ValueError("File backup nằm ngoài thư mục backup.")
    return path


def list_backups(dest_dir: Path) -> list[str]:
    """Tên file backup hợp lệ trong thư mục, mới nhất trước."""
    d = Path(dest_dir)
    if not d.is_dir():
        return []
    names = [p.name for p in d.iterdir() if p.is_file() and re.fullmatch(BACKUP_NAME_RE, p.name)]
    return sorted(names, key=lambda n: ((_STAMP_RE.search(n) or [None, ""])[1], n), reverse=True)


def load_backup(path: Path) -> dict:
    """Đọc file backup; nội dung không phải JSON thì ValueError."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ kiểm file
def _cell_ok(value, col_type: str) -> bool:
    if value is None:
        return True
    base = _norm_type(col_type)
    if base.startswith("frozen<") and base.endswith(">"):
        base = base[len("frozen<"):-1]
    head = base.split("<", 1)[0]
    if head in _TEXT_TYPES:
        return isinstance(value, str)
    if head == "boolean":
        return isinstance(value, bool)
    if head in _INT_TYPES:
        return isinstance(value, int) and not isinstance(value, bool)
    if head in _NUM_TYPES:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if head in ("set", "list"):
        return isinstance(value, list)
    if head == "map":
        return isinstance(value, dict)
    return True  # kiểu lạ (tuple, UDT...): để Cassandra tự kiểm


def validate_backup(data, schema: dict[str, dict[str, str]]) -> list[str]:
    """Danh sách lỗi (rỗng nếu hợp lệ). Phải chạy xong và rỗng TRƯỚC mọi TRUNCATE."""
    if not isinstance(data, dict):
        return ["File không phải đối tượng JSON."]
    errors: list[str] = []
    if data.get("format") != BACKUP_FORMAT:
        errors.append(f"format sai: cần '{BACKUP_FORMAT}', file có {data.get('format')!r}.")
    tables = data.get("tables")
    counts = data.get("counts")
    if not isinstance(tables, dict):
        return errors + ["Thiếu mục 'tables'."]
    if not isinstance(counts, dict):
        errors.append("Thiếu mục 'counts'.")
        counts = {}
    for t in BASE_TABLES:
        if t not in tables:
            errors.append(f"Thiếu bảng '{t}' trong file.")
    for t in tables:
        if t not in BASE_TABLES:
            errors.append(f"Bảng '{t}' không thuộc schema ứng dụng (13 bảng thật, không có MV).")
    for t in BASE_TABLES:
        entry = tables.get(t)
        if entry is None:
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("columns"), dict) \
                or not isinstance(entry.get("rows"), list):
            errors.append(f"Bảng '{t}': cần có 'columns' (đối tượng) và 'rows' (danh sách).")
            continue
        cols: dict = entry["columns"]
        live = schema.get(t, {})
        for c, ty in cols.items():
            if c not in live:
                errors.append(f"Bảng '{t}': cột '{c}' không có trong schema hiện tại.")
            elif _norm_type(ty) != _norm_type(live[c]):
                errors.append(f"Bảng '{t}': cột '{c}' kiểu '{ty}' khác schema hiện tại '{live[c]}'.")
        rows = entry["rows"]
        if counts.get(t) != len(rows):
            errors.append(f"Bảng '{t}': counts={counts.get(t)!r} nhưng có {len(rows)} dòng.")
        cell_errors = 0
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"Bảng '{t}': dòng {i} không phải đối tượng.")
                continue
            for k, v in row.items():
                if k not in cols:
                    errors.append(f"Bảng '{t}': dòng {i} có khóa '{k}' ngoài danh sách cột của file.")
                elif k in live and not _cell_ok(v, live[k]):
                    cell_errors += 1
                    if cell_errors <= _MAX_CELL_ERRORS_PER_TABLE:
                        errors.append(f"Bảng '{t}': dòng {i}, cột '{k}' kiểu {live[k]} nhưng giá trị là {v!r}.")
        if cell_errors > _MAX_CELL_ERRORS_PER_TABLE:
            errors.append(f"Bảng '{t}': tổng cộng {cell_errors} giá trị sai kiểu.")
    return errors


# ------------------------------------------------------------------ tạo backup
def create_backup(db, dest_dir: Path, now: datetime, label: str = "") -> Path:
    """Ghi `<keyspace>_<yyyymmdd>_<HHMMSS>[_label].json` (giờ +07) vào dest_dir; không ghi đè file có sẵn."""
    if label and not _LABEL_RE.fullmatch(label):
        raise ValueError("Nhãn backup chỉ gồm chữ thường a-z (tối đa 20 ký tự).")
    vn = to_vn(now)
    schema = current_schema(db)
    tables: dict[str, dict] = {}
    for t in BASE_TABLES:
        rows = db.raw("BK_export", t, f"SELECT JSON * FROM {t}", kind="read")
        tables[t] = {"columns": dict(schema.get(t, {})), "rows": [json.loads(r["[json]"]) for r in rows]}
    release = db.one("SYS_local")
    data = {
        "format": BACKUP_FORMAT,
        "keyspace": db.keyspace,
        "created_at": vn.isoformat(timespec="seconds"),
        "release_version": (release or {}).get("release_version"),
        "tables": tables,
        "counts": {t: len(v["rows"]) for t, v in tables.items()},
    }
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = vn.strftime("%Y%m%d_%H%M%S")
        path = dest / f"{db.keyspace}_{stamp}{'_' + label if label else ''}.json"
        if not path.exists():
            break
        vn += timedelta(seconds=1)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path


# ------------------------------------------------------------------ restore
def _insert_rows(db, table: str, rows: list[dict]) -> None:
    """INSERT INTO <table> JSON ? cho từng dòng. Với CassandraDb: chạy song song và để lại MỘT dòng trace mỗi bảng."""
    if not rows:
        return
    payloads = [json.dumps(r, ensure_ascii=False) for r in rows]
    session = getattr(db, "session", None)
    if session is None:  # Db khác (không có session): từng dòng qua db.raw
        for p in payloads:
            db.raw("BK_insert", table, f"INSERT INTO {table} JSON ?", [p], kind="write")
        return
    cql = f"INSERT INTO {table} JSON ?"
    entry = trace.TraceEntry(
        name="BK_insert", code="BK", q="", table=table, cql=f"{cql}   -- {len(rows)} dòng", params=[],
        partition_key={}, consistency=getattr(db, "consistency_name", "LOCAL_QUORUM"), kind="write",
        applied=None, current=None, row_count=len(rows), elapsed_ms=0.0, error=None)
    t0 = time.perf_counter()
    try:
        prepared = session.prepare(cql)
        execute_concurrent(session, [(prepared, (p,)) for p in payloads], concurrency=50, raise_on_first_error=True)
    except BaseException as e:
        entry.error = f"{type(e).__name__}: {e}"
        raise
    finally:
        entry.elapsed_ms = (time.perf_counter() - t0) * 1000
        trace.record(entry)


def _wait_view_matches_base(db, timeout: float = 10.0) -> None:
    """MV tự cập nhật sau INSERT vào vehicles; chờ ngắn cho số dòng MV bằng vehicles."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if _count(db, "vehicles_by_plate") == _count(db, "vehicles"):
            return
        time.sleep(0.2)


def _fail(code: str, message: str, **data) -> ActionResult:
    return ActionResult(False, code, message, data=data)


def restore_backup(db, dest_dir: Path, name: str, state: MaintenanceState, now: datetime) -> ActionResult:
    if not state.begin():
        return _fail("maintenance", "Đang có một thao tác khôi phục khác, hệ thống đang ở chế độ bảo trì.")
    try:  # từ đây trở đi LUÔN state.end() ở finally
        try:
            path = resolve_backup(dest_dir, name)
        except ValueError as e:
            return _fail("backup_invalid", f"Không dùng được tên file: {e}", errors=[str(e)])
        if not path.is_file():
            return _fail("not_found", f"Không tìm thấy file backup '{name}'.")
        try:
            data = load_backup(path)
        except (ValueError, OSError) as e:
            return _fail("backup_invalid", f"Không đọc được file backup: {e}", errors=[str(e)])
        errors = validate_backup(data, current_schema(db))
        if errors:  # TRƯỚC mọi TRUNCATE: dữ liệu hiện tại còn nguyên
            head = "; ".join(errors[:3]) + (f" (và {len(errors) - 3} lỗi khác)" if len(errors) > 3 else "")
            return _fail("backup_invalid", f"File backup không hợp lệ, chưa thay đổi gì: {head}", errors=errors)
        if not capabilities.TRUNCATE_CLEARS_MV:
            raise RuntimeError("Nhánh B (DROP/CREATE MV) chưa được cài đặt; TRUNCATE_CLEARS_MV=False.")

        before = table_counts(db)
        safety = create_backup(db, dest_dir, now, "prerestore")  # lưới an toàn nếu INSERT lỗi giữa chừng
        phase, table = "TRUNCATE", ""
        try:
            for table in BASE_TABLES:
                db.raw("BK_truncate", table, f"TRUNCATE {table}", kind="write")
            phase = "INSERT"
            for table in BASE_TABLES:
                _insert_rows(db, table, data["tables"][table]["rows"])
            _wait_view_matches_base(db)
        except Exception as e:  # noqa: BLE001 - dữ liệu đã bị TRUNCATE: báo rõ và chỉ cách khôi phục
            return ActionResult(
                False, "partial",
                f"Khôi phục lỗi khi {phase} bảng {table}: {type(e).__name__}: {e}. Dữ liệu hiện tại có thể thiếu "
                f"hoặc rỗng. Hãy khôi phục lại từ bản an toàn {safety.name}.",
                data={"counts_before": before, "safety_backup": safety.name, "failed_table": table,
                      "phase": phase, "error": f"{type(e).__name__}: {e}"})
        after = table_counts(db)
        return ActionResult(True, "ok", f"Đã khôi phục {sum(after[t] for t in BASE_TABLES)} dòng của {len(BASE_TABLES)} "
                            f"bảng từ {path.name}. Bản an toàn trước khi khôi phục: {safety.name}.",
                            data={"counts_before": before, "counts_after": after, "safety_backup": safety.name})
    finally:
        state.end()
