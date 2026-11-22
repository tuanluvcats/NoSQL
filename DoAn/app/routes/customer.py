"""Khách hàng: đặt xe, báo giá, xem chi tiết chuyến."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import RedirectResponse

from config import AREAS, PAYMENT_METHODS, RATING_TAGS
from domain.auth import CUSTOMER, can_cancel_ride, can_view_ride
from domain.ids import new_ride_id
from domain.tz import fmt_vn
from routes.deps import current_user, flash_trace, get_db, pop_trace_event, render, require_role, set_flash
from services import booking, reports
from services.booking import BookingForm

router = APIRouter()
_CUSTOMER = Depends(require_role(CUSTOMER))


def _page(request: Request, form: dict, errors: list[str], status: int = 200, quote=None, result=None,
          price_changed: bool = False):
    ctx = {"form": form, "errors": errors, "areas": AREAS, "methods": PAYMENT_METHODS, "quote": quote,
           "result": result, "lwt_current": result.current if result is not None and not result.ok else None,
           "promo_message": booking.promo_reason(quote.promo_error) if quote is not None else None,
           "price_changed": price_changed}
    return render(request, "customer/book.html", ctx, status_code=status)


def _parse(ride_id: str, city: str, district: str, pickup_address: str, destination_address: str,
           distance_km: str, payment_method: str, promo_code: str) -> BookingForm:
    try:
        distance = float((distance_km or "").replace(",", ".").strip())
    except ValueError:
        distance = 0.0  # ngoài khoảng 0.1..200 nên validate_booking sẽ báo lỗi quãng đường
    return BookingForm(ride_id=ride_id.strip(), city=city.strip(), district=district.strip(),
                       pickup_address=pickup_address, destination_address=destination_address,
                       distance_km=distance, payment_method=payment_method.strip(),
                       promo_code=promo_code.strip().upper() or None)


def _as_dict(f: BookingForm, raw_distance: str) -> dict:
    return {"ride_id": f.ride_id, "city": f.city, "district": f.district, "pickup_address": f.pickup_address,
            "destination_address": f.destination_address, "distance_km": raw_distance,
            "payment_method": f.payment_method, "promo_code": f.promo_code or ""}


def _same_price(raw: str, payable: float) -> bool:
    """Giá khách đã thấy (ô ẩn quoted_payable) còn khớp giá tính lại không; sai định dạng coi như đã đổi."""
    try:
        return abs(float(raw.strip()) - float(payable)) <= 0.5
    except ValueError:
        return False


@router.get("/customer/book")
def book_form(request: Request, user: dict = _CUSTOMER):
    ride_id = new_ride_id(request.app.state.clock())
    form = {"ride_id": ride_id, "city": "HCM", "district": "Q1", "pickup_address": "",
            "destination_address": "", "distance_km": "", "payment_method": "CASH", "promo_code": ""}
    return _page(request, form, [])


@router.post("/customer/book/quote")
def book_quote(request: Request, ride_id: str = Form(""), city: str = Form(""), district: str = Form(""),
               pickup_address: str = Form(""), destination_address: str = Form(""),
               distance_km: str = Form(""), payment_method: str = Form(""), promo_code: str = Form(""),
               user: dict = _CUSTOMER):
    f = _parse(ride_id, city, district, pickup_address, destination_address, distance_km,
               payment_method, promo_code)
    form = _as_dict(f, distance_km)
    errors = booking.validate_booking(f)
    if errors:
        return _page(request, form, errors, 400)
    q = booking.quote(get_db(request), f, request.app.state.clock())
    return _page(request, form, [], 200, quote=q)


@router.post("/customer/book")
def book_submit(request: Request, ride_id: str = Form(""), city: str = Form(""), district: str = Form(""),
                pickup_address: str = Form(""), destination_address: str = Form(""),
                distance_km: str = Form(""), payment_method: str = Form(""), promo_code: str = Form(""),
                quoted_payable: str = Form(""), user: dict = _CUSTOMER):
    f = _parse(ride_id, city, district, pickup_address, destination_address, distance_km,
               payment_method, promo_code)
    form = _as_dict(f, distance_km)
    db, now = get_db(request), request.app.state.clock()
    if quoted_payable.strip() and not booking.validate_booking(f):
        q = booking.quote(db, f, now)  # chỉ đọc B16, một lần mỗi lần đặt, không theo dòng
        if not _same_price(quoted_payable, q.payable):
            return _page(request, form, [], 409, quote=q, price_changed=True)
    result = booking.book_ride(db, user["ref_id"], f, now)
    if not result.ok:
        return _page(request, form, [result.message], 400, result=result)
    set_flash(request, True, result.message)
    flash_trace(request, "book" if result.code == "ok" else None)
    return RedirectResponse(f"/rides/{result.ride_id}", status_code=303)


@router.get("/rides/{ride_id}")
def ride_detail(request: Request, ride_id: str, user: dict = Depends(current_user)):
    ride = reports.ride_detail(get_db(request), ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyến đi.")
    if not can_view_ride(user.get("role"), user.get("ref_id"), ride):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem chuyến này.")
    history = ride["history"]  # [(thời điểm +07, trạng thái)] đã sắp theo thời gian
    event = pop_trace_event(request)  # sự kiện do route POST đặt (book/accept/start/complete/cancel)
    can_cancel = can_cancel_ride(user.get("role"), user.get("ref_id"), ride)
    return render(request, "rides/detail.html", {"ride": ride, "history": history, "fmt": fmt_vn, "event": event,
                                                 "can_cancel": can_cancel, "areas": AREAS,
                                                 "rating_tags": RATING_TAGS})
