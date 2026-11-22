"""Nhãn tiếng Việt cho các mã trạng thái/vai trò/phương thức thanh toán (chỉ để hiển thị, giá trị lưu trữ giữ nguyên mã)."""
from __future__ import annotations

RIDE_STATUS = {
    "REQUESTED": "Đang tìm tài xế",
    "ACCEPTED": "Tài xế đang đến",
    "ONGOING": "Đang trong chuyến",
    "COMPLETED": "Hoàn thành",
    "CANCELLED": "Đã hủy",
}
DRIVER_STATUS = {
    "AVAILABLE": "Sẵn sàng",
    "BUSY": "Đang chở khách",
    "OFFLINE": "Ngoại tuyến",
}
PAY_METHOD = {
    "CASH": "Tiền mặt",
    "MOMO": "MoMo",
    "ZALOPAY": "ZaloPay",
    "CARD": "Thẻ ngân hàng",
}
CITY = {
    "HCM": "TP. Hồ Chí Minh",
    "HN": "Hà Nội",
}
DISTRICT = {
    "Q1": "Quận 1",
    "Q3": "Quận 3",
    "TAN_PHU": "Tân Phú",
    "TAN_BINH": "Tân Bình",
    "BINH_THANH": "Bình Thạnh",
    "GO_VAP": "Gò Vấp",
    "HOAN_KIEM": "Hoàn Kiếm",
    "CAU_GIAY": "Cầu Giấy",
    "DONG_DA": "Đống Đa",
    "NAM_TU_LIEM": "Nam Từ Liêm",
    "SOC_SON": "Sóc Sơn",
}
ROLE_LABEL = {
    "ADMIN": "Quản trị viên",
    "OPERATOR": "Điều phối viên",
    "CUSTOMER": "Khách hàng",
    "DRIVER": "Tài xế",
}


def _lookup(table: dict[str, str], value):
    """Trả nhãn nếu có trong bảng, không thì trả nguyên giá trị (không đoán, không làm mất dữ liệu lạ)."""
    try:
        return table.get(value, value)
    except TypeError:  # giá trị không băm được
        return value


def ride_status(value):
    return _lookup(RIDE_STATUS, value)


def driver_status(value):
    return _lookup(DRIVER_STATUS, value)


def pay_method(value):
    return _lookup(PAY_METHOD, value)


def role_label(value):
    return _lookup(ROLE_LABEL, value)


def city_label(value):
    return _lookup(CITY, value)


def district_label(value):
    return _lookup(DISTRICT, value)


def ride_headline(status, viewer: str = "customer", driver_name: str | None = None) -> str:
    """Tiêu đề trang chuyến theo trạng thái và người xem: customer = khách của chuyến, driver = tài xế của chuyến,
    other = điều phối, quản trị hoặc tài xế đang xem chuyến chờ."""
    coming = f"Tài xế {driver_name} đang đến" if driver_name else "Tài xế đang đến"
    if status == "REQUESTED":
        return "Đang tìm tài xế cho bạn" if viewer == "customer" else "Chuyến đang chờ tài xế"
    if status == "ACCEPTED":
        return "Đến điểm đón khách" if viewer == "driver" else coming
    if status == "ONGOING":
        return "Đang chở khách" if viewer == "driver" else "Đang trong chuyến"
    if status == "COMPLETED":
        return "Chuyến đã hoàn thành"
    if status == "CANCELLED":
        return "Chuyến đã hủy"
    return ride_status(status) or "Chuyến đi"
