"""Tài khoản: đăng nhập, đăng ký (LWT), khóa/mở khóa. Không bao giờ trả password_hash ra ngoài."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from config import AREAS
from domain import auth
from domain.ids import new_customer_id
from domain.passwords import hash_password, verify_password
from services.result import ActionResult

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,32}$")
PHONE_RE = re.compile(r"^0\d{9}$")
MIN_PASSWORD_LEN = 6
BAD_CREDENTIALS_MSG = "Sai tên đăng nhập hoặc mật khẩu."
# Băm giả để thời gian xử lý của "không có tài khoản" gần giống "sai mật khẩu".
_DUMMY_HASH = "pbkdf2_sha256$100000$0000000000000000$" + "0" * 64


@dataclass
class RegisterForm:
    username: str
    password: str
    full_name: str
    phone: str
    email: str
    address: str = ""


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "password_hash"}


def _validate(form: RegisterForm) -> str | None:
    if not USERNAME_RE.match(form.username or ""):
        return "Tên đăng nhập gồm 3-32 ký tự: chữ thường không dấu, số hoặc dấu gạch dưới."
    if len(form.password or "") < MIN_PASSWORD_LEN:
        return f"Mật khẩu phải dài ít nhất {MIN_PASSWORD_LEN} ký tự."
    if not (form.full_name or "").strip():
        return "Họ tên không được để trống."
    if not PHONE_RE.match(form.phone or ""):
        return "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."
    if "@" not in (form.email or ""):
        return "Email không hợp lệ."
    return None


def register_customer(db, form: RegisterForm, now: datetime) -> ActionResult:
    """T01 (LWT user_accounts) trước, B18 (customers) sau. Mật khẩu băm pbkdf2."""
    err = _validate(form)
    if err:
        return ActionResult(False, "invalid_input", err)
    customer_id = new_customer_id(now)
    res = db.lwt("T01_account_insert", [form.username, hash_password(form.password), "CUSTOMER",
                                        customer_id, form.full_name.strip(), now])
    if not res.applied:
        return ActionResult(False, "username_taken", "Tên đăng nhập đã được dùng.",
                            current=_public(res.current or {}) or None)
    try:
        c = db.lwt("B18_customer_insert", [customer_id, form.full_name.strip(), form.phone, form.email.strip(),
                                           (form.address or "").strip() or None, now])
        applied = c.applied
    except Exception as e:  # noqa: BLE001 - D10: không rollback, báo partial
        return ActionResult(True, "partial", f"Đã tạo tài khoản nhưng ghi hồ sơ khách lỗi ({type(e).__name__}). "
                            "Hãy dùng Kiểm tra nhất quán.", data={"customer_id": customer_id})
    if not applied:
        return ActionResult(True, "partial", "Đã tạo tài khoản nhưng mã khách bị trùng, hồ sơ chưa được ghi.",
                            data={"customer_id": customer_id})
    return ActionResult(True, "ok", "Đăng ký thành công.", data={"customer_id": customer_id})


def login(db, username: str, password: str, now: datetime) -> ActionResult:
    row = db.one("B01_account_get", [username])
    if row is None:
        verify_password(password or "", _DUMMY_HASH)
        return ActionResult(False, "bad_credentials", BAD_CREDENTIALS_MSG)
    if not verify_password(password or "", row.get("password_hash")) or auth.effective_role(row.get("role")) is None:
        return ActionResult(False, "bad_credentials", BAD_CREDENTIALS_MSG)
    if not row.get("is_active"):
        return ActionResult(False, "account_locked", "Tài khoản đã bị khóa.")
    db.exec("T02_login_touch", [now, username])
    return ActionResult(True, "ok", "Đăng nhập thành công.", data={"user": _public(row)})


def load_active_user(db, username: str) -> dict | None:
    """Gọi ở MỌI request: tài khoản bị khóa/xóa/sai vai trò thì coi như chưa đăng nhập."""
    row = db.one("B01_account_get", [username])
    if row is None or not row.get("is_active") or auth.effective_role(row.get("role")) is None:
        return None
    return _public(row)


def list_accounts(db) -> list[dict]:
    return sorted((_public(r) for r in db.rows("APP01_accounts_scan")), key=lambda r: r["username"])


def count_active_admins(db) -> int:
    return sum(1 for r in db.rows("APP01_accounts_scan")
               if auth.effective_role(r.get("role")) == auth.ADMIN and r.get("is_active"))


def set_account_active(db, target: str, active: bool, actor: str, now: datetime) -> ActionResult:
    if active:
        res = db.lwt("T02_account_unlock", [target])
        if res.applied:
            return ActionResult(True, "ok", f"Đã mở khóa tài khoản {target}.")
        if (res.current or {}).get("is_active") is None:
            return ActionResult(False, "not_found", "Không tìm thấy tài khoản.")
        return ActionResult(True, "duplicate_ok", f"Tài khoản {target} đã được mở khóa từ trước.", current=res.current)

    row = db.one("B01_account_get", [target])
    if row is None:
        return ActionResult(False, "not_found", "Không tìm thấy tài khoản.")
    is_admin = auth.effective_role(row.get("role")) == auth.ADMIN
    admin_count = count_active_admins(db) if is_admin and row.get("is_active") else 0
    refusal = auth.lock_refusal(row, actor, admin_count)
    if refusal == "self_lock":
        return ActionResult(False, "self_lock", "Không thể tự khóa chính mình.")
    if refusal == "last_admin":
        return ActionResult(False, "last_admin", "Không thể khóa quản trị viên đang hoạt động cuối cùng.")

    is_driver = row.get("role") == "DRIVER"
    driver_id = row.get("ref_id")
    if is_driver and driver_id:
        off = db.lwt("APP09_driver_offline", [driver_id])
        if not off.applied and (off.current or {}).get("status") == "BUSY":
            return ActionResult(False, "driver_busy", "Tài xế đang có chuyến (BUSY), chưa thể khóa.",
                                current=off.current)
    res = db.lwt("T02_account_lock", [target])
    if is_driver and driver_id:
        for city, districts in AREAS.items():
            for district in districts:
                db.exec("T05_area_delete", [city, district, driver_id])
    if not res.applied:
        return ActionResult(True, "duplicate_ok", f"Tài khoản {target} đã bị khóa từ trước.", current=res.current)
    return ActionResult(True, "ok", f"Đã khóa tài khoản {target}.")
