"""Truy vấn đọc cho lịch sử, thu nhập tháng, doanh thu, thống kê khu vực, GPS và xuất CSV (9.3, 9.4).

Mỗi truy vấn đi vào đúng một bảng phi chuẩn hóa theo partition key của nó (không ALLOW FILTERING trên bảng lớn):
B07/B08 `rides_by_customer`, B10/A01 `rides_by_driver_month`, A02/A03 `payments_by_city_date`, A04 `rides_by_area_date`,
A06 `drivers_by_area` (IN trên clustering/partition key), B13/Q14 `driver_locations`.
Ngày/tháng luôn tính theo +07:00 (D11). Hàm tổng hợp (COUNT/SUM/AVG/MIN/MAX) do Cassandra tính trong partition.
"""
from __future__ import annotations

import csv
import io
import math
from datetime import date, datetime, timedelta

from config import AREAS, PAYMENT_METHODS
from domain.rides import history_entries
from domain.tz import to_vn, truncate_ms, vn_date
from services.result import ActionResult

HISTORY_COLUMNS = ("ride_date", "ride_id", "pickup_address", "destination_address", "driver_id", "fare", "status")
PAYMENT_COLUMNS = ("payment_method", "paid_at", "ride_id", "customer_id", "driver_id", "district", "amount", "discount")

_MIN_DAY = date(2000, 1, 1)
_MAX_DAY = date(2100, 1, 1)
_MAX_SPEED_KMH = 300.0


def _num(v) -> float:
    """None/NaN (vd AVG của tập rỗng) -> 0.0."""
    if v is None:
        return 0.0
    f = float(v)
    return 0.0 if math.isnan(f) else f


# ------------------------------------------------------------------ khách
def customer_history(db, customer_id: str, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    """Chuyến của một khách, mới nhất trước (clustering ride_date DESC, ride_id DESC). B07, hoặc B08 khi lọc ngày."""
    if date_from is None and date_to is None:
        return db.rows("B07_customer_history", [customer_id])
    return db.rows("B08_customer_history_range", [customer_id, date_from or _MIN_DAY, date_to or _MAX_DAY])


def ride_detail(db, ride_id: str) -> dict | None:
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return None
    ride = dict(ride)
    ride["history"] = history_entries(ride.get("status_history"))  # [(thời điểm +07, trạng thái)] theo thời gian
    return ride


# ------------------------------------------------------------------ tài xế
def driver_month(db, driver_id: str, yyyymm: int) -> dict:
    rides = db.rows("B10_driver_month", [driver_id, yyyymm])
    agg = db.one("A01_driver_income", [driver_id, yyyymm]) or {}
    income = {"so_chuyen": int(agg.get("so_chuyen") or 0), "tong_cuoc": _num(agg.get("tong_cuoc")),
              "cuoc_tb": _num(agg.get("cuoc_tb")), "cuoc_thap_nhat": _num(agg.get("cuoc_thap_nhat")),
              "cuoc_cao_nhat": _num(agg.get("cuoc_cao_nhat"))}
    return {"rides": rides, "income": income}


def driver_ratings(db, driver_id: str) -> dict:
    rows = db.rows("B14_ratings", [driver_id])
    agg = db.one("A05_rating_avg", [driver_id]) or {}
    count = int(agg.get("so_danh_gia") or 0)
    avg = round(_num(agg.get("diem_tb")), 2) if count else None
    return {"rows": rows, "count": count, "avg": avg}


# ------------------------------------------------------------------ doanh thu, khu vực
def revenue_day(db, city: str, day: date) -> dict:
    by_method: dict[str, dict] = {}
    for m in PAYMENT_METHODS:
        row = db.one("A02_revenue_method", [city, day, m]) or {}
        by_method[m] = {"count": int(row.get("so_giao_dich") or 0), "amount": _num(row.get("doanh_thu")),
                        "discount": _num(row.get("tong_giam_gia"))}
    return {"by_method": by_method,
            "total_count": sum(v["count"] for v in by_method.values()),
            "total_amount": sum(v["amount"] for v in by_method.values()),
            "total_discount": sum(v["discount"] for v in by_method.values())}


def revenue_7days(db, city: str, end_day: date) -> dict:
    """7 ngày kết thúc ở end_day (gồm cả end_day), tăng dần. A03 dùng IN trên partition key pay_date."""
    days = [end_day - timedelta(days=6 - i) for i in range(7)]
    row = db.one("A03_revenue_days", [city, days]) or {}
    return {"days": days, "count": int(row.get("so_giao_dich") or 0), "amount": _num(row.get("doanh_thu"))}


def area_day_stats(db, city: str, district: str, day: date) -> dict:
    row = db.one("A04_area_stats", [city, district, day]) or {}
    count = int(row.get("so_chuyen") or 0)
    earliest, latest = row.get("som_nhat"), row.get("muon_nhat")
    return {"so_chuyen": count, "tong_cuoc": _num(row.get("tong_cuoc")),
            "som_nhat": to_vn(earliest) if count and earliest is not None else None,
            "muon_nhat": to_vn(latest) if count and latest is not None else None}


def area_drivers(db, city: str, districts: list[str]) -> list[dict]:
    """Tài xế đang rảnh ở nhiều quận cùng lúc (A06, `district IN ...`). Quận ngoài cấu hình bị bỏ."""
    valid = [d for d in dict.fromkeys(districts) if d in AREAS.get(city, ())]
    if not valid:
        return []
    return db.rows("A06_area_multi", [city, valid])


# ------------------------------------------------------------------ GPS
def record_location(db, driver_id: str, lat, lng, speed, now: datetime) -> ActionResult:
    try:
        lat_v, lng_v, speed_v = float(lat), float(lng), float(0.0 if speed is None else speed)
    except (TypeError, ValueError):
        return ActionResult(False, "invalid_input", "Tọa độ hoặc tốc độ không phải số.")
    if not all(math.isfinite(v) for v in (lat_v, lng_v, speed_v)):
        return ActionResult(False, "invalid_input", "Tọa độ hoặc tốc độ không hợp lệ.")
    if not (-90.0 <= lat_v <= 90.0 and -180.0 <= lng_v <= 180.0):
        return ActionResult(False, "invalid_input", "Tọa độ không hợp lệ (vĩ độ -90..90, kinh độ -180..180).")
    if not 0.0 <= speed_v <= _MAX_SPEED_KMH:
        return ActionResult(False, "invalid_input", f"Tốc độ phải trong khoảng 0..{int(_MAX_SPEED_KMH)} km/h.")
    if db.one("B03_driver_get", [driver_id]) is None:
        return ActionResult(False, "not_found", "Không tìm thấy tài xế.")
    now = truncate_ms(now)
    db.exec("T03_location_insert", [driver_id, vn_date(now), now, lat_v, lng_v, speed_v])
    return ActionResult(True, "ok", "Đã ghi vị trí.", data={"day": vn_date(now)})


def _point(row: dict) -> dict:
    return {**row, "ts": to_vn(row["ts"])}  # driver trả datetime naive UTC; hiển thị theo +07


def driver_track(db, driver_id: str, day: date) -> dict:
    """`latest` (B13, LIMIT 1 trên clustering ts DESC) và `track` (Q14, cả lộ trình trong ngày, mới nhất trước).
    `ts` đã đổi sang +07."""
    latest = db.one("B13_location_latest", [driver_id, day])
    return {"latest": _point(latest) if latest else None,
            "track": [_point(r) for r in db.rows("Q14_location_track", [driver_id, day])]}


# ------------------------------------------------------------------ CSV
def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    if isinstance(v, datetime):
        return to_vn(v).strftime("%Y-%m-%d %H:%M:%S")
    s = str(v)  # date và cassandra.util.Date đều in dạng YYYY-MM-DD
    if s[:1] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s  # chống chèn công thức khi mở bằng Excel
    return s


def _csv(columns: tuple[str, ...], rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(columns)
    for r in rows:
        w.writerow([_cell(r.get(c)) for c in columns])
    return "﻿" + buf.getvalue()  # BOM UTF-8 để Excel nhận đúng tiếng Việt


def history_csv(rows) -> str:
    """Chỉ xuất đúng các cột trong HISTORY_COLUMNS: cột lạ trong dòng dữ liệu (vd khóa nhạy cảm) không bao giờ lọt ra."""
    return _csv(HISTORY_COLUMNS, rows)


def payments_csv(rows) -> str:
    return _csv(PAYMENT_COLUMNS, rows)
