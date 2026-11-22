"""Tài xế bật/tắt nhận chuyến (9.3) và danh sách chuyến chờ theo khu vực.

Mọi lần ghi `drivers.status` là LWT (D4). Tài xế chỉ có mặt ở MỘT (city, district) trong `drivers_by_area`:
bật nhận chuyến thì xóa ở mọi khu vực cấu hình rồi mới ghi khu vực mới. Biển số được kiểm qua MV
`vehicles_by_plate` (D5) vì không có bảng xe theo tài xế.
"""
from __future__ import annotations

import logging

from datetime import date, datetime
from typing import Iterable

from config import AREAS
from domain.labels import city_label, district_label
from domain.tz import truncate_ms, vn_date
from services.result import ActionResult

log = logging.getLogger(__name__)


def find_area_rows(db, driver_id: str, cities: Iterable[str] | None = None) -> list[dict]:
    """Các dòng drivers_by_area của tài xế (A06): mỗi city một truy vấn `district IN AREAS[city]`."""
    out: list[dict] = []
    for city in (list(cities) if cities is not None else list(AREAS)):
        districts = AREAS.get(city)
        if not districts:
            continue
        out.extend(db.rows("A06_area_find_driver", [city, list(districts), driver_id]))
    return out


def remove_from_all_areas(db, driver_id: str) -> list[tuple[str, str]]:
    """DELETE ở mọi (city, district) trong cấu hình (T05). Xóa dòng không tồn tại là vô hại."""
    pairs: list[tuple[str, str]] = []
    for city, districts in AREAS.items():
        for district in districts:
            db.exec("T05_area_delete", [city, district, driver_id])
            pairs.append((city, district))
    return pairs


def _valid_coords(lat: float | None, lng: float | None) -> bool:
    if lat is None and lng is None:
        return True
    if lat is None or lng is None:
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def go_online(db, driver_id: str, city: str, district: str, plate: str, lat: float | None,
              lng: float | None, now: datetime) -> ActionResult:
    if city not in AREAS or district not in AREAS[city]:
        return ActionResult(False, "invalid_input", "Thành phố hoặc quận không hợp lệ.")
    if not _valid_coords(lat, lng):
        return ActionResult(False, "invalid_input", "Tọa độ không hợp lệ (cần cả vĩ độ và kinh độ hợp lệ).")
    now = truncate_ms(now)
    d = db.one("B03_driver_get", [driver_id])
    if d is None:
        return ActionResult(False, "not_found", "Không tìm thấy tài xế.")
    plate = (plate or "").strip()
    if not any(r.get("driver_id") == driver_id for r in db.rows("B05_vehicle_by_plate", [plate])):
        return ActionResult(False, "invalid_input", "Biển số không thuộc tài xế này.")
    status = d.get("status")
    if status == "BUSY":
        return ActionResult(False, "driver_busy", "Tài xế đang có chuyến, chưa thể bật nhận chuyến.")
    was_offline = status == "OFFLINE"
    if was_offline:
        r = db.lwt("APP20_driver_online", [driver_id])
        if not r.applied and (r.current or {}).get("status") == "BUSY":
            return ActionResult(False, "driver_busy", "Tài xế đang có chuyến, chưa thể bật nhận chuyến.",
                                current=r.current)
    try:
        remove_from_all_areas(db, driver_id)
        db.exec("T03_area_insert", [city, district, driver_id, d.get("full_name"), d.get("phone"), d.get("rating"),
                                    plate, lat, lng, now])
        if lat is not None and lng is not None:
            db.exec("T03_location_insert", [driver_id, vn_date(now), now, lat, lng, 0.0])
    except Exception:  # noqa: BLE001 - D10: không rollback, báo partial
        log.exception("Tài xế %s bật nhận chuyến: ghi khu vực/vị trí lỗi", driver_id)
        return ActionResult(True, "partial", "Đã bật nhận chuyến nhưng khu vực hoặc vị trí chưa được lưu đầy đủ. "
                            "Hãy thử bật lại, hoặc nhờ quản trị viên đối soát.")
    return ActionResult(True, "ok", f"Đã bật nhận chuyến tại {district_label(district)}, {city_label(city)}.",
                        data={"was_offline": was_offline, "location": lat is not None})


def go_offline(db, driver_id: str, now: datetime) -> ActionResult:
    d = db.one("B03_driver_get", [driver_id])
    if d is None:
        return ActionResult(False, "not_found", "Không tìm thấy tài xế.")
    busy = ActionResult(False, "driver_busy", "Tài xế đang có chuyến, không thể tắt nhận chuyến.")
    if d.get("status") == "BUSY":
        return busy
    r = db.lwt("APP09_driver_offline", [driver_id])
    if not r.applied and (r.current or {}).get("status") == "BUSY":
        busy.current = r.current
        return busy
    try:
        remove_from_all_areas(db, driver_id)
    except Exception:  # noqa: BLE001
        log.exception("Tài xế %s tắt nhận chuyến: xóa khu vực lỗi", driver_id)
        return ActionResult(True, "partial", "Đã tắt nhận chuyến nhưng khu vực chưa được xóa hết. "
                            "Hãy thử tắt lại, hoặc nhờ quản trị viên đối soát.")
    return ActionResult(True, "ok", "Đã tắt nhận chuyến.")


def waiting_rides(db, city: str, district: str, day: date) -> list[dict]:
    """Chuyến REQUESTED của một khu vực trong ngày (APP15, ngày tính theo +07)."""
    rows = db.rows("APP15_area_waiting", [city, district, day])
    return sorted(rows, key=lambda r: r["requested_at"])
