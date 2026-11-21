import pytest

from config import AREAS
from db.repo import LwtResult
from domain.passwords import SEED_SHA256_123456, hash_password
from domain.tz import parse_vn
from services import accounts
from services.accounts import RegisterForm
from tests.fakes import FakeDb

pytestmark = pytest.mark.auth

NOW = parse_vn("2026-11-21 09:00:00")


def _form(**kw):
    base = dict(username="cust016", password="matkhau1", full_name="Nguyễn Văn Mười Sáu",
                phone="0912345678", email="a@b.vn", address="1 Lê Lợi")
    base.update(kw)
    return RegisterForm(**base)


def _acc(username="cust001", role="CUSTOMER", ref_id="CUST001", active=True, pw=SEED_SHA256_123456):
    return {"username": username, "password_hash": pw, "role": role, "ref_id": ref_id,
            "full_name": "X", "is_active": active, "created_at": None, "last_login_at": None}


# ---- đăng ký ----
def test_register_success_calls_account_then_customer():
    db = FakeDb()
    r = accounts.register_customer(db, _form(), NOW)
    assert r.ok and r.code == "ok"
    assert db.names() == ["T01_account_insert", "B18_customer_insert"]
    assert r.data["customer_id"].startswith("CUST_")
    t01 = dict(zip(["username", "hash", "role", "ref_id", "full_name", "now"], db.calls[0][1]))
    assert t01["role"] == "CUSTOMER" and t01["ref_id"] == r.data["customer_id"]
    assert t01["hash"].startswith("pbkdf2_sha256$")
    assert "matkhau1" not in str(db.calls)


def test_register_username_taken_does_not_touch_customers_and_hides_hash():
    db = FakeDb({"T01_account_insert": [LwtResult(False, {"username": "cust016", "password_hash": "h", "role": "CUSTOMER"})]})
    r = accounts.register_customer(db, _form(), NOW)
    assert not r.ok and r.code == "username_taken"
    assert r.current["username"] == "cust016"
    assert "password_hash" not in r.current
    assert db.names() == ["T01_account_insert"]


@pytest.mark.parametrize("field,value", [
    ("username", "Ab"), ("username", "CUST016"), ("username", "a b c"), ("username", "x" * 33),
    ("password", "12345"), ("phone", "912345678"), ("phone", "0912abc678"), ("email", "khong-co-a-cong"),
    ("full_name", "  "),
])
def test_register_invalid_input_makes_no_db_call(field, value):
    db = FakeDb()
    r = accounts.register_customer(db, _form(**{field: value}), NOW)
    assert not r.ok and r.code == "invalid_input"
    assert db.calls == []


def test_register_customer_write_failure_after_account_is_partial():
    db = FakeDb({"B18_customer_insert": [RuntimeError("timeout")]})
    r = accounts.register_customer(db, _form(), NOW)
    assert r.ok and r.code == "partial"


# ---- đăng nhập ----
def test_login_ok_touches_and_hides_hash():
    db = FakeDb({"B01_account_get": [_acc()]})
    r = accounts.login(db, "cust001", "123456", NOW)
    assert r.ok
    assert "password_hash" not in r.data["user"]
    assert r.data["user"]["username"] == "cust001" and r.data["user"]["ref_id"] == "CUST001"
    assert db.names() == ["B01_account_get", "T02_login_touch"]


def test_login_pbkdf2_account_ok():
    db = FakeDb({"B01_account_get": [_acc(pw=hash_password("matkhau1"))]})
    assert accounts.login(db, "cust001", "matkhau1", NOW).ok


def test_login_wrong_password_and_unknown_user_same_message_no_touch():
    wrong = FakeDb({"B01_account_get": [_acc()]})
    r1 = accounts.login(wrong, "cust001", "sai-mat-khau", NOW)
    unknown = FakeDb({"B01_account_get": [None]})
    r2 = accounts.login(unknown, "khong_co", "123456", NOW)
    assert r1.code == r2.code == "bad_credentials" and not r1.ok and not r2.ok
    assert r1.message == r2.message
    assert "T02_login_touch" not in wrong.names() + unknown.names()


def test_login_locked_account_is_refused_without_touch():
    db = FakeDb({"B01_account_get": [_acc(active=False)]})
    r = accounts.login(db, "cust001", "123456", NOW)
    assert not r.ok and r.code == "account_locked"
    assert "T02_login_touch" not in db.names()


def test_login_locked_account_with_wrong_password_does_not_reveal_lock():
    db = FakeDb({"B01_account_get": [_acc(active=False)]})
    assert accounts.login(db, "cust001", "sai", NOW).code == "bad_credentials"


def test_login_unknown_role_is_refused():
    db = FakeDb({"B01_account_get": [_acc(role="HACKER")]})
    assert accounts.login(db, "cust001", "123456", NOW).code == "bad_credentials"


# ---- load_active_user ----
def test_load_active_user_none_for_missing_or_locked_and_strips_hash():
    assert accounts.load_active_user(FakeDb({"B01_account_get": [None]}), "x") is None
    assert accounts.load_active_user(FakeDb({"B01_account_get": [_acc(active=False)]}), "cust001") is None
    u = accounts.load_active_user(FakeDb({"B01_account_get": [_acc()]}), "cust001")
    assert u["username"] == "cust001" and "password_hash" not in u


def test_load_active_user_none_for_unknown_role():
    assert accounts.load_active_user(FakeDb({"B01_account_get": [_acc(role="HACKER")]}), "cust001") is None


# ---- khóa / mở khóa ----
def test_lock_driver_goes_offline_first_then_locks_then_clears_all_areas():
    db = FakeDb({"B01_account_get": [_acc("drv551", "DRIVER", "DRV_551")]})
    r = accounts.set_account_active(db, "drv551", False, "admin", NOW)
    assert r.ok
    names = db.names()
    assert names.index("APP09_driver_offline") < names.index("T02_account_lock")
    after = names[names.index("T02_account_lock") + 1:]
    assert after == ["T05_area_delete"] * 11
    assert len(AREAS["HCM"]) + len(AREAS["HN"]) == 11
    deleted = {(p[0], p[1]) for n, p in db.calls if n == "T05_area_delete"}
    assert deleted == {(c, d) for c, ds in AREAS.items() for d in ds}
    assert all(p[2] == "DRV_551" for n, p in db.calls if n == "T05_area_delete")


def test_lock_busy_driver_is_refused_and_account_untouched():
    db = FakeDb({"B01_account_get": [_acc("drv552", "DRIVER", "DRV_552")],
                 "APP09_driver_offline": [LwtResult(False, {"status": "BUSY"})]})
    r = accounts.set_account_active(db, "drv552", False, "admin", NOW)
    assert not r.ok and r.code == "driver_busy"
    assert "T02_account_lock" not in db.names()
    assert "T05_area_delete" not in db.names()


def test_lock_offline_driver_still_locks():
    db = FakeDb({"B01_account_get": [_acc("drv555", "DRIVER", "DRV_555")],
                 "APP09_driver_offline": [LwtResult(False, {"status": "OFFLINE"})]})
    assert accounts.set_account_active(db, "drv555", False, "admin", NOW).ok
    assert "T02_account_lock" in db.names()


def test_lock_self_refused_before_any_write():
    db = FakeDb({"B01_account_get": [_acc("admin", "ADMIN", None)]})
    r = accounts.set_account_active(db, "admin", False, "admin", NOW)
    assert r.code == "self_lock" and not r.ok
    assert not any(n.startswith(("T02", "APP09")) for n in db.names())


def test_lock_last_admin_refused():
    db = FakeDb({"B01_account_get": [_acc("dieuphoi", "OPERATOR", None)],
                 "APP01_accounts_scan": [[_acc("dieuphoi", "OPERATOR", None),
                                          _acc("admin", "ADMIN", None, active=False), _acc("cust001")]]})
    r = accounts.set_account_active(db, "dieuphoi", False, "cust001", NOW)
    assert r.code == "last_admin"
    assert "T02_account_lock" not in db.names()


def test_lock_admin_ok_when_another_active_admin_exists():
    db = FakeDb({"B01_account_get": [_acc("dieuphoi", "OPERATOR", None)],
                 "APP01_accounts_scan": [[_acc("dieuphoi", "OPERATOR", None), _acc("admin", "ADMIN", None)]]})
    assert accounts.set_account_active(db, "dieuphoi", False, "admin", NOW).ok


def test_lock_missing_account_is_not_found():
    db = FakeDb({"B01_account_get": [None]})
    r = accounts.set_account_active(db, "ghost", False, "admin", NOW)
    assert r.code == "not_found" and db.names() == ["B01_account_get"]


def test_lock_already_locked_is_idempotent_ok():
    db = FakeDb({"B01_account_get": [_acc(active=False)],
                 "T02_account_lock": [LwtResult(False, {"is_active": False})]})
    r = accounts.set_account_active(db, "cust001", False, "admin", NOW)
    assert r.ok and r.code == "duplicate_ok"


def test_unlock_runs_only_unlock_lwt():
    db = FakeDb()
    r = accounts.set_account_active(db, "cust001", True, "admin", NOW)
    assert r.ok and db.names() == ["T02_account_unlock"]


def test_unlock_missing_account_is_not_found():
    db = FakeDb({"T02_account_unlock": [LwtResult(False, {"is_active": None})]})
    assert accounts.set_account_active(db, "ghost", True, "admin", NOW).code == "not_found"


# ---- đếm / liệt kê ----
def test_count_active_admins_counts_operator_and_skips_locked():
    db = FakeDb({"APP01_accounts_scan": [[_acc("a", "ADMIN", None), _acc("b", "OPERATOR", None),
                                          _acc("c", "ADMIN", None, active=False), _acc("d")]]})
    assert accounts.count_active_admins(db) == 2


def test_list_accounts_sorted_without_hash():
    db = FakeDb({"APP01_accounts_scan": [[_acc("b"), _acc("a")]]})
    out = accounts.list_accounts(db)
    assert [a["username"] for a in out] == ["a", "b"]
    assert all("password_hash" not in a for a in out)
