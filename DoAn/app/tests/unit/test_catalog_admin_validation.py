import pytest

from db.repo import LwtResult
from domain.tz import parse_vn
from services import catalog_admin as ca
from services.catalog_admin import CustomerForm, DriverForm, PromoForm, VehicleForm
from tests.fakes import FakeDb

NOW = parse_vn("2026-11-21 09:00:00")


def _cust(**kw):
    base = dict(customer_id="CUST900", full_name="Khách Thử", phone="0901234567", email="a@b.vn", address="x")
    base.update(kw)
    return CustomerForm(**base)


def _drv(**kw):
    base = dict(driver_id="DRV_900", full_name="Tài Xế Thử", license_number="790112345600", phone="0912000900")
    base.update(kw)
    return DriverForm(**base)


def _veh(**kw):
    base = dict(vehicle_id="VEH_900", driver_id="DRV_900", license_plate="51A-999.99", model="Vios", color="Trắng")
    base.update(kw)
    return VehicleForm(**base)


def _promo(**kw):
    base = dict(promo_code="TEST10", description="Thử", discount_percent=10, max_discount=10000.0,
                min_fare=20000.0, cities={"HCM"}, usage_limit=10,
                valid_from=parse_vn("2026-11-01 00:00:00"), valid_to=parse_vn("2026-12-31 23:59:59"))
    base.update(kw)
    return PromoForm(**base)


# ---------------- validation thuần ----------------
def test_valid_forms_have_no_errors():
    assert ca.validate_customer(_cust()) == []
    assert ca.validate_driver(_drv()) == []
    assert ca.validate_vehicle(_veh()) == []
    assert ca.validate_promo(_promo()) == []


def test_customer_bad_phone_and_id():
    assert ca.validate_customer(_cust(phone="123"))
    assert ca.validate_customer(_cust(customer_id="cust900"))
    assert ca.validate_customer(_cust(customer_id="DRV_1"))
    assert ca.validate_customer(_cust(full_name="  "))
    assert ca.validate_customer(_cust(email="khong-co-a-cong"))


def test_driver_license_must_be_12_digits_and_id_prefix():
    assert ca.validate_driver(_drv(license_number="12345"))
    assert ca.validate_driver(_drv(license_number="79011234560X"))
    assert ca.validate_driver(_drv(driver_id="DRV900"))
    assert ca.validate_driver(_drv(phone="0912"))


def test_vehicle_plate_length_and_id_prefix():
    assert ca.validate_vehicle(_veh(license_plate=""))
    assert ca.validate_vehicle(_veh(license_plate="x" * 16))
    assert ca.validate_vehicle(_veh(vehicle_id="VEH900"))
    assert ca.validate_vehicle(_veh(license_plate="x" * 15)) == []


def test_promo_percent_limit_dates_cities():
    assert ca.validate_promo(_promo(discount_percent=0))
    assert ca.validate_promo(_promo(discount_percent=101))
    assert ca.validate_promo(_promo(usage_limit=0))
    assert ca.validate_promo(_promo(promo_code="ab"))
    assert ca.validate_promo(_promo(cities={"hcm"}))
    vf, vt = parse_vn("2026-12-31 00:00:00"), parse_vn("2026-11-01 00:00:00")
    assert ca.validate_promo(_promo(valid_from=vf, valid_to=vt))
    assert ca.validate_promo(_promo(valid_from=vf, valid_to=vf))  # bằng nhau cũng sai


# ---------------- service với FakeDb ----------------
def test_invalid_form_never_touches_db():
    db = FakeDb()
    assert ca.create_customer(db, _cust(phone="123"), NOW).code == "invalid_input"
    assert ca.update_customer(db, _cust(phone="123")).code == "invalid_input"
    assert ca.create_driver(db, _drv(license_number="1")).code == "invalid_input"
    assert ca.create_promo(db, _promo(discount_percent=0)).code == "invalid_input"
    assert db.calls == []


def test_create_customer_duplicate_returns_current():
    db = FakeDb({"B18_customer_insert": [LwtResult(False, {"customer_id": "CUST900"})]})
    r = ca.create_customer(db, _cust(), NOW)
    assert r.code == "duplicate" and r.current == {"customer_id": "CUST900"}


def test_update_customer_not_applied_is_not_found():
    db = FakeDb({"B19_customer_update": [LwtResult(False, None)]})
    assert ca.update_customer(db, _cust()).code == "not_found"


def test_delete_customer_checks_rides_then_accounts_before_delete():
    db = FakeDb({"B02_customer_get": [{"customer_id": "CUST900"}], "B09_customer_has_rides": [{"ride_id": "R"}]})
    assert ca.delete_customer(db, "CUST900").code == "has_rides"
    assert "B20_customer_delete" not in db.names()
    db = FakeDb({"B02_customer_get": [{"customer_id": "CUST900"}],
                 "APP01_accounts_scan": [[{"username": "u1", "ref_id": "CUST900"}]]})
    assert ca.delete_customer(db, "CUST900").code == "in_use"
    assert "B20_customer_delete" not in db.names()


def test_driver_has_rides_scans_every_month_from_first_month():
    db = FakeDb()
    assert ca.driver_has_rides(db, "DRV_1", NOW) is False
    months = [p[1] for n, p in db.calls if n == "APP22_driver_has_rides"]
    assert months == [202609, 202610, 202611]


def test_driver_has_rides_crosses_year_boundary():
    db = FakeDb()
    ca.driver_has_rides(db, "DRV_1", parse_vn("2027-02-05 10:00:00"), first_month=202611)
    assert [p[1] for n, p in db.calls if n == "APP22_driver_has_rides"] == [202611, 202612, 202701, 202702]


def test_delete_driver_busy_when_lwt_not_applied():
    db = FakeDb({"B03_driver_get": [{"driver_id": "DRV_9"}], "APP06_driver_delete": [LwtResult(False, {"status": "BUSY"})]})
    assert ca.delete_driver(db, "DRV_9", NOW).code == "driver_busy"


def test_delete_driver_in_use_by_vehicle():
    db = FakeDb({"B03_driver_get": [{"driver_id": "DRV_9"}],
                 "APP10_vehicles_scan": [[{"vehicle_id": "VEH_9", "driver_id": "DRV_9"}]]})
    r = ca.delete_driver(db, "DRV_9", NOW)
    assert r.code == "in_use" and "APP06_driver_delete" not in db.names()


def test_vehicle_unknown_driver_and_duplicate_plate():
    db = FakeDb()  # B03 trả None
    assert ca.create_vehicle(db, _veh()).code == "invalid_input"
    assert "APP11_vehicle_insert" not in db.names()
    db = FakeDb({"B03_driver_get": [{"driver_id": "DRV_900"}],
                 "B05_vehicle_by_plate": [{"vehicle_id": "VEH_OTHER", "license_plate": "51A-999.99"}]})
    r = ca.create_vehicle(db, _veh())
    assert r.code == "duplicate_plate" and "APP11_vehicle_insert" not in db.names()


def test_vehicle_update_same_vehicle_keeps_its_own_plate():
    db = FakeDb({"B03_driver_get": [{"driver_id": "DRV_900"}],
                 "B05_vehicle_by_plate": [{"vehicle_id": "VEH_900", "license_plate": "51A-999.99"}]})
    assert ca.update_vehicle(db, _veh()).ok


def test_update_promo_uses_read_used_count_as_condition():
    db = FakeDb({"B16_promo_get": [{"promo_code": "TEST10", "used_count": 3}]})
    assert ca.update_promo(db, _promo(usage_limit=5)).ok
    name, params = [c for c in db.calls if c[0] == "APP18_promo_update"][0]
    assert params[-2:] == ("TEST10", 3)


def test_update_promo_limit_below_used_count_rejected():
    db = FakeDb({"B16_promo_get": [{"promo_code": "TEST10", "used_count": 5}]})
    assert ca.update_promo(db, _promo(usage_limit=4)).code == "invalid_input"
    assert "APP18_promo_update" not in db.names()


def test_update_promo_lost_race_reports_lwt_lost():
    db = FakeDb({"B16_promo_get": [{"promo_code": "TEST10", "used_count": 3}, {"promo_code": "TEST10", "used_count": 4}],
                 "APP18_promo_update": [LwtResult(False, {"used_count": 4})]})
    assert ca.update_promo(db, _promo()).code == "lwt_lost"


def test_delete_promo_not_applied_in_use_or_missing():
    db = FakeDb({"APP19_promo_delete": [LwtResult(False, {"used_count": 5})]})
    assert ca.delete_promo(db, "GIAM20").code == "in_use"
    db = FakeDb({"APP19_promo_delete": [LwtResult(False, {"used_count": None})]})
    assert ca.delete_promo(db, "NOPE").code == "not_found"


def test_city_change_not_applied_is_not_found_and_bad_city_rejected():
    db = FakeDb({"T11_promo_city_add": [LwtResult(False, None)]})
    assert ca.add_promo_city(db, "NOPE", "DN").code == "not_found"
    db = FakeDb()
    assert ca.add_promo_city(db, "GIAM20", "d n").code == "invalid_input"
    assert db.calls == []
