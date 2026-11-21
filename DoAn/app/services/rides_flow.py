"""Vòng đời chuyến đi: nhận chuyến LWT hai tầng (drivers trước, rides sau, thua thì trả tài xế), bắt đầu,
hoàn thành + thanh toán, hủy.

Bổ sung so với T05 (ghi README): giữ tài xế `AVAILABLE -> BUSY` bằng LWT trước, rồi LWT `rides`
`IF status = 'REQUESTED'`. Nếu thua ở `rides` thì trả tài xế về `AVAILABLE` (APP08) để không kẹt BUSY.

Bắt đầu / hoàn thành / hủy: LWT trên `rides` chạy trước, chỉ khi applied mới ghi bảng phụ; khóa của bảng phụ
luôn lấy từ dòng `rides` vừa đọc (D1), không lấy từ form. Hủy dùng `IF status = <trạng thái vừa đọc>` (D3).
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping

from config import AREAS
from domain.auth import can_cancel_ride, can_view_ride
from domain.rides import CANCELLABLE
from domain.tz import truncate_ms, vn_date, yyyymm
from services.booking import release_promo
from services.driver_presence import _valid_coords, find_area_rows, remove_from_all_areas
from services.result import ActionResult


def accept_ride(db, ride_id: str, driver_id: str, now: datetime) -> ActionResult:
    now = truncate_ms(now)
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return ActionResult(False, "not_found", "Không tìm thấy chuyến đi.", ride_id=ride_id)
    if ride.get("status") != "REQUESTED":
        return ActionResult(False, "invalid_transition", "Chuyến đã được nhận hoặc không còn ở trạng thái chờ.",
                            ride_id=ride_id,
                            current={"status": ride.get("status"), "driver_id": ride.get("driver_id")})
    areas = find_area_rows(db, driver_id, [ride["city"]])
    if not areas:
        return ActionResult(False, "driver_not_online",
                            "Bạn chưa bật nhận chuyến ở thành phố của chuyến này.", ride_id=ride_id)
    area = areas[0]

    claim = db.lwt("APP07_driver_claim", [driver_id])
    if not claim.applied:
        return ActionResult(False, "driver_not_available",
                            "Tài xế không ở trạng thái rảnh (AVAILABLE), không thể nhận chuyến.",
                            ride_id=ride_id, current=claim.current)

    r = db.lwt("T05_ride_accept", [driver_id, area.get("full_name"), area.get("vehicle_plate"), now,
                                   {now: "ACCEPTED"}, ride_id])
    if not r.applied:
        db.lwt("APP08_driver_release", [driver_id])  # thua ở rides: trả tài xế về AVAILABLE
        return ActionResult(False, "lwt_lost", "Chuyến vừa được tài xế khác nhận.", ride_id=ride_id,
                            current=r.current)

    try:
        db.exec("T05_rbc_accept", [driver_id, ride["customer_id"], ride["ride_date"], ride_id])
        db.exec("T05_rad_accept", [driver_id, ride["city"], ride["district"], ride["ride_date"],
                                   ride["requested_at"], ride_id])
        db.exec("T05_rdm_insert", [driver_id, yyyymm(ride["requested_at"]), ride["requested_at"], ride_id,
                                   ride["customer_id"], ride.get("pickup_address"), ride.get("destination_address"),
                                   ride.get("distance_km"), ride.get("fare"), "ACCEPTED"])
        remove_from_all_areas(db, driver_id)
    except Exception as e:  # noqa: BLE001 - D10: không rollback, báo partial
        return ActionResult(True, "partial", f"Đã nhận chuyến nhưng ghi bảng phụ lỗi ({type(e).__name__}). "
                            "Hãy dùng Kiểm tra nhất quán -> Reconcile.", ride_id=ride_id)
    return ActionResult(True, "ok", "Đã nhận chuyến.", ride_id=ride_id)


# ---------------------------------------------------------------------------
# Bắt đầu / hoàn thành + thanh toán / hủy (Task 8)
# ---------------------------------------------------------------------------
Step = Callable[[], object]


def _run_steps(steps: list[Step]) -> list[str]:
    """D10: chạy từng bước ghi bảng phụ; một bước lỗi không chặn các bước sau (vd trả tài xế, trả lượt mã).
    Trả về danh sách tên lỗi; không rollback."""
    errors: list[str] = []
    for step in steps:
        try:
            step()
        except Exception as e:  # noqa: BLE001
            errors.append(type(e).__name__)
    return errors


def _partial(ride_id: str, what: str, errors: list[str]) -> ActionResult:
    return ActionResult(True, "partial", f"{what} nhưng ghi bảng phụ lỗi ({', '.join(errors)}). "
                        "Hãy dùng Kiểm tra nhất quán -> Reconcile.", ride_id=ride_id)


def _status_steps(db, ride: Mapping, status: str, driver_id: str | None) -> list[Step]:
    """Các lệnh cập nhật trạng thái ở rides_by_customer, rides_by_area_date (và rides_by_driver_month nếu có tài xế)."""
    steps: list[Step] = [
        lambda: db.exec("T06_rbc_status", [status, ride["customer_id"], ride["ride_date"], ride["ride_id"]]),
        lambda: db.exec("T06_rad_status", [status, ride["city"], ride["district"], ride["ride_date"],
                                           ride["requested_at"], ride["ride_id"]]),
    ]
    if driver_id:
        steps.append(lambda: db.exec("T06_rdm_status", [status, driver_id, yyyymm(ride["requested_at"]),
                                                        ride["requested_at"], ride["ride_id"]]))
    return steps


def _transition_guard(ride: Mapping | None, ride_id: str, driver_id: str, expected: str) -> ActionResult | None:
    if ride is None:
        return ActionResult(False, "not_found", "Không tìm thấy chuyến đi.", ride_id=ride_id)
    if ride.get("driver_id") != driver_id:
        return ActionResult(False, "forbidden", "Chuyến này không thuộc tài xế đang đăng nhập.", ride_id=ride_id)
    if ride.get("status") != expected:
        return ActionResult(False, "invalid_transition",
                            f"Chuyến đang ở trạng thái {ride.get('status')}, cần {expected}.", ride_id=ride_id,
                            current={"status": ride.get("status"), "driver_id": ride.get("driver_id")})
    return None


def _back_to_area(db, driver_id: str, city: str, district: str, plate: str | None, lat: float | None,
                  lng: float | None, now: datetime) -> None:
    d = db.one("B03_driver_get", [driver_id])
    if d is None:
        return
    db.exec("T03_area_insert", [city, district, driver_id, d.get("full_name"), d.get("phone"), d.get("rating"),
                                plate, lat, lng, now])


def start_ride(db, ride_id: str, driver_id: str, lat: float | None, lng: float | None,
               now: datetime) -> ActionResult:
    now = truncate_ms(now)
    if not _valid_coords(lat, lng):
        return ActionResult(False, "invalid_input", "Tọa độ không hợp lệ (cần cả vĩ độ và kinh độ hợp lệ).",
                            ride_id=ride_id)
    ride = db.one("B06_ride_get", [ride_id])
    bad = _transition_guard(ride, ride_id, driver_id, "ACCEPTED")
    if bad:
        return bad
    r = db.lwt("T06_ride_start", [now, {now: "ONGOING"}, ride_id, driver_id])  # IF status='ACCEPTED' AND driver_id
    if not r.applied:
        return ActionResult(False, "lwt_lost", "Trạng thái chuyến vừa thay đổi, không thể bắt đầu.",
                            ride_id=ride_id, current=r.current)
    steps = _status_steps(db, ride, "ONGOING", driver_id)
    if lat is not None and lng is not None:
        steps.append(lambda: db.exec("T03_location_insert", [driver_id, vn_date(now), now, lat, lng, 0.0]))
    errors = _run_steps(steps)
    if errors:
        return _partial(ride_id, "Đã bắt đầu chuyến", errors)
    return ActionResult(True, "ok", "Đã bắt đầu chuyến.", ride_id=ride_id)


def complete_ride(db, ride_id: str, driver_id: str, drop_district: str, lat: float | None,
                  lng: float | None, now: datetime) -> ActionResult:
    now = truncate_ms(now)
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return ActionResult(False, "not_found", "Không tìm thấy chuyến đi.", ride_id=ride_id)
    if drop_district not in AREAS.get(ride.get("city"), ()):  # trước mọi LWT
        return ActionResult(False, "invalid_input", "Quận trả khách không thuộc thành phố của chuyến.",
                            ride_id=ride_id)
    if not _valid_coords(lat, lng):
        return ActionResult(False, "invalid_input", "Tọa độ không hợp lệ (cần cả vĩ độ và kinh độ hợp lệ).",
                            ride_id=ride_id)
    bad = _transition_guard(ride, ride_id, driver_id, "ONGOING")
    if bad:
        return bad
    r = db.lwt("T08_ride_complete", [now, {now: "COMPLETED"}, ride_id, driver_id])
    if not r.applied:
        return ActionResult(False, "lwt_lost", "Trạng thái chuyến vừa thay đổi, không thể hoàn thành.",
                            ride_id=ride_id, current=r.current)
    fare = ride.get("fare") or 0.0
    discount = ride.get("discount") or 0.0
    errors = _run_steps(_status_steps(db, ride, "COMPLETED", driver_id) + [
        lambda: db.exec("T08_payment_insert", [ride["city"], vn_date(now), ride.get("payment_method"), now,
                                               ride_id, ride["customer_id"], driver_id, ride["district"],
                                               fare - discount, discount]),
        lambda: db.lwt("APP08_driver_release", [driver_id]),
        lambda: _back_to_area(db, driver_id, ride["city"], drop_district, ride.get("vehicle_plate"),
                              lat, lng, now),
    ])
    if errors:
        return _partial(ride_id, "Đã hoàn thành chuyến", errors)
    return ActionResult(True, "ok", "Đã hoàn thành chuyến và ghi nhận thanh toán.", ride_id=ride_id,
                        data={"amount": fare - discount, "discount": discount})


def cancel_ride(db, ride_id: str, actor: Mapping, reason: str, now: datetime) -> ActionResult:
    now = truncate_ms(now)
    reason = (reason or "").strip() or "Khách hủy"
    if len(reason) > 200:
        return ActionResult(False, "invalid_input", "Lý do hủy tối đa 200 ký tự.", ride_id=ride_id)
    ride: Mapping | None = None
    r = None
    for _attempt in (1, 2):  # D3: IF status = <trạng thái vừa đọc>; thua thì đọc lại (tối đa 2 vòng)
        ride = db.one("B06_ride_get", [ride_id])
        if ride is None:
            return ActionResult(False, "not_found", "Không tìm thấy chuyến đi.", ride_id=ride_id)
        if not can_view_ride(actor.get("role"), actor.get("ref_id"), ride):
            return ActionResult(False, "forbidden", "Bạn không có quyền với chuyến này.", ride_id=ride_id)
        if ride.get("status") not in CANCELLABLE:
            return ActionResult(False, "invalid_transition",
                                f"Chuyến đang ở trạng thái {ride.get('status')}, không thể hủy.", ride_id=ride_id,
                                current={"status": ride.get("status")})
        if not can_cancel_ride(actor.get("role"), actor.get("ref_id"), ride):
            return ActionResult(False, "forbidden", "Bạn không có quyền hủy chuyến này.", ride_id=ride_id)
        r = db.lwt("T10_ride_cancel", [reason, {now: "CANCELLED"}, ride_id, ride["status"]])
        if r.applied:
            break
    else:
        return ActionResult(False, "lwt_lost", "Trạng thái chuyến vừa thay đổi, hãy thử lại.", ride_id=ride_id,
                            current=r.current if r is not None else None)

    driver_id = ride.get("driver_id")
    had_driver = ride["status"] == "ACCEPTED" and bool(driver_id)  # trạng thái đã quan sát, khớp với IF của LWT
    steps = _status_steps(db, ride, "CANCELLED", driver_id if had_driver else None)
    if had_driver:
        steps += [
            lambda: db.lwt("APP08_driver_release", [driver_id]),
            lambda: _back_to_area(db, driver_id, ride["city"], ride["district"], ride.get("vehicle_plate"),
                                  None, None, now),
        ]
    if ride.get("promo_code"):
        steps.append(lambda: release_promo(db, ride["promo_code"]))
    errors = _run_steps(steps)
    if errors:
        return _partial(ride_id, "Đã hủy chuyến", errors)
    return ActionResult(True, "ok", "Đã hủy chuyến.", ride_id=ride_id)
