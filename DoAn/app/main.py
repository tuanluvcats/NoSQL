"""Ứng dụng FastAPI render phía server cho keyspace ride_booking."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from config import APP_DIR, Settings
from db import session as db_session
from db import trace
from db.repo import CassandraDb
from db.trace import TraceStore
from domain.tz import now_vn
from routes import admin_accounts, admin_backup, admin_catalog, admin_tools, auth as auth_routes, customer as customer_routes, driver as driver_routes, rides as rides_routes, reports as reports_routes, system as system_routes
from routes.deps import AuthRedirect, auth_redirect_handler, optional_user, render, safe_user
from services.maintenance import MaintenanceState
from services.system_info import cassandra_version

RESTORE_PATH = "/admin/backup/restore"
logger = logging.getLogger("ride_booking")


def create_app(settings: Settings | None = None, db=None, clock=None) -> FastAPI:
    settings = settings or Settings.from_env()
    injected_db = db

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cluster = None
        if injected_db is None:
            try:
                cluster, session = db_session.connect(settings, settings.keyspace)
                app.state.db = CassandraDb(session, settings.keyspace)
                app.state.db_error = None
            except Exception as e:  # noqa: BLE001 - hiện banner thay vì sập ứng dụng
                app.state.db = None
                app.state.db_error = f"{type(e).__name__}: {e}"
        try:
            yield
        finally:
            if cluster is not None:
                cluster.shutdown()

    app = FastAPI(title="Đặt xe công nghệ - Cassandra", lifespan=lifespan)
    app.state.settings = settings
    app.state.clock = clock or now_vn
    app.state.db = injected_db
    app.state.db_error = None
    app.state.maintenance = MaintenanceState()
    app.state.trace_store = TraceStore(maxlen=100)

    @app.middleware("http")
    async def _start_trace(request: Request, call_next):
        trace.start_request()
        # chế độ bảo trì (đang restore): chặn mọi ghi, trừ chính lệnh restore (tự kiểm cờ bằng state.begin())
        if (app.state.maintenance.active and request.method not in ("GET", "HEAD", "OPTIONS")
                and request.url.path != RESTORE_PATH):
            safe_user(request)  # menu của trang 503 hiện đúng người dùng (SessionMiddleware được thêm sau nên chạy trước)
            return render(request, "error.html", {"status": 503, "detail": "Đang khôi phục dữ liệu, vui lòng thử lại sau ít phút."},
                          status_code=503)
        return await call_next(request)

    # thêm SAU middleware trên để phiên được nạp trước nó (request.scope["session"] có sẵn cho trang 503)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")

    app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

    app.add_exception_handler(AuthRedirect, auth_redirect_handler)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        safe_user(request)  # menu của trang lỗi hiện đúng người dùng đã đăng nhập
        return render(request, "error.html", {"status": exc.status_code, "detail": exc.detail},
                      status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _server_error(request: Request, exc: Exception):
        logger.error("Lỗi 500 tại %s %s", request.method, request.url.path, exc_info=(type(exc), exc, exc.__traceback__))
        safe_user(request)
        # chống lộ chuỗi lỗi DB/đường dẫn: chỉ hiện chi tiết khi APP_DEBUG=1, còn lại đã có đầy đủ trong log của server
        detail = (f"{type(exc).__name__}: {exc}" if settings.debug
                  else "Đã xảy ra lỗi hệ thống. Chi tiết đã được ghi vào log của máy chủ.")
        return render(request, "error.html", {"status": 500, "detail": detail}, status_code=500)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def home(request: Request, user: dict | None = Depends(optional_user)):
        version = cassandra_version(getattr(request.app.state, "db", None))
        return render(request, "home.html", {"keyspace": settings.keyspace, "cassandra_version": version})

    app.include_router(auth_routes.router)
    app.include_router(admin_accounts.router)
    app.include_router(admin_catalog.router)
    app.include_router(admin_tools.router)
    app.include_router(admin_backup.router)
    app.include_router(customer_routes.router)
    app.include_router(driver_routes.router)
    app.include_router(rides_routes.router)
    app.include_router(reports_routes.router)
    app.include_router(system_routes.router)
    return app


app = create_app()
