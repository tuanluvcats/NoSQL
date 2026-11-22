"""Múi giờ nghiệp vụ +07:00 (cố định, không dùng zoneinfo vì Windows không có tzdata)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

VN = timezone(timedelta(hours=7))


def truncate_ms(dt: datetime) -> datetime:
    return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)


def now_vn() -> datetime:
    return truncate_ms(datetime.now(VN))


def to_vn(dt: datetime) -> datetime:
    """datetime naive được coi là UTC (cách driver trả về timestamp)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN)


def vn_date(dt: datetime) -> date:
    return to_vn(dt).date()


def yyyymm(dt: datetime) -> int:
    d = vn_date(dt)
    return d.year * 100 + d.month


def parse_vn(s: str) -> datetime:
    s = s.strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=VN)
        except ValueError:
            continue
    raise ValueError(f'Thời gian không hợp lệ: {s!r} (cần YYYY-MM-DD HH:MM[:SS])')


def fmt_vn(dt: datetime) -> str:
    return to_vn(dt).strftime('%d/%m/%Y %H:%M:%S')


def to_date(v) -> date:
    """Nhận date, chuỗi 'YYYY-MM-DD', hoặc object có .date() (vd cassandra.util.Date)."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return datetime.strptime(v.strip(), '%Y-%m-%d').date()
    if hasattr(v, 'date'):
        return v.date()
    raise ValueError(f'Không đổi được sang date: {v!r}')


_DAY_FORMATS = ('%d/%m/%Y', '%Y-%m-%d')


def parse_day(raw: str) -> date:
    """Ngày người dùng nhập: dd/mm/yyyy (cách viết trên giao diện) hoặc YYYY-MM-DD (liên kết cũ, ô chọn ngày của trình duyệt)."""
    s = (raw or '').strip()
    for fmt in _DAY_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Ngày không hợp lệ: {raw!r}')


def fmt_ago(dt: datetime, now: datetime) -> str:
    """Thời gian tương đối cho danh sách chuyến chờ: vừa xong, 5 phút trước, 2 giờ trước; quá một ngày thì ghi ngày giờ."""
    secs = (to_vn(now) - to_vn(dt)).total_seconds()
    if secs < 60:
        return 'vừa xong'
    if secs < 3600:
        return f'{int(secs // 60)} phút trước'
    if secs < 86400:
        return f'{int(secs // 3600)} giờ trước'
    return to_vn(dt).strftime('%d/%m/%Y %H:%M')


def shift_month(ym: int, delta: int) -> int:
    """Cộng trừ tháng trên số YYYYMM (202601, -1 thành 202512)."""
    y, m = divmod(ym, 100)
    idx = y * 12 + (m - 1) + delta
    return (idx // 12) * 100 + idx % 12 + 1


def month_label(ym: int) -> str:
    """Số YYYYMM thành MM/YYYY để hiển thị."""
    return f'{ym % 100:02d}/{ym // 100}'
