"""Bắt đầu, hoàn thành, hủy chuyến. Danh tính (driver_id, customer_id) luôn lấy từ phiên đăng nhập, không từ form."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import RedirectResponse

from domain.auth import CUSTOMER, DRIVER, effective_role
from routes.deps import current_user, flash_trace, get_db, require_role, set_flash
from routes.driver import _float_or_none
from services import rating, rides_flow
from services.result import ActionResult

router = APIRouter()
_DRIVER = Depends(require_role(DRIVER))
_CUSTOMER = Depends(require_role(CUSTOMER))


def _finish(request: Request, user: dict, ride_id: str, result: ActionResult, event: str | None):
    """not_found -> 404, forbidden -> 403 (không lộ gì thêm); còn lại PRG (D14): flash + giữ trace rồi redirect."""
    if result.code == "not_found":
        raise HTTPException(status_code=404, detail=result.message)
    if result.code == "forbidden":
        raise HTTPException(status_code=403, detail=result.message)
    set_flash(request, result.ok, result.message)
    flash_trace(request, event if result.ok and result.code == "ok" else None)
    if not result.ok and effective_role(user.get("role")) == DRIVER:
        return RedirectResponse("/driver", status_code=303)
    return RedirectResponse(f"/rides/{ride_id}", status_code=303)


def _coords(request: Request, lat: str, lng: str, ride_id: str):
    lat_v, err_lat = _float_or_none(lat, "Vĩ độ")
    lng_v, err_lng = _float_or_none(lng, "Kinh độ")
    errs = [e for e in (err_lat, err_lng) if e]
    if errs:
        set_flash(request, False, " ".join(errs))
        return None, None, RedirectResponse(f"/rides/{ride_id}", status_code=303)
    return lat_v, lng_v, None


@router.post("/rides/{ride_id}/start")
def start(request: Request, ride_id: str, lat: str = Form(""), lng: str = Form(""), user: dict = _DRIVER):
    lat_v, lng_v, redirect = _coords(request, lat, lng, ride_id)
    if redirect is not None:
        return redirect
    result = rides_flow.start_ride(get_db(request), ride_id, user["ref_id"], lat_v, lng_v,
                                   request.app.state.clock())
    # ma trận 'start' đòi driver_locations: chỉ áp khi tài xế có gửi tọa độ
    return _finish(request, user, ride_id, result, "start" if lat_v is not None and lng_v is not None else None)


@router.post("/rides/{ride_id}/complete")
def complete(request: Request, ride_id: str, drop_district: str = Form(""), lat: str = Form(""),
             lng: str = Form(""), user: dict = _DRIVER):
    lat_v, lng_v, redirect = _coords(request, lat, lng, ride_id)
    if redirect is not None:
        return redirect
    result = rides_flow.complete_ride(get_db(request), ride_id, user["ref_id"], drop_district.strip(),
                                      lat_v, lng_v, request.app.state.clock())
    return _finish(request, user, ride_id, result, "complete")


@router.post("/rides/{ride_id}/cancel")
def cancel(request: Request, ride_id: str, reason: str = Form(""), user: dict = Depends(current_user)):
    actor = {"role": effective_role(user.get("role")), "ref_id": user.get("ref_id"), "username": user.get("username")}
    result = rides_flow.cancel_ride(get_db(request), ride_id, actor, reason, request.app.state.clock())
    return _finish(request, user, ride_id, result, "cancel")


@router.post("/rides/{ride_id}/rate")
def rate(request: Request, ride_id: str, stars: str = Form(""), comment: str = Form(""),
         tags: list[str] = Form(default=[]), user: dict = _CUSTOMER):
    """Khách đánh giá chuyến của chính mình (customer_id lấy từ phiên). Số sao không phải số nguyên thì coi là 0."""
    try:
        stars_v = int(stars.strip())
    except ValueError:
        stars_v = 0
    result = rating.rate_ride(get_db(request), ride_id, user["ref_id"], stars_v, comment, tags,
                              request.app.state.clock())
    return _finish(request, user, ride_id, result, "rate")
