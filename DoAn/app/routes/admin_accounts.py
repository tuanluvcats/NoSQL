"""Quản trị tài khoản: xem danh sách, khóa/mở khóa."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse

from domain.auth import ADMIN
from routes.deps import flash_trace, get_db, render, require_role, set_flash
from services import accounts

router = APIRouter(prefix="/admin/accounts")


@router.get("")
def accounts_page(request: Request, user: dict = Depends(require_role(ADMIN))):
    rows = accounts.list_accounts(get_db(request))
    return render(request, "admin/accounts.html", {"accounts": rows})


def _toggle(request: Request, username: str, user: dict, active: bool):
    result = accounts.set_account_active(get_db(request), username, active, user["username"],
                                         request.app.state.clock())
    set_flash(request, result.ok, result.message)
    flash_trace(request)
    return RedirectResponse("/admin/accounts", status_code=303)


@router.post("/{username}/lock")
def lock(request: Request, username: str, user: dict = Depends(require_role(ADMIN))):
    return _toggle(request, username, user, False)


@router.post("/{username}/unlock")
def unlock(request: Request, username: str, user: dict = Depends(require_role(ADMIN))):
    return _toggle(request, username, user, True)
