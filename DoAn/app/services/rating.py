"""Đánh giá tài xế: một lần duy nhất nhờ LWT `rated_at` trên `rides`, và backfill cho dữ liệu seed.

Thứ tự (rides là nguồn đúng): LWT `rides` (`IF rated_at = null AND status = 'COMPLETED' AND customer_id = ?`) trước,
chỉ khi applied mới ghi `ratings_by_driver`, rồi tính lại điểm trung bình (làm tròn 2 chữ số) và cập nhật
`drivers.rating` cùng `drivers_by_area.rating`. `drivers_by_area` chỉ UPDATE ở dòng đang CÓ (tìm bằng A06): UPDATE là
upsert nên cập nhật mù sẽ sinh dòng ma khiến tài xế offline "hiện ra" trong danh sách rảnh (Review Focus 1).
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from config import RATING_TAGS
from domain.tz import truncate_ms
from services.driver_presence import find_area_rows
from services.result import ActionResult

MAX_COMMENT = 500


def _invalid_input(stars, comment, tags) -> str | None:
    if isinstance(stars, bool) or not isinstance(stars, int) or not 1 <= stars <= 5:
        return "Số sao phải là số nguyên từ 1 đến 5."
    if not isinstance(tags, (list, tuple)) or any(t not in RATING_TAGS for t in tags):
        return "Thẻ đánh giá không hợp lệ."
    if len(comment or "") > MAX_COMMENT:
        return f"Nhận xét tối đa {MAX_COMMENT} ký tự."
    return None


def rate_ride(db, ride_id: str, customer_id: str, stars: int, comment: str, tags: Sequence[str],
              now: datetime) -> ActionResult:
    now = truncate_ms(now)
    ride = db.one("B06_ride_get", [ride_id])
    if ride is None:
        return ActionResult(False, "not_found", "Không tìm thấy chuyến đi.", ride_id=ride_id)
    if ride.get("customer_id") != customer_id:
        return ActionResult(False, "forbidden", "Chỉ khách của chuyến mới được đánh giá.", ride_id=ride_id)
    if ride.get("status") != "COMPLETED" or not ride.get("driver_id"):
        return ActionResult(False, "invalid_transition", "Chỉ đánh giá được chuyến đã hoàn thành.", ride_id=ride_id,
                            current={"status": ride.get("status")})
    if ride.get("rated_at") is not None:
        return ActionResult(False, "already_rated", "Chuyến này đã được đánh giá.", ride_id=ride_id)
    comment = (comment or "").strip()
    tags = list(tags) if isinstance(tags, (list, tuple)) else tags
    bad = _invalid_input(stars, comment, tags)
    if bad:
        return ActionResult(False, "invalid_input", bad, ride_id=ride_id)

    driver_id = ride["driver_id"]
    r = db.lwt("APP14_ride_rate", [now, ride_id, customer_id])
    if not r.applied:
        return ActionResult(False, "already_rated", "Chuyến này đã được đánh giá.", ride_id=ride_id, current=r.current)

    try:
        db.exec("T09_rating_insert", [driver_id, now, ride_id, customer_id, float(stars), comment, tags])
        agg = db.one("A05_rating_avg", [driver_id]) or {}
        avg = round(float(agg["diem_tb"]), 2)
        db.exec("T09_driver_rating", [avg, driver_id])
        for row in find_area_rows(db, driver_id):  # không có dòng (tài xế offline) thì không ghi: chống dòng ma
            db.exec("T09_area_rating", [avg, row["city"], row["district"], driver_id])
    except Exception as e:  # noqa: BLE001 - D10: không rollback, báo partial
        return ActionResult(True, "partial", f"Đã ghi nhận đánh giá nhưng cập nhật điểm lỗi ({type(e).__name__}). "
                            "Hãy dùng Kiểm tra nhất quán.", ride_id=ride_id)
    return ActionResult(True, "ok", "Cảm ơn bạn đã đánh giá.", ride_id=ride_id,
                        data={"rating": avg, "count": agg.get("so_danh_gia")})


def backfill_rated_at(db) -> int:
    """D9: chuyến seed đã có dòng đánh giá nhưng `rated_at` còn null thì đặt `rated_at` = thời điểm đánh giá,
    để không cho đánh giá lại. Trả số lần LWT applied (chạy lại được, lần sau trả 0)."""
    applied = 0
    for d in db.rows("APP03_drivers_scan", []):
        for row in db.rows("B14_ratings", [d["driver_id"]]):
            if db.lwt("APP21_ride_backfill_rated", [row["rated_at"], row["ride_id"]]).applied:
                applied += 1
    return applied
