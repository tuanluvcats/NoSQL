"""Hàm dùng chung của các route: render có sẵn panel trace, lưu trace qua redirect (PRG)."""
from __future__ import annotations

from fastapi import HTTPException, Request
from starlette.templating import Jinja2Templates

from config import APP_DIR
from db import trace
from domain.write_matrix import WRITE_MATRIX

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def get_db(request: Request):
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Chưa kết nối được Cassandra")
    return db


def matrix_check(entries, event: str | None) -> dict | None:
    """So bảng đã ghi thật với WRITE_MATRIX[event] (required phải đủ, optional chỉ để thông tin)."""
    if not event or event not in WRITE_MATRIX:
        return None
    written = trace.tables_written(entries)
    spec = WRITE_MATRIX[event]
    required = [(t, t in written) for t in spec["required"]]
    optional = [(t, t in written) for t in spec["optional"]]
    return {
        "event": event,
        "required": required,
        "optional": optional,
        "missing": [t for t, ok in required if not ok],
        "complete": all(ok for _, ok in required),
    }


def _session(request: Request) -> dict:
    return request.scope.get("session") or {}


def render(request: Request, template: str, ctx: dict | None = None, status_code: int = 200):
    ctx = dict(ctx or {})
    entries = trace.current()
    event = ctx.get("event")
    session = _session(request)
    store = getattr(request.app.state, "trace_store", None)
    token = session.pop("trace_token", None) if session else None
    last_trace = store.pop(token) if store is not None else None
    ctx.setdefault("trace", entries)
    ctx.setdefault("last_trace", last_trace)
    ctx.setdefault("user", session.get("user"))
    ctx.setdefault("maintenance", bool(getattr(request.app.state, "maintenance", False)))
    ctx.setdefault("db_error", getattr(request.app.state, "db_error", None))
    ctx["event"] = event
    ctx["written"] = trace.tables_written(entries)
    ctx["matrix"] = matrix_check(entries, event)
    return templates.TemplateResponse(request, template, ctx, status_code=status_code)


def flash_trace(request: Request) -> None:
    """Giữ trace của request POST hiện tại để trang sau redirect hiển thị 'CQL của thao tác vừa rồi'."""
    entries = trace.current()
    store = request.app.state.trace_store
    if entries:
        request.session["trace_token"] = store.put(entries)
