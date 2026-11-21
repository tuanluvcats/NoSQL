"""Đăng nhập, đăng xuất, đăng ký khách hàng."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse

from routes.deps import flash_trace, get_db, optional_user, render, set_flash
from services import accounts
from services.accounts import RegisterForm

router = APIRouter()

_MSGS = {
    "locked": ("warning", "Tài khoản đã bị khóa hoặc không còn hiệu lực, vui lòng đăng nhập lại."),
    "registered": ("success", "Đăng ký thành công, hãy đăng nhập."),
    "bye": ("info", "Bạn đã đăng xuất."),
}


@router.get("/login")
def login_form(request: Request, msg: str | None = None, user: dict | None = Depends(optional_user)):
    note = _MSGS.get(msg or "")
    return render(request, "login.html", {"note": note, "form_error": None, "username": ""})


@router.post("/login")
def login_submit(request: Request, username: str = Form(""), password: str = Form("")):
    db = get_db(request)
    username = username.strip()
    result = accounts.login(db, username, password, request.app.state.clock())
    if not result.ok:
        status = 403 if result.code == "account_locked" else 401
        return render(request, "login.html", {"note": None, "form_error": result.message, "username": username},
                      status_code=status)
    request.session.clear()  # tránh dùng lại session cũ
    request.session["username"] = result.data["user"]["username"]
    flash_trace(request)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login?msg=bye", status_code=303)


@router.get("/register")
def register_form(request: Request, user: dict | None = Depends(optional_user)):
    return render(request, "register.html", {"form_error": None, "form": {}})


@router.post("/register")
def register_submit(request: Request, username: str = Form(""), password: str = Form(""),
                    full_name: str = Form(""), phone: str = Form(""), email: str = Form(""),
                    address: str = Form("")):
    db = get_db(request)
    form = RegisterForm(username=username.strip(), password=password, full_name=full_name,
                        phone=phone.strip(), email=email.strip(), address=address)
    result = accounts.register_customer(db, form, request.app.state.clock())
    if not result.ok:
        status = 409 if result.code == "username_taken" else 400
        keep = {"username": form.username, "full_name": full_name, "phone": form.phone,
                "email": form.email, "address": address}
        return render(request, "register.html", {"form_error": result.message, "form": keep}, status_code=status)
    if result.code == "partial":
        set_flash(request, True, result.message)
    flash_trace(request)
    return RedirectResponse("/login?msg=registered", status_code=303)
