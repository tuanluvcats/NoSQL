"""Ứng dụng FastAPI render phía server cho keyspace ride_booking."""
from __future__ import annotations

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
from routes import admin_accounts, admin_catalog, admin_tools, auth as auth_routes, customer as customer_routes, driver as driver_routes, rides as rides_routes
from routes.deps import AuthRedirect, auth_redirect_handler, optional_user, render


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
    app.state.maintenance = False
    app.state.trace_store = TraceStore(maxlen=100)

    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")

    @app.middleware("http")
    async def _start_trace(request: Request, call_next):
        trace.start_request()
        return await call_next(request)

    app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

    app.add_exception_handler(AuthRedirect, auth_redirect_handler)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        return render(request, "error.html", {"status": exc.status_code, "detail": exc.detail},
                      status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _server_error(request: Request, exc: Exception):
        return render(request, "error.html", {"status": 500, "detail": f"{type(exc).__name__}: {exc}"},
                      status_code=500)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def home(request: Request, user: dict | None = Depends(optional_user)):
        return render(request, "home.html", {})

    app.include_router(auth_routes.router)
    app.include_router(admin_accounts.router)
    app.include_router(admin_catalog.router)
    app.include_router(admin_tools.router)
    app.include_router(customer_routes.router)
    app.include_router(driver_routes.router)
    app.include_router(rides_routes.router)
    return app


app = create_app()
