"""Kiểm tra nhất quán và reconcile (9.4). `rides` là nguồn đúng; các bảng phụ có thể lệch khi một lệnh ghi lỗi giữa chừng
(D10, không rollback) nên có công cụ so sánh và ghi lại từ `rides`.

Tài xế kẹt BUSY: lệnh nhận chuyến chạy LWT `drivers` (AVAILABLE -> BUSY) trước rồi mới LWT `rides`. Nếu lệnh đầu gặp
WriteTimeout kiểu CAS (kết quả không rõ) hoặc tiến trình chết giữa hai lệnh thì tài xế BUSY mà không có chuyến nào.
`find_stuck_busy_drivers` phát hiện, `release_stuck_driver` chỉ giải phóng (LWT `IF status = 'BUSY'`) khi xác minh
KHÔNG còn chuyến ACCEPTED/ONGOING của tài xế đó.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from domain.labels import driver_status
from domain.tz import vn_date, yyyymm
from services.driver_presence import find_area_rows
from services.result import ActionResult

ACTIVE = ("ACCEPTED", "ONGOING")
# Quét rides (không có chỉ mục theo tài xế): chỉ dùng cho công cụ quản trị, có chủ đích (không nằm trong catalog nghiệp vụ).
RIDES_SCAN_CODE = "APP27_rides_by_driver_scan"
RIDES_SCAN_CQL = "SELECT ride_id, driver_id, status FROM rides"


@dataclass(frozen=True)
class Diff:
    table: str
    column: str
    expected: Any
    actual: Any


def _missing(table: str) -> Diff:
    return Diff(table, "(row)", "present", "missing")


def _compare(diffs: list[Diff], table: str, expected: dict, row: dict | None) -> None:
    if row is None:
        diffs.append(_missing(table))
        return
    for col, want in expected.items():
        if row.get(col) != want:
            diffs.append(Diff(table, col, want, row.get(col)))


def check_ride(db, ride_id: str) -> list[Diff]:
    """So `rides` với các bảng phụ trên cột status, driver_id, fare (payment: amount == fare - discount)."""
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return [_missing("rides")]
    diffs: list[Diff] = []
    want = {"status": ride.get("status"), "driver_id": ride.get("driver_id"), "fare": ride.get("fare")}
    _compare(diffs, "rides_by_customer", want,
             db.one("APP23_rbc_get", [ride["customer_id"], ride["ride_date"], ride_id]))
    _compare(diffs, "rides_by_area_date", want,
             db.one("APP24_rad_get", [ride["city"], ride["district"], ride["ride_date"], ride["requested_at"],
                                      ride_id]))
    if ride.get("driver_id"):
        _compare(diffs, "rides_by_driver_month", {"status": ride.get("status"), "fare": ride.get("fare")},
                 db.one("APP25_rdm_get", [ride["driver_id"], yyyymm(ride["requested_at"]), ride["requested_at"],
                                          ride_id]))
    if ride.get("status") == "COMPLETED" and ride.get("completed_at"):
        amount = (ride.get("fare") or 0.0) - (ride.get("discount") or 0.0)
        _compare(diffs, "payments_by_city_date", {"amount": amount},
                 db.one("APP26_payment_get", [ride["city"], vn_date(ride["completed_at"]),
                                              ride.get("payment_method"), ride["completed_at"], ride_id]))
    return diffs


def reconcile(db, ride_id: str) -> list[str]:
    """Ghi lại các bảng phụ từ `rides` (INSERT cùng khóa nên chạy lại được, không sinh dòng trùng).
    Trả danh sách bảng đã ghi; không có chuyến thì trả []."""
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return []
    written: list[str] = []
    db.exec("T04_rbc_insert", [ride["customer_id"], ride["ride_date"], ride_id, ride.get("pickup_address"),
                               ride.get("destination_address"), ride.get("driver_id"), ride.get("fare"),
                               ride.get("status")])
    written.append("rides_by_customer")
    db.exec("T04_rad_insert", [ride["city"], ride["district"], ride["ride_date"], ride["requested_at"], ride_id,
                               ride["customer_id"], ride.get("driver_id"), ride.get("pickup_address"),
                               ride.get("destination_address"), ride.get("fare"), ride.get("status"),
                               ride.get("payment_method")])
    written.append("rides_by_area_date")
    if ride.get("driver_id"):
        db.exec("T05_rdm_insert", [ride["driver_id"], yyyymm(ride["requested_at"]), ride["requested_at"], ride_id,
                                   ride["customer_id"], ride.get("pickup_address"), ride.get("destination_address"),
                                   ride.get("distance_km"), ride.get("fare"), ride.get("status")])
        written.append("rides_by_driver_month")
    if ride.get("status") == "COMPLETED" and ride.get("completed_at"):
        discount = ride.get("discount") or 0.0
        db.exec("T08_payment_insert", [ride["city"], vn_date(ride["completed_at"]), ride.get("payment_method"),
                                       ride["completed_at"], ride_id, ride["customer_id"], ride.get("driver_id"),
                                       ride["district"], (ride.get("fare") or 0.0) - discount, discount])
        written.append("payments_by_city_date")
    return written


def check_driver_areas(db, driver_id: str) -> list[str]:
    """Tài xế chỉ được có mặt ở MỘT khu vực và phải AVAILABLE. Trả danh sách lỗi (rỗng là ổn)."""
    rows = find_area_rows(db, driver_id)
    problems: list[str] = []
    if len(rows) > 1:
        where = ", ".join(f"{r['city']}/{r['district']}" for r in rows)
        problems.append(f"Có hơn 1 dòng drivers_by_area ({len(rows)}): {where}")
    elif len(rows) == 1:
        d = db.one("B03_driver_get", [driver_id])
        status = d.get("status") if d else None
        if status != "AVAILABLE":
            r = rows[0]
            problems.append(f"Có dòng drivers_by_area ở {r['city']}/{r['district']} nhưng tài xế đang {status}, "
                            "không phải AVAILABLE")
    return problems


# ---------------------------------------------------------------------------
# Tài xế kẹt BUSY
# ---------------------------------------------------------------------------
def _scan_active(db) -> dict[str, list[str]]:
    """driver_id -> các ride_id ACCEPTED/ONGOING theo `rides` (nguồn đúng). Quét toàn bảng, chỉ dùng cho công cụ này."""
    out: dict[str, list[str]] = {}
    for r in db.raw(RIDES_SCAN_CODE, "rides", RIDES_SCAN_CQL, (), kind="scan"):
        if r.get("driver_id") and r.get("status") in ACTIVE:
            out.setdefault(r["driver_id"], []).append(r["ride_id"])
    return out


def _prev_month(ym: int) -> int:
    y, m = divmod(ym, 100)
    return (y - 1) * 100 + 12 if m == 1 else ym - 1


def _fast_active_row(db, driver_id: str, now: datetime) -> dict | None:
    """Đường nhanh: rides_by_driver_month tháng này và tháng trước; mỗi dòng ứng viên được xác nhận lại bằng `rides`
    (bảng phụ có thể cũ). Trả về dòng `rides` đã xác nhận."""
    this_month = yyyymm(now)
    for ym in (this_month, _prev_month(this_month)):
        for row in db.rows("B10_driver_month", [driver_id, ym]):
            if row.get("status") not in ACTIVE:
                continue
            ride = db.one("B06_ride_get", [row["ride_id"]])
            if ride and ride.get("driver_id") == driver_id and ride.get("status") in ACTIVE:
                return ride
    return None


def _fast_active(db, driver_id: str, now: datetime) -> str | None:
    row = _fast_active_row(db, driver_id, now)
    return row["ride_id"] if row else None


def recent_active_ride_row(db, driver_id: str, now: datetime) -> dict | None:
    """Như recent_active_ride nhưng trả cả dòng `rides` đã đọc khi xác nhận (không đọc thêm lần nào)."""
    return _fast_active_row(db, driver_id, now)


def recent_active_ride(db, driver_id: str, now: datetime) -> str | None:
    """Chuyến ACCEPTED/ONGOING của tài xế chỉ qua đường nhanh (đọc theo partition key, không quét bảng).
    Dùng cho trang tài xế, tải mỗi lần mở trang nên không được quét toàn bảng `rides`."""
    return _fast_active(db, driver_id, now)


def active_ride_of(db, driver_id: str, now: datetime, scan: dict[str, list[str]] | None = None) -> str | None:
    """Chuyến ACCEPTED/ONGOING của tài xế, hoặc None. Không thấy ở đường nhanh thì quét `rides` để chắc chắn, vì lệnh
    ghi bảng phụ có thể đã lỗi (D10): thiếu dòng ở rides_by_driver_month không chứng minh được là không có chuyến."""
    found = _fast_active(db, driver_id, now)
    if found is not None:
        return found
    ids = (scan if scan is not None else _scan_active(db)).get(driver_id)
    return ids[0] if ids else None


def find_stuck_busy_drivers(db, now: datetime) -> list[dict]:
    """Tài xế BUSY mà không có chuyến ACCEPTED/ONGOING nào. Mỗi phần tử: driver_id, full_name, reason."""
    busy = sorted((d for d in db.rows("APP03_drivers_scan", []) if d.get("status") == "BUSY"),
                  key=lambda x: x["driver_id"])
    stuck: list[dict] = []
    scan: dict[str, list[str]] | None = None
    for d in busy:
        if _fast_active(db, d["driver_id"], now) is not None:
            continue
        if scan is None:
            scan = _scan_active(db)  # quét một lần, dùng cho mọi tài xế BUSY còn lại
        if d["driver_id"] in scan:
            continue
        stuck.append({"driver_id": d["driver_id"], "full_name": d.get("full_name"),
                      "reason": "BUSY nhưng không có chuyến ACCEPTED/ONGOING nào"})
    return stuck


def release_stuck_driver(db, driver_id: str, now: datetime) -> ActionResult:
    """Đưa tài xế BUSY kẹt về AVAILABLE bằng LWT `IF status = 'BUSY'`, chỉ sau khi xác minh không có chuyến đang chạy.
    Sau khi release kiểm lại; nếu có chuyến vừa xuất hiện (chạy đua với lệnh nhận chuyến) thì claim lại (bồi hoàn)."""
    d = db.one("B03_driver_get", [driver_id])
    if d is None:
        return ActionResult(False, "not_found", "Không tìm thấy tài xế.")
    if d.get("status") != "BUSY":
        return ActionResult(False, "invalid_transition", f"Tài xế đang ở trạng thái {driver_status(d.get('status'))}, không cần giải phóng.",
                            current={"status": d.get("status")})
    ride_id = active_ride_of(db, driver_id, now)
    if ride_id is not None:
        return ActionResult(False, "driver_busy", f"Tài xế đang có chuyến {ride_id}, không được giải phóng.",
                            ride_id=ride_id)
    r = db.lwt("APP08_driver_release", [driver_id])
    if not r.applied:
        return ActionResult(False, "lwt_lost", "Trạng thái tài xế vừa thay đổi, không giải phóng.", current=r.current)
    late = active_ride_of(db, driver_id, now)
    if late is not None:
        db.lwt("APP07_driver_claim", [driver_id])
        return ActionResult(False, "lwt_lost", f"Chuyến {late} vừa được nhận trong lúc giải phóng, tài xế vẫn được giữ ở trạng thái đang chở khách.",
                            ride_id=late)
    return ActionResult(True, "ok", "Đã giải phóng tài xế, tài xế có thể nhận chuyến trở lại.")
