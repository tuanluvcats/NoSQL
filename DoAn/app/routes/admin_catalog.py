"""Quản trị danh mục: khách, tài xế, xe (tra MV theo biển số), khuyến mãi (set cities). Chỉ ADMIN/OPERATOR."""
from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import RedirectResponse

from domain.auth import ADMIN
from domain.tz import parse_vn, to_vn
from routes.deps import flash_trace, get_db, render, require_role, set_flash
from services import catalog_admin as ca
from services.catalog_admin import CustomerForm, DriverForm, PromoForm, VehicleForm
from services.result import ActionResult

router = APIRouter(prefix="/admin")
_ADMIN = Depends(require_role(ADMIN))

_STATUS = {"invalid_input": 400, "duplicate": 409, "duplicate_plate": 409, "not_found": 404}


def _status(result: ActionResult) -> int:
    return _STATUS.get(result.code, 409)


def _first_month(request: Request) -> int:
    return request.app.state.settings.first_month


def _done(request: Request, result: ActionResult, location: str):
    """PRG (D14): flash + giữ trace của thao tác rồi redirect."""
    set_flash(request, result.ok, result.message)
    flash_trace(request)
    return RedirectResponse(location, status_code=303)


def _dt_input(dt: datetime | None) -> str:
    return to_vn(dt).strftime("%Y-%m-%dT%H:%M") if dt else ""


def _parse_dt(s: str) -> datetime | None:
    s = (s or "").strip().replace("T", " ")
    try:
        return parse_vn(s) if s else None
    except ValueError:
        return None


# ------------------------------------------------------------- customers
def _customer_page(request: Request, form: dict, is_new: bool, errors: list[str], status: int = 200):
    return render(request, "admin/customer_form.html", {"form": form, "is_new": is_new, "errors": errors},
                  status_code=status)


def _customer_dict(f: CustomerForm) -> dict:
    return {"customer_id": f.customer_id, "full_name": f.full_name, "phone": f.phone,
            "email": f.email, "address": f.address}


@router.get("/customers")
def customers_list(request: Request, user: dict = _ADMIN):
    return render(request, "admin/customers.html", {"rows": ca.list_customers(get_db(request))})


@router.get("/customers/new")
def customers_new(request: Request, user: dict = _ADMIN):
    return _customer_page(request, {}, True, [])


@router.post("/customers")
def customers_create(request: Request, customer_id: str = Form(""), full_name: str = Form(""),
                     phone: str = Form(""), email: str = Form(""), address: str = Form(""),
                     user: dict = _ADMIN):
    f = CustomerForm(customer_id.strip(), full_name, phone.strip(), email.strip(), address)
    result = ca.create_customer(get_db(request), f, request.app.state.clock())
    if not result.ok:
        return _customer_page(request, _customer_dict(f), True, [result.message], _status(result))
    return _done(request, result, "/admin/customers")


@router.get("/customers/{customer_id}/edit")
def customers_edit(request: Request, customer_id: str, user: dict = _ADMIN):
    row = ca.get_customer(get_db(request), customer_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy khách {customer_id}.")
    return _customer_page(request, row, False, [])


@router.post("/customers/{customer_id}/delete")
def customers_delete(request: Request, customer_id: str, user: dict = _ADMIN):
    return _done(request, ca.delete_customer(get_db(request), customer_id), "/admin/customers")


@router.post("/customers/{customer_id}")
def customers_update(request: Request, customer_id: str, full_name: str = Form(""), phone: str = Form(""),
                     email: str = Form(""), address: str = Form(""), user: dict = _ADMIN):
    f = CustomerForm(customer_id, full_name, phone.strip(), email.strip(), address)
    result = ca.update_customer(get_db(request), f)
    if not result.ok:
        return _customer_page(request, _customer_dict(f), False, [result.message], _status(result))
    return _done(request, result, "/admin/customers")


# --------------------------------------------------------------- drivers
def _driver_page(request: Request, form: dict, is_new: bool, errors: list[str], status: int = 200):
    return render(request, "admin/driver_form.html", {"form": form, "is_new": is_new, "errors": errors},
                  status_code=status)


def _driver_dict(f: DriverForm) -> dict:
    return {"driver_id": f.driver_id, "full_name": f.full_name, "license_number": f.license_number, "phone": f.phone}


@router.get("/drivers")
def drivers_list(request: Request, user: dict = _ADMIN):
    return render(request, "admin/drivers.html", {"rows": ca.list_drivers(get_db(request))})


@router.get("/drivers/new")
def drivers_new(request: Request, user: dict = _ADMIN):
    return _driver_page(request, {}, True, [])


@router.post("/drivers")
def drivers_create(request: Request, driver_id: str = Form(""), full_name: str = Form(""),
                   license_number: str = Form(""), phone: str = Form(""), user: dict = _ADMIN):
    f = DriverForm(driver_id.strip(), full_name, license_number.strip(), phone.strip())
    result = ca.create_driver(get_db(request), f)
    if not result.ok:
        return _driver_page(request, _driver_dict(f), True, [result.message], _status(result))
    return _done(request, result, "/admin/drivers")


@router.get("/drivers/{driver_id}/edit")
def drivers_edit(request: Request, driver_id: str, user: dict = _ADMIN):
    row = ca.get_driver(get_db(request), driver_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tài xế {driver_id}.")
    return _driver_page(request, row, False, [])


@router.post("/drivers/{driver_id}/delete")
def drivers_delete(request: Request, driver_id: str, user: dict = _ADMIN):
    result = ca.delete_driver(get_db(request), driver_id, request.app.state.clock(), _first_month(request))
    return _done(request, result, "/admin/drivers")


@router.post("/drivers/{driver_id}")
def drivers_update(request: Request, driver_id: str, full_name: str = Form(""), license_number: str = Form(""),
                   phone: str = Form(""), user: dict = _ADMIN):
    f = DriverForm(driver_id, full_name, license_number.strip(), phone.strip())
    result = ca.update_driver(get_db(request), f)
    if not result.ok:
        return _driver_page(request, _driver_dict(f), False, [result.message], _status(result))
    return _done(request, result, "/admin/drivers")


# -------------------------------------------------------------- vehicles
def _vehicle_page(request: Request, form: dict, is_new: bool, errors: list[str], status: int = 200):
    return render(request, "admin/vehicle_form.html", {"form": form, "is_new": is_new, "errors": errors},
                  status_code=status)


def _vehicle_dict(f: VehicleForm) -> dict:
    return {"vehicle_id": f.vehicle_id, "driver_id": f.driver_id, "license_plate": f.license_plate,
            "model": f.model, "color": f.color}


@router.get("/vehicles")
def vehicles_list(request: Request, user: dict = _ADMIN):
    return render(request, "admin/vehicles.html", {"rows": ca.list_vehicles(get_db(request)), "plate": None,
                                                   "hits": None})


@router.get("/vehicles/by-plate")
def vehicles_by_plate(request: Request, plate: str = "", user: dict = _ADMIN):
    hits = ca.find_vehicle_by_plate(get_db(request), plate)
    return render(request, "admin/vehicles.html", {"rows": ca.list_vehicles(get_db(request)),
                                                   "plate": plate.strip(), "hits": hits})


@router.get("/vehicles/new")
def vehicles_new(request: Request, user: dict = _ADMIN):
    return _vehicle_page(request, {}, True, [])


@router.post("/vehicles")
def vehicles_create(request: Request, vehicle_id: str = Form(""), driver_id: str = Form(""),
                    license_plate: str = Form(""), model: str = Form(""), color: str = Form(""),
                    user: dict = _ADMIN):
    f = VehicleForm(vehicle_id.strip(), driver_id.strip(), license_plate.strip(), model, color)
    result = ca.create_vehicle(get_db(request), f)
    if not result.ok:
        return _vehicle_page(request, _vehicle_dict(f), True, [result.message], _status(result))
    return _done(request, result, "/admin/vehicles")


@router.get("/vehicles/{vehicle_id}/edit")
def vehicles_edit(request: Request, vehicle_id: str, user: dict = _ADMIN):
    row = ca.get_vehicle(get_db(request), vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy xe {vehicle_id}.")
    return _vehicle_page(request, row, False, [])


@router.post("/vehicles/{vehicle_id}/delete")
def vehicles_delete(request: Request, vehicle_id: str, user: dict = _ADMIN):
    return _done(request, ca.delete_vehicle(get_db(request), vehicle_id), "/admin/vehicles")


@router.post("/vehicles/{vehicle_id}")
def vehicles_update(request: Request, vehicle_id: str, driver_id: str = Form(""), license_plate: str = Form(""),
                    model: str = Form(""), color: str = Form(""), user: dict = _ADMIN):
    f = VehicleForm(vehicle_id, driver_id.strip(), license_plate.strip(), model, color)
    result = ca.update_vehicle(get_db(request), f)
    if not result.ok:
        return _vehicle_page(request, _vehicle_dict(f), False, [result.message], _status(result))
    return _done(request, result, "/admin/vehicles")


# ------------------------------------------------------------ promotions
def _promo_page(request: Request, form: dict, is_new: bool, errors: list[str], status: int = 200):
    return render(request, "admin/promotion_form.html", {"form": form, "is_new": is_new, "errors": errors},
                  status_code=status)


def _promo_from_raw(code: str, description: str, discount_percent: str, max_discount: str, min_fare: str,
                    cities: str, usage_limit: str, valid_from: str, valid_to: str):
    """Chuyển chuỗi trên form thành PromoForm; lỗi định dạng trả về danh sách lỗi (chưa đến bước validate_promo)."""
    errs: list[str] = []

    def num(raw: str, cast, label: str):
        try:
            return cast((raw or "").strip())
        except ValueError:
            errs.append(f"{label} không phải số hợp lệ.")
            return None

    pct = num(discount_percent, int, "Phần trăm giảm")
    mx = num(max_discount, float, "Mức giảm tối đa")
    mf = num(min_fare, float, "Cước tối thiểu")
    lim = num(usage_limit, int, "Giới hạn lượt dùng")
    vf, vt = _parse_dt(valid_from), _parse_dt(valid_to)
    if vf is None or vt is None:
        errs.append("Thời gian hiệu lực không hợp lệ.")
    city_set = {c for c in re.split(r"[,\s]+", (cities or "").upper()) if c}
    raw = {"promo_code": code, "description": description, "discount_percent": discount_percent,
           "max_discount": max_discount, "min_fare": min_fare, "cities": ", ".join(sorted(city_set)),
           "usage_limit": usage_limit, "valid_from": valid_from, "valid_to": valid_to}
    if errs:
        return None, errs, raw
    return PromoForm(code, description, pct, mx, mf, city_set, lim, vf, vt), [], raw


@router.get("/promotions")
def promotions_list(request: Request, user: dict = _ADMIN):
    return render(request, "admin/promotions.html", {"rows": ca.list_promos(get_db(request))})


@router.get("/promotions/new")
def promotions_new(request: Request, user: dict = _ADMIN):
    return _promo_page(request, {"discount_percent": "10", "usage_limit": "100"}, True, [])


@router.post("/promotions")
def promotions_create(request: Request, promo_code: str = Form(""), description: str = Form(""),
                      discount_percent: str = Form(""), max_discount: str = Form(""), min_fare: str = Form(""),
                      cities: str = Form(""), usage_limit: str = Form(""), valid_from: str = Form(""),
                      valid_to: str = Form(""), user: dict = _ADMIN):
    f, errs, raw = _promo_from_raw(promo_code.strip().upper(), description, discount_percent, max_discount,
                                   min_fare, cities, usage_limit, valid_from, valid_to)
    if f is None:
        return _promo_page(request, raw, True, errs, 400)
    result = ca.create_promo(get_db(request), f)
    if not result.ok:
        return _promo_page(request, raw, True, [result.message], _status(result))
    return _done(request, result, "/admin/promotions")


@router.post("/promotions/{promo_code}/cities/add")
def promotions_city_add(request: Request, promo_code: str, city: str = Form(""), user: dict = _ADMIN):
    return _done(request, ca.add_promo_city(get_db(request), promo_code, city), "/admin/promotions")


@router.post("/promotions/{promo_code}/cities/remove")
def promotions_city_remove(request: Request, promo_code: str, city: str = Form(""), user: dict = _ADMIN):
    return _done(request, ca.remove_promo_city(get_db(request), promo_code, city), "/admin/promotions")


@router.get("/promotions/{promo_code}/edit")
def promotions_edit(request: Request, promo_code: str, user: dict = _ADMIN):
    row = ca.get_promo(get_db(request), promo_code)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy mã khuyến mãi {promo_code}.")
    form = dict(row)
    form["cities"] = ", ".join(sorted(row.get("cities") or ()))
    form["valid_from"] = _dt_input(row.get("valid_from"))
    form["valid_to"] = _dt_input(row.get("valid_to"))
    return _promo_page(request, form, False, [])


@router.post("/promotions/{promo_code}/delete")
def promotions_delete(request: Request, promo_code: str, user: dict = _ADMIN):
    return _done(request, ca.delete_promo(get_db(request), promo_code), "/admin/promotions")


@router.post("/promotions/{promo_code}")
def promotions_update(request: Request, promo_code: str, description: str = Form(""),
                      discount_percent: str = Form(""), max_discount: str = Form(""), min_fare: str = Form(""),
                      usage_limit: str = Form(""), valid_from: str = Form(""), valid_to: str = Form(""),
                      user: dict = _ADMIN):
    f, errs, raw = _promo_from_raw(promo_code, description, discount_percent, max_discount, min_fare, "",
                                   usage_limit, valid_from, valid_to)
    if f is None:
        return _promo_page(request, raw, False, errs, 400)
    result = ca.update_promo(get_db(request), f)
    if not result.ok:
        current = ca.get_promo(get_db(request), promo_code)
        raw["cities"] = ", ".join(sorted((current or {}).get("cities") or ()))
        return _promo_page(request, raw, False, [result.message], _status(result))
    return _done(request, result, "/admin/promotions")
