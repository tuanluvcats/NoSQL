"""Lịch sử, thu nhập, báo cáo doanh thu, khu vực, GPS và xuất CSV (9.3, 9.4).

Phân quyền: khách chỉ xem lịch sử của MÌNH (customer_id lấy từ phiên, bỏ qua tham số lạ), tài xế chỉ xem thu nhập và
đánh giá của MÌNH, báo cáo/xuất CSV/lộ trình chỉ ADMIN (gồm OPERATOR). Ngày mặc định là hôm nay theo +07."""
from __future__ import annotations

import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.responses import Response

from config import AREAS, PAYMENT_METHODS
from domain.auth import ADMIN, CUSTOMER, DRIVER
from domain.tz import month_label, parse_day, shift_month, vn_date, yyyymm as month_of
from routes.deps import get_db, render, require_role
from services import reports

router = APIRouter()
_ADMIN = Depends(require_role(ADMIN))
_CUSTOMER = Depends(require_role(CUSTOMER))
_DRIVER = Depends(require_role(DRIVER))

_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
SAMPLE_HINT = "Dữ liệu mẫu: 04/10/2026"


def _day(raw: str | None, default: date, label: str = "Ngày") -> date:
    if raw is None or not raw.strip():
        return default
    try:
        return parse_day(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{label} không hợp lệ (cần dạng ngày/tháng/năm, ví dụ 04/10/2026).")


def _opt_day(raw: str | None, label: str) -> date | None:
    return _day(raw, None, label) if raw and raw.strip() else None  # type: ignore[arg-type]


def _city(raw: str | None) -> str:
    city = (raw or "HCM").strip()
    if city not in AREAS:
        raise HTTPException(status_code=400, detail="Thành phố không hợp lệ.")
    return city


def _ident(raw: str | None, label: str) -> str:
    value = (raw or "").strip()
    if not _ID.match(value):
        raise HTTPException(status_code=400, detail=f"{label} không hợp lệ.")
    return value


def _today(request: Request) -> date:
    return vn_date(request.app.state.clock())


def _csv_response(text: str, filename: str) -> Response:
    return Response(content=text.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ------------------------------------------------------------------ khách
@router.get("/customer/rides")
def customer_rides(request: Request, date_from: str | None = Query(None, alias="from"),
                   date_to: str | None = Query(None, alias="to"), user: dict = _CUSTOMER):
    d_from, d_to = _opt_day(date_from, "Từ ngày"), _opt_day(date_to, "Đến ngày")
    if d_from and d_to and d_from > d_to:
        raise HTTPException(status_code=400, detail="Từ ngày phải trước hoặc bằng đến ngày.")
    rows = reports.customer_history(get_db(request), user["ref_id"], d_from, d_to)  # chỉ của chính mình
    return render(request, "customer/history.html", {"rows": rows, "date_from": d_from.isoformat() if d_from else "",
                                                     "date_to": d_to.isoformat() if d_to else ""})


# ------------------------------------------------------------------ tài xế
def _month(raw: str | None, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    s = raw.strip()
    if not re.fullmatch(r"\d{6}", s) or not 1 <= int(s[4:]) <= 12 or not 2000 <= int(s[:4]) <= 2100:
        raise HTTPException(status_code=400, detail="Tháng không hợp lệ (cần YYYYMM, ví dụ 202610).")
    return int(s)


@router.get("/driver/income")
def driver_income(request: Request, yyyymm: str | None = None, user: dict = _DRIVER):
    current = month_of(request.app.state.clock())
    month = _month(yyyymm, current)
    data = reports.driver_month(get_db(request), user["ref_id"], month)  # chỉ của chính tài xế đăng nhập
    first = request.app.state.settings.first_month
    prev_m, next_m = shift_month(month, -1), shift_month(month, 1)
    prev_m = prev_m if prev_m >= first else None
    next_m = next_m if next_m <= current else None
    return render(request, "driver/income.html", {
        "month": month, "month_label": month_label(month),
        "prev_month": prev_m, "prev_label": month_label(prev_m) if prev_m else "",
        "next_month": next_m, "next_label": month_label(next_m) if next_m else "",
        "income": data["income"], "rides": data["rides"], "hint": SAMPLE_HINT})


@router.get("/driver/ratings")
def driver_ratings(request: Request, user: dict = _DRIVER):
    data = reports.driver_ratings(get_db(request), user["ref_id"])
    return render(request, "driver/ratings.html", data)


# ------------------------------------------------------------------ ADMIN
@router.get("/admin/reports")
def admin_reports(request: Request, city: str | None = None, day: str | None = None, district: str | None = None,
                  user: dict = _ADMIN):
    city_v = _city(city)
    day_v = _day(day, _today(request))
    district_v = (district or AREAS[city_v][0]).strip()
    if district_v not in AREAS[city_v]:
        raise HTTPException(status_code=400, detail="Quận không thuộc thành phố đã chọn.")
    db = get_db(request)
    ctx = {"city": city_v, "day": day_v.isoformat(), "district": district_v, "areas": AREAS,
           "revenue": reports.revenue_day(db, city_v, day_v), "week": reports.revenue_7days(db, city_v, day_v),
           "stats": reports.area_day_stats(db, city_v, district_v, day_v), "methods": PAYMENT_METHODS,
           "hint": SAMPLE_HINT, "today": day_v}
    return render(request, "admin/reports.html", ctx)


@router.get("/admin/areas")
def admin_areas(request: Request, city: str | None = None, districts: list[str] = Query(default=[]),
                user: dict = _ADMIN):
    city_v = _city(city)
    chosen = [d for d in districts if d in AREAS[city_v]] or list(AREAS[city_v])
    rows = reports.area_drivers(get_db(request), city_v, chosen)
    return render(request, "admin/areas.html", {"city": city_v, "areas": AREAS, "chosen": chosen, "rows": rows})


@router.get("/admin/export/history.csv")
def export_history(request: Request, customer_id: str = "", user: dict = _ADMIN):
    cid = _ident(customer_id, "Mã khách")
    db = get_db(request)
    if db.one("B02_customer_get", [cid]) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng.")
    return _csv_response(reports.history_csv(reports.customer_history(db, cid)), f"history_{cid}.csv")


@router.get("/admin/export/payments.csv")
def export_payments(request: Request, city: str | None = None, day: str | None = None, user: dict = _ADMIN):
    city_v = _city(city)
    day_v = _day(day, _today(request))
    rows = get_db(request).rows("B15_payments_day", [city_v, day_v])
    return _csv_response(reports.payments_csv(rows), f"payments_{city_v}_{day_v.isoformat()}.csv")


@router.get("/admin/drivers/{driver_id}/track")
def driver_track_page(request: Request, driver_id: str, day: str | None = None, user: dict = _ADMIN):
    did = _ident(driver_id, "Mã tài xế")
    day_v = _day(day, _today(request))
    db = get_db(request)
    driver = db.one("B03_driver_get", [did])
    if driver is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài xế.")
    data = reports.driver_track(db, did, day_v)
    return render(request, "admin/track.html", {"driver": driver, "day": day_v.isoformat(), "hint": SAMPLE_HINT, **data})
