"""Vòng đời chuyến đi: nhận chuyến LWT hai tầng (drivers trước, rides sau, thua thì trả tài xế).

Bổ sung so với T05 (ghi README): giữ tài xế `AVAILABLE -> BUSY` bằng LWT trước, rồi LWT `rides`
`IF status = 'REQUESTED'`. Nếu thua ở `rides` thì trả tài xế về `AVAILABLE` (APP08) để không kẹt BUSY.
"""
from __future__ import annotations

from datetime import datetime

from domain.tz import truncate_ms, yyyymm
from services.driver_presence import find_area_rows, remove_from_all_areas
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
