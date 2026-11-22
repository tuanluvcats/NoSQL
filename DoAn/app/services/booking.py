"""Đặt xe (9.3): giữ lượt khuyến mãi bằng LWT optimistic, ghi `rides` bằng IF NOT EXISTS rồi mới ghi bảng phụ.

Thứ tự (D2): giữ lượt `promotions` (LWT `IF used_count = n`) -> INSERT rides IF NOT EXISTS ->
rides_by_customer -> rides_by_area_date. Nếu ride không applied (gửi trùng) thì trả lượt.
Crash giữa hai bước chỉ làm thất thoát một lượt (thận trọng), không bao giờ vượt `usage_limit`.
"""
from __future__ import annotations

import logging

from dataclasses import dataclass
from datetime import datetime

from cassandra import WriteTimeout

from config import AREAS, PAYMENT_METHODS
from domain.ids import is_new_ride_id
from domain.money import discount_of, fare_of, normalize_distance
from domain.promo import promo_error
from domain.tz import truncate_ms, vn_date
from services.result import ActionResult

log = logging.getLogger(__name__)

ADDRESS_MAX = 200
_PROMO_REASONS = {
    "not_found": "Mã khuyến mãi không tồn tại.",
    "not_started": "Mã khuyến mãi chưa đến thời gian áp dụng.",
    "expired": "Mã khuyến mãi đã hết hạn.",
    "city": "Mã khuyến mãi không áp dụng cho thành phố này.",
    "min_fare": "Cước chưa đạt mức tối thiểu để dùng mã khuyến mãi.",
}


@dataclass
class BookingForm:
    ride_id: str
    city: str
    district: str
    pickup_address: str
    destination_address: str
    distance_km: float
    payment_method: str
    promo_code: str | None = None


@dataclass
class Quote:
    fare: float
    discount: float
    payable: float
    promo_error: str | None


@dataclass
class PromoReservation:
    ok: bool
    discount: float
    error: str | None


def _code(promo_code: str | None) -> str | None:
    return (promo_code or "").strip().upper() or None


def validate_booking(f: BookingForm) -> list[str]:
    errs: list[str] = []
    if not is_new_ride_id(f.ride_id):
        errs.append("Mã chuyến không hợp lệ, hãy mở lại trang đặt xe.")
    if f.city not in AREAS or f.district not in AREAS.get(f.city, ()):
        errs.append("Thành phố hoặc quận không hợp lệ.")
    pickup = (f.pickup_address or "").strip()
    dest = (f.destination_address or "").strip()
    for label, addr in (("Điểm đón", pickup), ("Điểm đến", dest)):
        if not 1 <= len(addr) <= ADDRESS_MAX:
            errs.append(f"{label} phải dài từ 1 đến {ADDRESS_MAX} ký tự.")
    if pickup and dest and pickup == dest:
        errs.append("Điểm đón và điểm đến phải khác nhau.")
    try:
        normalize_distance(f.distance_km)
    except (ValueError, TypeError):
        errs.append("Quãng đường phải trong khoảng 0.1 đến 200 km.")
    if f.payment_method not in PAYMENT_METHODS:
        errs.append("Phương thức thanh toán không hợp lệ.")
    return errs


def quote(db, f: BookingForm, now: datetime) -> Quote:
    """Chỉ đọc B16, không giữ lượt."""
    fare = fare_of(normalize_distance(f.distance_km))
    code = _code(f.promo_code)
    if not code:
        return Quote(fare, 0.0, fare, None)
    promo = db.one("B16_promo_get", [code])
    err = promo_error(promo, f.city, fare, now)
    if err:
        return Quote(fare, 0.0, fare, err)
    discount = discount_of(fare, promo["discount_percent"], promo["max_discount"])
    return Quote(fare, discount, fare - discount, None)


def reserve_promo(db, code: str, city: str, fare: float, now: datetime, max_attempts: int = 20) -> PromoReservation:
    """Vòng LWT `IF used_count = n`. WriteTimeout (CAS) thì đọc lại rồi tiếp tục: có thể mất một lượt nhưng không vượt giới hạn."""
    for _ in range(max_attempts):
        promo = db.one("B16_promo_get", [code])
        err = promo_error(promo, city, fare, now)
        if err == "exhausted":
            return PromoReservation(False, 0.0, "promo_exhausted")
        if err:
            return PromoReservation(False, 0.0, "promo_invalid:" + err)
        n = promo["used_count"] or 0
        try:
            res = db.lwt("T07_promo_use", [n + 1, code, n])
        except WriteTimeout:
            continue
        if res.applied:
            return PromoReservation(True, discount_of(fare, promo["discount_percent"], promo["max_discount"]), None)
    return PromoReservation(False, 0.0, "promo_busy")


def release_promo(db, code: str, max_attempts: int = 20) -> bool:
    """Trả lượt. WriteTimeout thì dừng (không thử lại): ghi có thể đã áp dụng, thử lại sẽ trả dư và vượt giới hạn."""
    for _ in range(max_attempts):
        promo = db.one("B16_promo_get", [code])
        n = (promo or {}).get("used_count") or 0
        if promo is None or n <= 0:
            return False
        try:
            res = db.lwt("T07_promo_use", [n - 1, code, n])
        except WriteTimeout:
            return False
        if res.applied:
            return True
    return False


def _duplicate(customer_id: str, ride_id: str, existing: dict | None) -> ActionResult:
    if (existing or {}).get("customer_id") == customer_id:
        return ActionResult(True, "duplicate_ok", "Chuyến này đã được đặt trước đó, không tạo thêm.",
                            ride_id=ride_id, current=existing)
    return ActionResult(False, "duplicate", "Mã chuyến đã được dùng bởi yêu cầu khác.", ride_id=ride_id,
                        current=existing)


def book_ride(db, customer_id: str, f: BookingForm, now: datetime) -> ActionResult:
    errs = validate_booking(f)
    if errs:
        return ActionResult(False, "invalid_input", " ".join(errs), data={"errors": errs})
    cust = db.one("B02_customer_get", [customer_id])
    if cust is None:
        return ActionResult(False, "not_found", "Không tìm thấy hồ sơ khách hàng.")
    distance = normalize_distance(f.distance_km)
    fare = fare_of(distance)
    now = truncate_ms(now)
    pickup = f.pickup_address.strip()
    dest = f.destination_address.strip()
    code = _code(f.promo_code)

    existing = db.one("B06_ride_get", [f.ride_id])
    if existing is not None:
        return _duplicate(customer_id, f.ride_id, existing)

    discount = 0.0
    if code:
        res = reserve_promo(db, code, f.city, fare, now)
        if not res.ok:
            if res.error == "promo_exhausted":
                return ActionResult(False, "promo_exhausted", "Mã khuyến mãi đã hết lượt.", data={"reason": "exhausted"})
            if res.error == "promo_busy":
                return ActionResult(False, "promo_busy", "Mã khuyến mãi đang được nhiều người dùng, hãy thử lại.",
                                    data={"reason": "busy"})
            reason = (res.error or "").split(":", 1)[-1]
            return ActionResult(False, "promo_invalid", _PROMO_REASONS.get(reason, "Mã khuyến mãi không hợp lệ."),
                                data={"reason": reason})
        discount = res.discount

    ride_date = vn_date(now)
    r = db.lwt("T04_ride_insert", [f.ride_id, customer_id, cust.get("full_name"), cust.get("phone"), f.city,
                                   f.district, pickup, dest, distance, fare, discount, code,
                                   f.payment_method, ride_date, now, {now: "REQUESTED"}])
    if not r.applied:
        if code:
            release_promo(db, code)
        return _duplicate(customer_id, f.ride_id, r.current)

    try:
        db.exec("T04_rbc_insert", [customer_id, ride_date, f.ride_id, pickup, dest, None, fare, "REQUESTED"])
        db.exec("T04_rad_insert", [f.city, f.district, ride_date, now, f.ride_id, customer_id, None, pickup, dest,
                                   fare, "REQUESTED", f.payment_method])
    except Exception:  # noqa: BLE001 - D10: không rollback, báo partial
        log.exception("Đặt chuyến %s: ghi bảng phụ lỗi", f.ride_id)
        return ActionResult(True, "partial", "Đã tạo chuyến nhưng một phần dữ liệu chưa đồng bộ, "
                            "quản trị viên sẽ đối soát lại.", ride_id=f.ride_id)
    return ActionResult(True, "ok", "Đã đặt xe thành công.", ride_id=f.ride_id,
                        data={"fare": fare, "discount": discount, "payable": fare - discount})
