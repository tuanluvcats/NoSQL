"""Công cụ quản trị: kiểm tra nhất quán, reconcile, backfill rated_at, giải phóng tài xế kẹt BUSY. Chỉ ADMIN/OPERATOR.

Mọi lệnh chạy qua CassandraDb nên đều có trong trace; thao tác sửa (POST) giữ trace qua PRG (D14)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse

from domain.auth import ADMIN
from routes.deps import flash_trace, get_db, render, require_role, set_flash
from services import consistency, rating

router = APIRouter(prefix="/admin/consistency")
_ADMIN = Depends(require_role(ADMIN))
_MAX_ID = 64


def _page(request: Request, extra: dict | None = None, status_code: int = 200):
    db = get_db(request)
    ctx = {"stuck": consistency.find_stuck_busy_drivers(db, request.app.state.clock()),
           "ride_id": "", "diffs": None, "driver_id": "", "area_problems": None}
    ctx.update(extra or {})
    return render(request, "admin/consistency.html", ctx, status_code=status_code)


def _done(request: Request, ok: bool, message: str):
    set_flash(request, ok, message)
    flash_trace(request)
    return RedirectResponse("/admin/consistency", status_code=303)


def _clean(value: str) -> str:
    return (value or "").strip()[:_MAX_ID]


@router.get("")
def consistency_page(request: Request, user: dict = _ADMIN):
    return _page(request)


@router.post("/check")
def check(request: Request, ride_id: str = Form(""), user: dict = _ADMIN):
    ride_id = _clean(ride_id)
    if not ride_id:
        return _page(request, {"error": "Hãy nhập mã chuyến."}, 400)
    return _page(request, {"ride_id": ride_id, "diffs": consistency.check_ride(get_db(request), ride_id)})


@router.post("/reconcile")
def reconcile(request: Request, ride_id: str = Form(""), user: dict = _ADMIN):
    ride_id = _clean(ride_id)
    db = get_db(request)
    if not ride_id:
        return _done(request, False, "Hãy nhập mã chuyến.")
    written = consistency.reconcile(db, ride_id)
    if not written:
        return _done(request, False, f"Không tìm thấy chuyến {ride_id}.")
    left = consistency.check_ride(db, ride_id)
    if left:
        return _done(request, False, f"Đã ghi lại {len(written)} bảng cho {ride_id} nhưng còn lệch {len(left)} chỗ.")
    return _done(request, True, f"Đã reconcile {ride_id} từ rides: ghi {', '.join(written)}.")


@router.post("/backfill")
def backfill(request: Request, user: dict = _ADMIN):
    n = rating.backfill_rated_at(get_db(request))
    return _done(request, True, f"Backfill rated_at: {n} chuyến được đánh dấu đã đánh giá.")


@router.post("/driver")
def driver(request: Request, driver_id: str = Form(""), action: str = Form("check_areas"), user: dict = _ADMIN):
    driver_id = _clean(driver_id)
    db = get_db(request)
    if not driver_id:
        return _done(request, False, "Hãy nhập mã tài xế.")
    if action == "release":
        result = consistency.release_stuck_driver(db, driver_id, request.app.state.clock())
        return _done(request, result.ok, result.message)
    if action != "check_areas":
        return _done(request, False, "Hành động không hợp lệ.")
    return _page(request, {"driver_id": driver_id, "area_problems": consistency.check_driver_areas(db, driver_id)})
