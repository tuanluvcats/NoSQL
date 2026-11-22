"""Trang Kết nối (mục 8, công khai) và trang NoSQL minh họa (cần đăng nhập)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse

from db.catalog import STATEMENTS
from domain.write_matrix import WRITE_MATRIX
from routes.deps import TECH_COOKIE, current_user, get_db, render, safe_user
from services.system_info import MISSING_PK_CQL, collections_demo, connection_info, missing_pk_demo

router = APIRouter()


@router.get("/connection")
def connection_page(request: Request):
    safe_user(request)  # trang công khai: không được 503/redirect chỉ vì không có DB
    info = connection_info(getattr(request.app.state, "db", None), request.app.state.settings)
    if info["error"] and getattr(request.app.state, "db_error", None):
        info["error"] = request.app.state.db_error
    return render(request, "connection.html", {"info": info})


def _nosql_page(request: Request, missing_pk: dict | None = None):
    db = get_db(request)
    catalog = [{"code": s.code, "q": s.q, "table": s.table, "kind": s.kind, "cql": s.cql, "name": s.name,
                "pk": ", ".join(c for c, _ in s.pk) or ("(quét toàn bảng)" if s.kind == "scan" else "-")}
               for s in STATEMENTS.values()]
    ctx = {"catalog": catalog, "matrix_rows": WRITE_MATRIX, "demo": collections_demo(db),
           "missing_pk": missing_pk, "missing_pk_cql": MISSING_PK_CQL}
    return render(request, "nosql.html", ctx)


@router.get("/nosql")
def nosql_page(request: Request, user: dict = Depends(current_user)):
    return _nosql_page(request)


@router.post("/nosql/missing-pk")
def nosql_missing_pk(request: Request, user: dict = Depends(current_user)):
    message = missing_pk_demo(get_db(request))
    return _nosql_page(request, {"message": message})


def _safe_next(target: str) -> str:
    """Chống open redirect: chỉ nhận đường dẫn nội bộ, không nhận hai dấu gạch chéo đầu hay gạch chéo rồi gạch ngược."""
    if target.startswith("/") and not target.startswith("//") and not target.startswith("/\\"):
        return target
    return "/"


@router.post("/tech-mode")
def set_tech_mode(on: str = Form("0"), next: str = Form("/")):
    """Bật/tắt chế độ kỹ thuật bằng cookie (không cần đăng nhập, không đổi quyền hay dữ liệu)."""
    response = RedirectResponse(_safe_next(next), status_code=303)
    response.set_cookie(TECH_COOKIE, "1" if on == "1" else "0", max_age=30 * 24 * 3600, httponly=True, samesite="lax")
    return response
