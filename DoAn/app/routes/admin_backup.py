"""Backup/restore JSON logical (9.2). Chỉ ADMIN/OPERATOR. Không có nút nodetool snapshot.

Restore: service tự bật chế độ bảo trì (middleware chặn mọi POST khác) và luôn tắt khi xong hoặc lỗi."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse

from domain.auth import ADMIN
from routes.deps import flash_trace, get_db, render, require_role, set_flash
from services import backup

router = APIRouter(prefix="/admin/backup")
_ADMIN = Depends(require_role(ADMIN))


def _dest(request: Request):
    return request.app.state.settings.backup_dir


def _done(request: Request, ok: bool, message: str):
    set_flash(request, ok, message)
    flash_trace(request)
    return RedirectResponse("/admin/backup", status_code=303)


@router.get("")
def backup_page(request: Request, user: dict = _ADMIN):
    db = get_db(request)
    return render(request, "admin/backup.html", {
        "files": backup.list_backups(_dest(request)),
        "counts": backup.table_counts(db),
        "base_tables": backup.BASE_TABLES,
        "backup_dir": str(_dest(request)),
    })


@router.post("/create")
def create(request: Request, label: str = Form(""), user: dict = _ADMIN):
    label = (label or "").strip().lower()
    try:
        path = backup.create_backup(get_db(request), _dest(request), request.app.state.clock(), label)
    except ValueError as e:
        return _done(request, False, str(e))
    return _done(request, True, f"Đã tạo backup {path.name}.")


@router.post("/restore")
def restore(request: Request, name: str = Form(""), user: dict = _ADMIN):
    result = backup.restore_backup(get_db(request), _dest(request), (name or "").strip(),
                                   request.app.state.maintenance, request.app.state.clock())
    return _done(request, result.ok, result.message)
