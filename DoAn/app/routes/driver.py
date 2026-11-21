"""Tài xế: bật/tắt nhận chuyến, chuyến chờ theo khu vực, nhận chuyến. driver_id luôn lấy từ phiên đăng nhập."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import RedirectResponse

from config import AREAS
from domain.auth import DRIVER
from domain.tz import fmt_vn, to_date, vn_date
from routes.deps import flash_trace, get_db, pop_trace_event, render, require_role, set_flash
from services import driver_presence, reports, rides_flow
from services.result import ActionResult

router = APIRouter()
_DRIVER = Depends(require_role(DRIVER))


def _float_or_none(raw: str, label: str) -> tuple[float | None, str | None]:
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None, None
    try:
        return float(raw), None
    except ValueError:
        return None, f"{label} không phải số."


def _home(request: Request, user: dict, errors: list[str] | None = None, status: int = 200, form: dict | None = None):
    db = get_db(request)
    driver_id = user["ref_id"]
    driver = db.one("B03_driver_get", [driver_id])
    if driver is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ tài xế.")
    areas = driver_presence.find_area_rows(db, driver_id)
    ctx = {"driver": driver, "areas": areas, "area_config": AREAS, "errors": errors or [],
           "form": form or {"city": "HCM", "district": "Q1", "plate": "", "lat": "", "lng": ""},
           "event": pop_trace_event(request) if status == 200 else None}
    return render(request, "driver/home.html", ctx, status_code=status)


@router.get("/driver")
def driver_home(request: Request, user: dict = _DRIVER):
    return _home(request, user)


@router.post("/driver/online")
def driver_online(request: Request, city: str = Form(""), district: str = Form(""), plate: str = Form(""),
                  lat: str = Form(""), lng: str = Form(""), user: dict = _DRIVER):
    form = {"city": city.strip(), "district": district.strip(), "plate": plate.strip(), "lat": lat, "lng": lng}
    lat_v, err_lat = _float_or_none(lat, "Vĩ độ")
    lng_v, err_lng = _float_or_none(lng, "Kinh độ")
    errs = [e for e in (err_lat, err_lng) if e]
    if errs:
        return _home(request, user, errs, 400, form)
    result = driver_presence.go_online(get_db(request), user["ref_id"], form["city"], form["district"],
                                       form["plate"], lat_v, lng_v, request.app.state.clock())
    if not result.ok and result.code in ("invalid_input", "not_found"):
        return _home(request, user, [result.message], 400, form)
    event = None
    if result.ok and result.code == "ok" and result.data.get("was_offline") and result.data.get("location"):
        event = "driver_online"  # đủ drivers, drivers_by_area, driver_locations nên áp ma trận ghi
    return _done(request, result, "/driver", event)


@router.post("/driver/offline")
def driver_offline(request: Request, user: dict = _DRIVER):
    result = driver_presence.go_offline(get_db(request), user["ref_id"], request.app.state.clock())
    return _done(request, result, "/driver")


def _done(request: Request, result: ActionResult, location: str, event: str | None = None):
    """PRG (D14): flash + giữ trace của thao tác rồi redirect."""
    set_flash(request, result.ok, result.message)
    flash_trace(request, event)
    return RedirectResponse(location, status_code=303)


@router.get("/driver/waiting")
def driver_waiting(request: Request, city: str | None = None, district: str | None = None,
                   day: str | None = None, user: dict = _DRIVER):
    db = get_db(request)
    if not city or not district:
        areas = driver_presence.find_area_rows(db, user["ref_id"])
        city = city or (areas[0]["city"] if areas else "HCM")
        here = [a["district"] for a in areas if a["city"] == city]
        district = district or (here[0] if here else (AREAS[city][0] if city in AREAS else "Q1"))
    if city not in AREAS or district not in AREAS[city]:
        raise HTTPException(status_code=400, detail="Thành phố hoặc quận không hợp lệ.")
    if day:
        try:
            day_v: date = to_date(day)
        except ValueError:
            raise HTTPException(status_code=400, detail="Ngày không hợp lệ (cần YYYY-MM-DD).")
    else:
        day_v = vn_date(request.app.state.clock())
    rides = driver_presence.waiting_rides(db, city, district, day_v)
    return render(request, "driver/waiting.html", {"city": city, "district": district, "day": day_v.isoformat(),
                                                   "areas": AREAS, "rides": rides, "fmt": fmt_vn})


@router.post("/rides/{ride_id}/accept")
def accept(request: Request, ride_id: str, user: dict = _DRIVER):
    # driver_id chỉ lấy từ phiên đăng nhập, bỏ qua mọi giá trị do form gửi lên
    result = rides_flow.accept_ride(get_db(request), ride_id, user["ref_id"], request.app.state.clock())
    if result.code == "not_found":
        raise HTTPException(status_code=404, detail=result.message)
    if result.ok:
        return _done(request, result, f"/rides/{ride_id}", "accept" if result.code == "ok" else None)
    return _done(request, result, "/driver")


@router.post("/driver/location")
def driver_location(request: Request, lat: str = Form(""), lng: str = Form(""), speed: str = Form(""),
                    user: dict = _DRIVER):
    """Ghi điểm GPS của CHÍNH tài xế đăng nhập (driver_id từ phiên, bỏ qua giá trị form). Tốc độ bỏ trống thì là 0."""
    lat_v, err_lat = _float_or_none(lat, "Vĩ độ")
    lng_v, err_lng = _float_or_none(lng, "Kinh độ")
    speed_v, err_speed = _float_or_none(speed, "Tốc độ")
    errs = [e for e in (err_lat, err_lng, err_speed) if e]
    if errs:
        set_flash(request, False, " ".join(errs))
        return RedirectResponse("/driver", status_code=303)
    result = reports.record_location(get_db(request), user["ref_id"], lat_v, lng_v, speed_v or 0.0,
                                     request.app.state.clock())
    if result.code == "not_found":
        raise HTTPException(status_code=404, detail=result.message)
    return _done(request, result, "/driver")
