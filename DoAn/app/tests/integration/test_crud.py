import time

import pytest

from domain.tz import parse_vn
from services import catalog_admin as ca
from services.catalog_admin import CustomerForm, DriverForm, PromoForm, VehicleForm
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.crud

NOW = parse_vn("2026-11-21 09:00:00")


def _cust(**kw):
    base = dict(customer_id="CUST900", full_name="Khách Chín Trăm", phone="0901000900",
                email="c900@x.vn", address="9 Nguyễn Trãi")
    base.update(kw)
    return CustomerForm(**base)


def _drv(**kw):
    base = dict(driver_id="DRV_900", full_name="Tài Xế Chín Trăm", license_number="790112345900", phone="0912000900")
    base.update(kw)
    return DriverForm(**base)


def _veh(**kw):
    base = dict(vehicle_id="VEH_900", driver_id="DRV_900", license_plate="51A-999.99", model="Vios", color="Trắng")
    base.update(kw)
    return VehicleForm(**base)


def _promo(**kw):
    base = dict(promo_code="TEST10", description="Mã thử", discount_percent=10, max_discount=10000.0,
                min_fare=20000.0, cities={"HCM"}, usage_limit=10,
                valid_from=parse_vn("2026-11-01 00:00:00"), valid_to=parse_vn("2026-12-31 23:59:59"))
    base.update(kw)
    return PromoForm(**base)


def _wait_plate(db, plate, want_ids, timeout=5.0):
    """MV cập nhật bất đồng bộ: poll tối đa `timeout` giây cho tới khi kết quả tra theo biển khớp want_ids."""
    deadline = time.time() + timeout
    got = []
    while time.time() < deadline:
        got = [r["vehicle_id"] for r in ca.find_vehicle_by_plate(db, plate)]
        if got == want_ids:
            return got
        time.sleep(0.1)
    return got


# ---------------- customers ----------------
def test_customer_create_duplicate_update_delete(db):
    assert ca.create_customer(db, _cust(), NOW).ok
    row = db.one("B02_customer_get", ["CUST900"])
    assert row["full_name"] == "Khách Chín Trăm" and row["created_at"] is not None
    dup = ca.create_customer(db, _cust(full_name="Người khác"), NOW)
    assert dup.code == "duplicate" and dup.current["customer_id"] == "CUST900"
    assert db.one("B02_customer_get", ["CUST900"])["full_name"] == "Khách Chín Trăm"  # không bị ghi đè

    assert ca.update_customer(db, _cust(phone="0908888888")).ok
    assert db.one("B02_customer_get", ["CUST900"])["phone"] == "0908888888"

    assert ca.delete_customer(db, "CUST900").ok
    assert db.one("B02_customer_get", ["CUST900"]) is None


def test_customer_with_rides_cannot_be_deleted(db):
    r = ca.delete_customer(db, "CUST001")
    assert r.code == "has_rides"
    assert db.one("B02_customer_get", ["CUST001"]) is not None


def test_customer_with_account_cannot_be_deleted(db):
    from services import accounts
    from services.accounts import RegisterForm

    reg = accounts.register_customer(db, RegisterForm("cust016", "matkhau1", "Mười Sáu", "0912345678", "a@b.vn"), NOW)
    cid = reg.data["customer_id"]
    assert ca.customer_has_rides(db, cid) is False  # khách mới chưa có chuyến, nhưng có tài khoản cust016
    r = ca.delete_customer(db, cid)
    assert r.code == "in_use" and r.data["accounts"] == ["cust016"]
    assert db.one("B02_customer_get", [cid]) is not None


# ---------------- drivers ----------------
def test_driver_create_defaults_duplicate_and_delete(db):
    assert ca.create_driver(db, _drv()).ok
    d = db.one("B03_driver_get", ["DRV_900"])
    assert d["status"] == "OFFLINE" and d["rating"] == 5.0
    assert ca.create_driver(db, _drv()).code == "duplicate"

    assert ca.delete_driver(db, "DRV_555", NOW).code == "has_rides"
    assert db.one("B03_driver_get", ["DRV_555"]) is not None

    assert ca.delete_driver(db, "DRV_900", NOW).ok
    assert db.one("B03_driver_get", ["DRV_900"]) is None


def test_driver_has_rides_detected_from_seed_month(db):
    assert ca.driver_has_rides(db, "DRV_555", NOW) is True
    assert ca.driver_has_rides(db, "DRV_NOPE", NOW) is False


def test_busy_driver_without_rides_cannot_be_deleted(db):
    assert ca.create_driver(db, _drv()).ok
    assert db.lwt("APP20_driver_online", ["DRV_900"]).applied
    r = ca.delete_driver(db, "DRV_900", NOW)
    assert r.code == "driver_busy" and db.one("B03_driver_get", ["DRV_900"])["status"] == "AVAILABLE"


def test_driver_with_vehicle_or_account_cannot_be_deleted(db):
    assert ca.create_driver(db, _drv()).ok
    assert ca.create_vehicle(db, _veh()).ok
    r = ca.delete_driver(db, "DRV_900", NOW)
    assert r.code == "in_use" and r.data["vehicles"] == ["VEH_900"] and r.data["accounts"] == []
    assert ca.delete_vehicle(db, "VEH_900").ok
    # còn tài khoản trỏ tới (ref_id = DRV_900) cũng chặn xóa
    assert db.lwt("T01_account_insert", ["drv900", "x", "DRIVER", "DRV_900", "Tài Xế Chín Trăm", NOW]).applied
    r = ca.delete_driver(db, "DRV_900", NOW)
    assert r.code == "in_use" and r.data["accounts"] == ["drv900"]
    assert db.one("B03_driver_get", ["DRV_900"]) is not None


# ---------------- vehicles + MV ----------------
def test_vehicle_lookup_by_plate_via_mv_and_plate_change(db):
    assert ca.create_driver(db, _drv()).ok
    assert ca.create_vehicle(db, _veh()).ok
    assert _wait_plate(db, "51A-999.99", ["VEH_900"]) == ["VEH_900"]
    assert ca.find_vehicle_by_plate(db, "51A-999.99")[0]["vehicle_id"] == "VEH_900"

    assert ca.update_vehicle(db, _veh(license_plate="51A-888.88")).ok
    assert _wait_plate(db, "51A-888.88", ["VEH_900"]) == ["VEH_900"]
    assert _wait_plate(db, "51A-999.99", []) == []  # biển cũ không còn trong MV


def test_vehicle_seed_lookup_and_duplicate_plate(db):
    assert ca.find_vehicle_by_plate(db, "51K-567.89")[0]["vehicle_id"] == "VEH_555"
    assert ca.create_driver(db, _drv()).ok
    r = ca.create_vehicle(db, _veh(vehicle_id="VEH_901", license_plate="51K-567.89"))
    assert r.code == "duplicate_plate" and r.current["vehicle_id"] == "VEH_555"
    assert db.one("B04_vehicle_get", ["VEH_901"]) is None


def test_vehicle_needs_existing_driver_and_duplicate_id(db):
    assert ca.create_vehicle(db, _veh(driver_id="DRV_NOPE")).code == "invalid_input"
    assert db.one("B04_vehicle_get", ["VEH_900"]) is None
    assert ca.create_driver(db, _drv()).ok
    assert ca.create_vehicle(db, _veh()).ok
    assert ca.create_vehicle(db, _veh(license_plate="51A-111.11")).code == "duplicate"


def test_vehicle_delete_removes_mv_row(db):
    assert ca.create_driver(db, _drv()).ok
    assert ca.create_vehicle(db, _veh()).ok
    assert _wait_plate(db, "51A-999.99", ["VEH_900"]) == ["VEH_900"]
    assert ca.delete_vehicle(db, "VEH_900").ok
    assert _wait_plate(db, "51A-999.99", []) == []
    assert ca.delete_vehicle(db, "VEH_900").code == "not_found"


# ---------------- promotions + set cities ----------------
def test_promo_create_update_delete_rules(db):
    assert ca.create_promo(db, _promo()).ok
    p = db.one("B16_promo_get", ["TEST10"])
    assert p["used_count"] == 0 and set(p["cities"]) == {"HCM"}
    assert ca.create_promo(db, _promo()).code == "duplicate"

    assert ca.update_promo(db, _promo(usage_limit=4)).ok  # used_count = 0 nên sửa được
    assert db.one("B16_promo_get", ["TEST10"])["usage_limit"] == 4
    assert set(db.one("B16_promo_get", ["TEST10"])["cities"]) == {"HCM"}  # sửa không đụng cities

    assert ca.update_promo(db, _promo(promo_code="GIAM20", usage_limit=4)).code == "invalid_input"  # used_count = 5
    assert db.one("B16_promo_get", ["GIAM20"])["usage_limit"] == 500
    assert ca.delete_promo(db, "GIAM20").code == "in_use"
    assert db.one("B16_promo_get", ["GIAM20"]) is not None

    assert ca.delete_promo(db, "TEST10").ok
    assert db.one("B16_promo_get", ["TEST10"]) is None


def test_promo_update_can_change_fields_when_used(db):
    assert ca.update_promo(db, _promo(promo_code="GIAM20", usage_limit=600, discount_percent=25)).ok
    p = db.one("B16_promo_get", ["GIAM20"])
    assert p["usage_limit"] == 600 and p["discount_percent"] == 25 and p["used_count"] == 5


def test_promo_city_add_and_remove(db):
    r = ca.add_promo_city(db, "GIAM20", "DN")
    assert r.ok and set(r.data["cities"]) == {"DN", "HCM", "HN"}
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"DN", "HCM", "HN"}
    r = ca.remove_promo_city(db, "GIAM20", "DN")
    assert r.ok and set(r.data["cities"]) == {"HCM", "HN"}
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"HCM", "HN"}
    assert ca.add_promo_city(db, "GIAM20", "HN").ok  # thêm phần tử đã có: idempotent
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"HCM", "HN"}


# ---------------- Review Focus 1: không tạo dòng ma ----------------
def test_update_missing_entities_creates_no_row(db):
    r = ca.update_customer(db, _cust(customer_id="CUST_NOPE"))
    assert r.code == "not_found" and db.one("B02_customer_get", ["CUST_NOPE"]) is None

    r = ca.add_promo_city(db, "NOPE", "DN")
    assert r.code == "not_found" and db.one("B16_promo_get", ["NOPE"]) is None
    r = ca.remove_promo_city(db, "NOPE", "DN")
    assert r.code == "not_found" and db.one("B16_promo_get", ["NOPE"]) is None

    r = ca.update_driver(db, _drv(driver_id="DRV_NOPE"))
    assert r.code == "not_found" and db.one("B03_driver_get", ["DRV_NOPE"]) is None

    assert ca.create_driver(db, _drv()).ok
    r = ca.update_vehicle(db, _veh(vehicle_id="VEH_NOPE", license_plate="51Z-000.00"))
    assert r.code == "not_found" and db.one("B04_vehicle_get", ["VEH_NOPE"]) is None
    assert _wait_plate(db, "51Z-000.00", []) == []

    r = ca.update_promo(db, _promo(promo_code="NOPE"))
    assert r.code == "not_found" and db.one("B16_promo_get", ["NOPE"]) is None
    assert ca.delete_promo(db, "NOPE").code == "not_found"
    assert ca.delete_customer(db, "CUST_NOPE").code == "not_found"
    assert ca.delete_driver(db, "DRV_NOPE", NOW).code == "not_found"
    assert db.one("B03_driver_get", ["DRV_NOPE"]) is None


# ---------------- HTTP ----------------
def test_admin_customers_page_lists_seed_rows(client_factory):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    r = c.get("/admin/customers")
    assert r.status_code == 200 and "CUST010" in r.text
    for path in ("/admin/drivers", "/admin/vehicles", "/admin/promotions"):
        assert c.get(path).status_code == 200, path
    assert "DRV_555" in c.get("/admin/drivers").text
    assert "GIAM20" in c.get("/admin/promotions").text


def test_operator_can_open_catalog_pages(client_factory):
    c = client_factory()
    assert http_login(c, "dieuphoi").status_code == 303
    assert c.get("/admin/customers").status_code == 200


def test_customer_and_driver_and_guest_cannot_use_crud(client_factory, db):
    guest = client_factory()
    assert guest.get("/admin/customers").status_code == 303
    assert guest.post("/admin/customers", data={"customer_id": "CUST900"}).status_code == 303

    cust = client_factory()
    assert http_login(cust, "cust001").status_code == 303
    for path in ("/admin/customers", "/admin/customers/new", "/admin/drivers", "/admin/vehicles",
                 "/admin/vehicles/by-plate?plate=51K-567.89", "/admin/promotions", "/admin/promotions/new",
                 "/admin/customers/CUST001/edit"):
        assert cust.get(path).status_code == 403, path
    r = cust.post("/admin/customers", data={"customer_id": "CUST900", "full_name": "X", "phone": "0901000900",
                                            "email": "a@b.vn", "address": ""})
    assert r.status_code == 403 and db.one("B02_customer_get", ["CUST900"]) is None
    assert cust.post("/admin/customers/CUST010/delete").status_code == 403
    assert cust.post("/admin/promotions/GIAM20/cities/add", data={"city": "DN"}).status_code == 403
    assert cust.post("/admin/promotions/GIAM20/delete").status_code == 403
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"HCM", "HN"}

    drv = client_factory()
    assert http_login(drv, "drv553").status_code == 303
    assert drv.get("/admin/drivers").status_code == 403
    assert drv.post("/admin/drivers/DRV_553/delete").status_code == 403


def test_http_customer_crud_flow(client_factory, db):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    assert c.get("/admin/customers/new").status_code == 200
    data = {"customer_id": "CUST900", "full_name": "Khách Chín Trăm", "phone": "0901000900",
            "email": "c900@x.vn", "address": "9 Nguyễn Trãi"}
    r = c.post("/admin/customers", data=data)
    assert r.status_code == 303 and r.headers["location"] == "/admin/customers"
    assert db.one("B02_customer_get", ["CUST900"]) is not None
    page = c.get("/admin/customers")
    assert "CUST900" in page.text and "CQL của thao tác vừa rồi" in page.text and "B18" in page.text

    bad = c.post("/admin/customers", data=data)  # trùng
    assert bad.status_code == 409 and "đã tồn tại" in bad.text
    bad = c.post("/admin/customers", data={**data, "customer_id": "CUST901", "phone": "123"})
    assert bad.status_code == 400 and db.one("B02_customer_get", ["CUST901"]) is None

    assert c.get("/admin/customers/CUST900/edit").status_code == 200
    r = c.post("/admin/customers/CUST900", data={**data, "phone": "0908888888"})
    assert r.status_code == 303
    assert db.one("B02_customer_get", ["CUST900"])["phone"] == "0908888888"
    # sửa thực thể không có: không tạo dòng
    assert c.post("/admin/customers/CUST_NOPE", data={**data, "customer_id": "CUST_NOPE"}).status_code == 404
    assert db.one("B02_customer_get", ["CUST_NOPE"]) is None
    assert c.get("/admin/customers/CUST_NOPE/edit").status_code == 404

    r = c.post("/admin/customers/CUST001/delete")
    assert r.status_code == 303 and db.one("B02_customer_get", ["CUST001"]) is not None
    r = c.post("/admin/customers/CUST900/delete")
    assert r.status_code == 303 and db.one("B02_customer_get", ["CUST900"]) is None


def test_http_vehicle_by_plate_page(client_factory):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    r = c.get("/admin/vehicles/by-plate", params={"plate": "51K-567.89"})
    assert r.status_code == 200 and "VEH_555" in r.text and "vehicles_by_plate" in r.text
    r = c.get("/admin/vehicles/by-plate", params={"plate": "00X-000.00"})
    assert r.status_code == 200 and "Không tìm thấy" in r.text


def test_http_promotion_cities_add_remove_and_create(client_factory, db):
    c = client_factory()
    assert http_login(c, "admin").status_code == 303
    r = c.post("/admin/promotions/GIAM20/cities/add", data={"city": "DN"})
    assert r.status_code == 303
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"DN", "HCM", "HN"}
    r = c.post("/admin/promotions/GIAM20/cities/remove", data={"city": "DN"})
    assert r.status_code == 303
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"HCM", "HN"}
    c.post("/admin/promotions/NOPE/cities/add", data={"city": "DN"})
    assert db.one("B16_promo_get", ["NOPE"]) is None

    form = {"promo_code": "TEST10", "description": "Mã thử", "discount_percent": "10", "max_discount": "10000",
            "min_fare": "20000", "cities": "HCM, HN", "usage_limit": "10",
            "valid_from": "2026-11-01T00:00", "valid_to": "2026-12-31T23:59"}
    r = c.post("/admin/promotions", data=form)
    assert r.status_code == 303
    p = db.one("B16_promo_get", ["TEST10"])
    assert p["used_count"] == 0 and set(p["cities"]) == {"HCM", "HN"}
    bad = c.post("/admin/promotions", data={**form, "promo_code": "TEST11", "discount_percent": "0"})
    assert bad.status_code == 400 and db.one("B16_promo_get", ["TEST11"]) is None
    bad = c.post("/admin/promotions", data={**form, "promo_code": "TEST12", "discount_percent": "abc"})
    assert bad.status_code == 400 and db.one("B16_promo_get", ["TEST12"]) is None
    assert c.get("/admin/promotions/TEST10/edit").status_code == 200
    r = c.post("/admin/promotions/TEST10", data={**form, "usage_limit": "20"})
    assert r.status_code == 303 and db.one("B16_promo_get", ["TEST10"])["usage_limit"] == 20
    assert c.post("/admin/promotions/GIAM20/delete").status_code == 303
    assert db.one("B16_promo_get", ["GIAM20"]) is not None
    assert c.post("/admin/promotions/TEST10/delete").status_code == 303
    assert db.one("B16_promo_get", ["TEST10"]) is None
