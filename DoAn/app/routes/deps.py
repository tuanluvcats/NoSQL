"""Hàm dùng chung của các route: render có sẵn panel trace, lưu trace qua redirect (PRG)."""
from __future__ import annotations

from fastapi import HTTPException, Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from config import APP_DIR
from db import trace
from db.trace import fmt_param
from domain.auth import effective_role
from domain.write_matrix import EVENT_LABELS, WRITE_MATRIX
from services.accounts import load_active_user

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
templates.env.globals["event_labels"] = EVENT_LABELS
templates.env.filters["cql"] = fmt_param  # tham số CQL hiển thị theo cú pháp CQL, không theo repr của Python


def get_db(request: Request):
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Chưa kết nối được Cassandra")
    return db


class AuthRedirect(Exception):
    """Chưa đăng nhập hoặc tài khoản vừa bị khóa: main.py đổi thành redirect 303."""

    def __init__(self, location: str):
        self.location = location


def auth_redirect_handler(request: Request, exc: AuthRedirect):
    return RedirectResponse(exc.location, status_code=303)


def optional_user(request: Request) -> dict | None:
    """Người dùng hiện tại, nạp lại từ Cassandra ở MỌI request (khóa tài khoản có hiệu lực ngay)."""
    if hasattr(request.state, "user_loaded"):
        return request.state.user
    username = request.session.get("username")
    user = None
    if username:
        user = load_active_user(get_db(request), username)
        if user is None:
            request.session.clear()
            raise AuthRedirect("/login?msg=locked")
    request.state.user = user
    request.state.user_loaded = True
    return user


def safe_user(request: Request) -> dict | None:
    """Người dùng hiện tại cho trang lỗi và trang công khai: KHÔNG bao giờ ném lỗi.

    Dùng lại kết quả nếu route đã nạp. Nếu chưa (route lỗi trước khi chạy dependency, 404, 500) thì lấy tên đăng nhập từ
    phiên rồi nạp lại từ Cassandra; tài khoản bị khóa, không có DB hoặc DB lỗi đều coi như khách và không lộ chi tiết lỗi."""
    if getattr(request.state, "user_loaded", False):
        return request.state.user
    username = _session(request).get("username")
    user = None
    db = getattr(request.app.state, "db", None)
    if username and db is not None:
        try:
            user = load_active_user(db, username)
        except Exception:  # noqa: BLE001 - trang lỗi không được sập hay lộ lỗi DB chỉ vì tra cứu người dùng
            user = None
    request.state.user = user
    request.state.user_loaded = True
    return user


def current_user(request: Request) -> dict:
    user = optional_user(request)
    if user is None:
        raise AuthRedirect("/login")
    return user


def require_role(*roles: str):
    """Dependency: chỉ cho vai trò hiệu lực (ADMIN/CUSTOMER/DRIVER) nằm trong roles. Khách thì về /login, sai vai trò thì 403."""

    def dep(request: Request) -> dict:
        user = current_user(request)
        if effective_role(user.get("role")) not in roles:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập trang này.")
        return user

    return dep


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


def set_flash(request: Request, ok: bool, message: str) -> None:
    request.session["flash"] = {"ok": ok, "message": message}


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
    ctx.setdefault("user", getattr(request.state, "user", None))
    ctx.setdefault("flash", session.pop("flash", None) if session else None)
    ctx.setdefault("maintenance", bool(getattr(getattr(request.app.state, "maintenance", None), "active", False)))
    ctx.setdefault("db_error", getattr(request.app.state, "db_error", None))
    ctx["event"] = event
    ctx["written"] = trace.tables_written(entries)
    if last_trace is not None and event:
        # trang sau redirect (PRG): ma trận ghi áp cho thao tác POST vừa rồi, không áp cho các lệnh đọc của trang này
        ctx["last_written"] = trace.tables_written(last_trace)
        ctx["last_matrix"] = matrix_check(last_trace, event)
        ctx["matrix"] = None
    else:
        ctx["matrix"] = matrix_check(entries, event)
    return templates.TemplateResponse(request, template, ctx, status_code=status_code)


def flash_trace(request: Request, event: str | None = None) -> None:
    """Giữ trace của request POST hiện tại để trang sau redirect hiển thị 'CQL của thao tác vừa rồi'.

    `event` (khóa của WRITE_MATRIX) cho trang sau biết áp ma trận ghi nào; trang đó lấy bằng `pop_trace_event`."""
    entries = trace.current()
    store = request.app.state.trace_store
    if entries:
        request.session["trace_token"] = store.put(entries)
        if event:
            request.session["trace_event"] = event
        else:
            request.session.pop("trace_event", None)


def pop_trace_event(request: Request) -> str | None:
    """Sự kiện của thao tác POST vừa rồi (chỉ có khi còn trace_token tương ứng)."""
    session = _session(request)
    event = session.pop("trace_event", None) if session else None
    return event if session and "trace_token" in session else None
