import pytest

from domain.tz import parse_vn
from services import accounts
from services.accounts import RegisterForm
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.auth

NOW = parse_vn("2026-11-21 09:00:00")


def _form(username="cust016", **kw):
    base = dict(username=username, password="matkhau1", full_name="Nguyễn Văn Mười Sáu",
                phone="0912345678", email="a@b.vn", address="1 Lê Lợi")
    base.update(kw)
    return RegisterForm(**base)


# ---------------- service trên Cassandra thật ----------------
def test_login_sets_last_login_at(db):
    assert accounts.login(db, "cust001", "123456", NOW).ok
    assert db.one("B01_account_get", ["cust001"])["last_login_at"] is not None


def test_login_bad_password_and_unknown_user(db):
    assert accounts.login(db, "cust001", "sai", NOW).code == "bad_credentials"
    assert accounts.login(db, "khong_ton_tai", "123456", NOW).code == "bad_credentials"
    assert db.one("B01_account_get", ["cust001"])["last_login_at"] is None


def test_register_customer_writes_account_and_customer_and_duplicate_is_rejected(db):
    r = accounts.register_customer(db, _form(), NOW)
    assert r.ok
    acc = db.one("B01_account_get", ["cust016"])
    assert acc["role"] == "CUSTOMER" and acc["ref_id"].startswith("CUST_")
    assert acc["ref_id"] == r.data["customer_id"]
    assert db.one("B02_customer_get", [acc["ref_id"]]) is not None
    assert accounts.login(db, "cust016", "matkhau1", NOW).ok  # mật khẩu pbkdf2 đăng nhập được
    again = accounts.register_customer(db, _form(), NOW)
    assert again.code == "username_taken" and again.current["username"] == "cust016"
    assert "password_hash" not in again.current


def test_lock_and_unlock_account(db):
    accounts.register_customer(db, _form(), NOW)
    assert accounts.set_account_active(db, "cust016", False, "admin", NOW).ok
    assert accounts.login(db, "cust016", "matkhau1", NOW).code == "account_locked"
    assert accounts.load_active_user(db, "cust016") is None
    assert accounts.set_account_active(db, "cust016", True, "admin", NOW).ok
    assert accounts.login(db, "cust016", "matkhau1", NOW).ok


def test_self_lock_refused(db):
    assert accounts.set_account_active(db, "admin", False, "admin", NOW).code == "self_lock"
    assert db.one("B01_account_get", ["admin"])["is_active"] is True


def test_cannot_lock_last_active_admin(db):
    assert accounts.set_account_active(db, "dieuphoi", False, "admin", NOW).ok
    assert accounts.count_active_admins(db) == 1
    r = accounts.set_account_active(db, "admin", False, "cust001", NOW)
    assert r.code == "last_admin"
    assert db.one("B01_account_get", ["admin"])["is_active"] is True


def test_lock_available_driver_goes_offline_and_leaves_area(db):
    assert any(r["driver_id"] == "DRV_551" for r in db.rows("B12_area_drivers", ["HCM", "TAN_PHU"]))
    assert accounts.set_account_active(db, "drv551", False, "admin", NOW).ok
    assert db.one("B03_driver_get", ["DRV_551"])["status"] == "OFFLINE"
    assert all(r["driver_id"] != "DRV_551" for r in db.rows("B12_area_drivers", ["HCM", "TAN_PHU"]))
    assert db.one("B01_account_get", ["drv551"])["is_active"] is False


def test_lock_busy_driver_refused_and_stays_active(db):
    r = accounts.set_account_active(db, "drv552", False, "admin", NOW)
    assert r.code == "driver_busy"
    assert db.one("B01_account_get", ["drv552"])["is_active"] is True
    assert db.one("B03_driver_get", ["DRV_552"])["status"] == "BUSY"


def test_lock_missing_account_creates_no_ghost_row(db):
    assert accounts.set_account_active(db, "nobody_x", False, "admin", NOW).code == "not_found"
    assert accounts.set_account_active(db, "nobody_x", True, "admin", NOW).code == "not_found"
    assert db.one("B01_account_get", ["nobody_x"]) is None


# ---------------- HTTP: đăng nhập, phân quyền ----------------
def test_guest_is_redirected_from_admin_and_post_actions(client_factory):
    c = client_factory()
    r = c.get("/admin/accounts")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    r = c.post("/admin/accounts/cust001/lock")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_customer_gets_403_on_admin_page_and_cannot_lock(client_factory, db):
    c = client_factory()
    assert http_login(c, "cust001").status_code == 303
    assert c.get("/admin/accounts").status_code == 403
    assert c.post("/admin/accounts/cust002/lock").status_code == 403
    assert c.post("/admin/accounts/cust002/unlock").status_code == 403
    assert db.one("B01_account_get", ["cust002"])["is_active"] is True


def test_driver_gets_403_on_admin_page(client_factory):
    c = client_factory()
    assert http_login(c, "drv553").status_code == 303
    assert c.get("/admin/accounts").status_code == 403


def test_admin_and_operator_can_open_accounts_page(client_factory):
    for user in ("admin", "dieuphoi"):
        c = client_factory()
        assert http_login(c, user).status_code == 303
        r = c.get("/admin/accounts")
        assert r.status_code == 200, user
        assert "drv560" in r.text
        assert "8d969eef" not in r.text  # giá trị băm không lộ ra trang/panel (tên cột trong CQL thì được)


def test_login_page_and_failed_login_do_not_create_session(client_factory):
    c = client_factory()
    assert c.get("/login").status_code == 200
    r = http_login(c, "cust001", "sai")
    assert r.status_code == 401
    assert "Sai tên đăng nhập hoặc mật khẩu" in r.text
    assert c.get("/admin/accounts").status_code == 303  # vẫn là khách


def test_failed_login_message_same_for_unknown_user(client_factory):
    c = client_factory()
    a = http_login(c, "cust001", "sai").text
    b = http_login(c, "khong_ton_tai", "sai").text
    assert "Sai tên đăng nhập hoặc mật khẩu" in a and "Sai tên đăng nhập hoặc mật khẩu" in b


def test_locked_account_cannot_login_over_http(client_factory, db):
    accounts.set_account_active(db, "cust002", False, "admin", NOW)
    c = client_factory()
    r = http_login(c, "cust002")
    assert r.status_code in (401, 403) and "khóa" in r.text


def test_account_locked_mid_session_is_blocked_on_every_request(client_factory, db):
    c = client_factory()
    assert http_login(c, "cust001").status_code == 303
    assert c.get("/").status_code == 200
    assert accounts.set_account_active(db, "cust001", False, "admin", NOW).ok
    r = c.get("/")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    # session đã bị xóa: kể cả mở khóa lại, cookie cũ không còn hiệu lực
    accounts.set_account_active(db, "cust001", True, "admin", NOW)
    r = c.get("/admin/accounts")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_locked_admin_is_blocked_on_admin_pages_and_actions(client_factory, db):
    c = client_factory()
    assert http_login(c, "dieuphoi").status_code == 303
    assert c.get("/admin/accounts").status_code == 200
    assert accounts.set_account_active(db, "dieuphoi", False, "admin", NOW).ok
    r = c.get("/admin/accounts")
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    r = c.post("/admin/accounts/cust003/lock")
    assert r.status_code == 303
    assert db.one("B01_account_get", ["cust003"])["is_active"] is True


def test_logout_ends_session(client_factory):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    assert c.get("/admin/accounts").status_code == 200
    assert c.post("/logout").status_code == 303
    assert c.get("/admin/accounts").status_code == 303


def test_http_admin_lock_unlock_flow_and_self_lock(client_factory, db):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    r = c.post("/admin/accounts/cust005/lock")
    assert r.status_code == 303 and r.headers["location"] == "/admin/accounts"
    assert db.one("B01_account_get", ["cust005"])["is_active"] is False
    page = c.get("/admin/accounts")
    assert "CQL của thao tác vừa rồi" in page.text and "T02" in page.text
    assert c.post("/admin/accounts/cust005/unlock").status_code == 303
    assert db.one("B01_account_get", ["cust005"])["is_active"] is True
    # tự khóa mình
    c.post("/admin/accounts/admin/lock")
    assert db.one("B01_account_get", ["admin"])["is_active"] is True
    # khóa tài xế BUSY
    c.post("/admin/accounts/drv552/lock")
    assert db.one("B01_account_get", ["drv552"])["is_active"] is True


def test_http_sole_remaining_admin_cannot_be_locked(client_factory, db):
    """Qua HTTP người khóa luôn là admin đang hoạt động nên 'admin cuối' chỉ gặp self_lock; last_admin do test service ở trên phủ."""
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    assert c.post("/admin/accounts/dieuphoi/lock").status_code == 303
    assert db.one("B01_account_get", ["dieuphoi"])["is_active"] is False
    assert accounts.count_active_admins(db) == 1
    page = c.post("/admin/accounts/admin/lock", follow_redirects=True)
    assert db.one("B01_account_get", ["admin"])["is_active"] is True
    assert page.status_code == 200


def test_register_over_http_then_login(client_factory, db):
    c = client_factory()
    assert c.get("/register").status_code == 200
    r = c.post("/register", data={"username": "cust016", "password": "matkhau1", "full_name": "Mười Sáu",
                                  "phone": "0912345678", "email": "a@b.vn", "address": "x"})
    assert r.status_code == 303
    assert db.one("B01_account_get", ["cust016"])["role"] == "CUSTOMER"
    assert http_login(c, "cust016", "matkhau1").status_code == 303
    bad = c.post("/register", data={"username": "cust016", "password": "matkhau1", "full_name": "Mười Sáu",
                                    "phone": "0912345678", "email": "a@b.vn", "address": "x"})
    assert bad.status_code == 409 and "đã được dùng" in bad.text
    bad2 = c.post("/register", data={"username": "X", "password": "1", "full_name": "",
                                     "phone": "1", "email": "x", "address": ""})
    assert bad2.status_code == 400
