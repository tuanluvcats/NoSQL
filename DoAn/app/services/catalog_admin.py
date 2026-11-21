"""CRUD danh mục (quản trị): customers, drivers, vehicles (+MV vehicles_by_plate), promotions (+set cities).

Nguyên tắc chống "dòng ma" (D13): UPDATE/INSERT của Cassandra là upsert, nên
- tạo bằng `IF NOT EXISTS` (đã có thì trả `duplicate`),
- sửa bằng `IF EXISTS` / `IF used_count = n` (không có thì trả `not_found`),
- thêm/bớt phần tử set `cities` bằng `IF EXISTS`.
Các trang danh sách quét toàn bảng nhỏ, chấp nhận ở quy mô dữ liệu mẫu (spec §7).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from db.catalog import LWT_ON_MV_BASE_OK
from domain.tz import yyyymm
from services.result import ActionResult

CUSTOMER_ID_RE = re.compile(r"^CUST[0-9A-Z_]{1,40}$")
DRIVER_ID_RE = re.compile(r"^DRV_[0-9A-Z_]{1,40}$")
VEHICLE_ID_RE = re.compile(r"^VEH_[0-9A-Z_]{1,40}$")
LICENSE_RE = re.compile(r"^\d{12}$")
PHONE_RE = re.compile(r"^0\d{9}$")
PROMO_CODE_RE = re.compile(r"^[A-Z0-9]{3,20}$")
CITY_RE = re.compile(r"^[A-Z]{2,5}$")
FIRST_MONTH = 202609


# ---------------------------------------------------------------- forms
@dataclass
class CustomerForm:
    customer_id: str
    full_name: str
    phone: str
    email: str = ""
    address: str = ""


@dataclass
class DriverForm:
    driver_id: str
    full_name: str
    license_number: str
    phone: str


@dataclass
class VehicleForm:
    vehicle_id: str
    driver_id: str
    license_plate: str
    model: str = ""
    color: str = ""


@dataclass
class PromoForm:
    promo_code: str
    description: str
    discount_percent: int
    max_discount: float
    min_fare: float
    cities: set[str] = field(default_factory=set)
    usage_limit: int = 1
    valid_from: datetime | None = None
    valid_to: datetime | None = None


# ----------------------------------------------------------- validation
def validate_customer(f: CustomerForm) -> list[str]:
    errs: list[str] = []
    if not CUSTOMER_ID_RE.match(f.customer_id or ""):
        errs.append("Mã khách phải bắt đầu bằng CUST, chỉ gồm chữ in hoa, số, gạch dưới (tối đa 44 ký tự).")
    if not (f.full_name or "").strip():
        errs.append("Họ tên không được để trống.")
    if not PHONE_RE.match(f.phone or ""):
        errs.append("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
    if (f.email or "").strip() and "@" not in f.email:
        errs.append("Email không hợp lệ.")
    return errs


def validate_driver(f: DriverForm) -> list[str]:
    errs: list[str] = []
    if not DRIVER_ID_RE.match(f.driver_id or ""):
        errs.append("Mã tài xế phải bắt đầu bằng DRV_, chỉ gồm chữ in hoa, số, gạch dưới.")
    if not (f.full_name or "").strip():
        errs.append("Họ tên không được để trống.")
    if not LICENSE_RE.match(f.license_number or ""):
        errs.append("Số bằng lái gồm đúng 12 chữ số.")
    if not PHONE_RE.match(f.phone or ""):
        errs.append("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
    return errs


def validate_vehicle(f: VehicleForm) -> list[str]:
    errs: list[str] = []
    if not VEHICLE_ID_RE.match(f.vehicle_id or ""):
        errs.append("Mã xe phải bắt đầu bằng VEH_, chỉ gồm chữ in hoa, số, gạch dưới.")
    if not DRIVER_ID_RE.match(f.driver_id or ""):
        errs.append("Mã tài xế của xe không hợp lệ (dạng DRV_...).")
    if not 1 <= len((f.license_plate or "").strip()) <= 15:
        errs.append("Biển số dài từ 1 đến 15 ký tự.")
    return errs


def validate_promo(f: PromoForm) -> list[str]:
    errs: list[str] = []
    if not PROMO_CODE_RE.match(f.promo_code or ""):
        errs.append("Mã khuyến mãi gồm 3-20 ký tự chữ in hoa hoặc số.")
    if not isinstance(f.discount_percent, int) or not 1 <= f.discount_percent <= 100:
        errs.append("Phần trăm giảm phải từ 1 đến 100.")
    if f.max_discount is None or f.max_discount < 0:
        errs.append("Mức giảm tối đa không được âm.")
    if f.min_fare is None or f.min_fare < 0:
        errs.append("Cước tối thiểu không được âm.")
    if not isinstance(f.usage_limit, int) or f.usage_limit < 1:
        errs.append("Giới hạn lượt dùng phải từ 1 trở lên.")
    if f.valid_from is None or f.valid_to is None:
        errs.append("Phải nhập thời gian hiệu lực (từ ngày, đến ngày).")
    elif not f.valid_from < f.valid_to:
        errs.append("Thời điểm bắt đầu phải nhỏ hơn thời điểm kết thúc.")
    for c in sorted(f.cities or ()):
        if not CITY_RE.match(c):
            errs.append(f"Mã thành phố '{c}' không hợp lệ (2-5 chữ in hoa).")
    return errs


def _invalid(errs: list[str]) -> ActionResult:
    return ActionResult(False, "invalid_input", " ".join(errs), data={"errors": errs})


def _blank_to_none(s: str | None) -> str | None:
    return (s or "").strip() or None


# ------------------------------------------------------------ dùng chung
def _accounts_pointing_to(db, ref_id: str) -> list[str]:
    return sorted(r["username"] for r in db.rows("APP01_accounts_scan") if r.get("ref_id") == ref_id)


def _months(first_month: int, now: datetime) -> list[int]:
    last = yyyymm(now)
    y, m = divmod(first_month, 100)
    out: list[int] = []
    while y * 100 + m <= last:
        out.append(y * 100 + m)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


# ------------------------------------------------------------- customers
def list_customers(db) -> list[dict]:
    return sorted(db.rows("APP02_customers_scan"), key=lambda r: r["customer_id"])


def get_customer(db, customer_id: str) -> dict | None:
    return db.one("B02_customer_get", [customer_id])


def customer_has_rides(db, customer_id: str) -> bool:
    return db.one("B09_customer_has_rides", [customer_id]) is not None


def create_customer(db, f: CustomerForm, now: datetime) -> ActionResult:
    errs = validate_customer(f)
    if errs:
        return _invalid(errs)
    res = db.lwt("B18_customer_insert", [f.customer_id, f.full_name.strip(), f.phone, _blank_to_none(f.email),
                                         _blank_to_none(f.address), now])
    if not res.applied:
        return ActionResult(False, "duplicate", f"Mã khách {f.customer_id} đã tồn tại.", current=res.current)
    return ActionResult(True, "ok", f"Đã tạo khách {f.customer_id}.")


def update_customer(db, f: CustomerForm) -> ActionResult:
    errs = validate_customer(f)
    if errs:
        return _invalid(errs)
    res = db.lwt("B19_customer_update", [f.full_name.strip(), f.phone, _blank_to_none(f.email),
                                         _blank_to_none(f.address), f.customer_id])
    if not res.applied:
        return ActionResult(False, "not_found", f"Không tìm thấy khách {f.customer_id}.")
    return ActionResult(True, "ok", f"Đã cập nhật khách {f.customer_id}.")


def delete_customer(db, customer_id: str) -> ActionResult:
    if get_customer(db, customer_id) is None:
        return ActionResult(False, "not_found", f"Không tìm thấy khách {customer_id}.")
    if customer_has_rides(db, customer_id):
        return ActionResult(False, "has_rides", "Khách đã có chuyến đi, không được xóa.")
    users = _accounts_pointing_to(db, customer_id)
    if users:
        return ActionResult(False, "in_use", f"Còn tài khoản trỏ tới khách này: {', '.join(users)}.",
                            data={"accounts": users})
    db.exec("B20_customer_delete", [customer_id])
    return ActionResult(True, "ok", f"Đã xóa khách {customer_id}.")


# --------------------------------------------------------------- drivers
def list_drivers(db) -> list[dict]:
    return sorted(db.rows("APP03_drivers_scan"), key=lambda r: r["driver_id"])


def get_driver(db, driver_id: str) -> dict | None:
    return db.one("B03_driver_get", [driver_id])


def driver_has_rides(db, driver_id: str, now: datetime, first_month: int = FIRST_MONTH) -> bool:
    """APP22 cho từng yyyymm từ first_month đến tháng của `now` (rides_by_driver_month chia partition theo tháng)."""
    return any(db.one("APP22_driver_has_rides", [driver_id, m]) is not None for m in _months(first_month, now))


def create_driver(db, f: DriverForm) -> ActionResult:
    errs = validate_driver(f)
    if errs:
        return _invalid(errs)
    res = db.lwt("APP04_driver_insert", [f.driver_id, f.full_name.strip(), f.license_number, f.phone])
    if not res.applied:
        return ActionResult(False, "duplicate", f"Mã tài xế {f.driver_id} đã tồn tại.", current=res.current)
    return ActionResult(True, "ok", f"Đã tạo tài xế {f.driver_id} (OFFLINE, điểm 5.0).")


def update_driver(db, f: DriverForm) -> ActionResult:
    errs = validate_driver(f)
    if errs:
        return _invalid(errs)
    res = db.lwt("APP05_driver_update", [f.full_name.strip(), f.license_number, f.phone, f.driver_id])
    if not res.applied:
        return ActionResult(False, "not_found", f"Không tìm thấy tài xế {f.driver_id}.")
    return ActionResult(True, "ok", f"Đã cập nhật tài xế {f.driver_id}.")


def delete_driver(db, driver_id: str, now: datetime, first_month: int = FIRST_MONTH) -> ActionResult:
    if get_driver(db, driver_id) is None:
        return ActionResult(False, "not_found", f"Không tìm thấy tài xế {driver_id}.")
    if driver_has_rides(db, driver_id, now, first_month):
        return ActionResult(False, "has_rides", "Tài xế đã có chuyến đi, không được xóa.")
    vehicles = sorted(v["vehicle_id"] for v in db.rows("APP10_vehicles_scan") if v.get("driver_id") == driver_id)
    users = _accounts_pointing_to(db, driver_id)
    if vehicles or users:
        parts = []
        if vehicles:
            parts.append("xe " + ", ".join(vehicles))
        if users:
            parts.append("tài khoản " + ", ".join(users))
        return ActionResult(False, "in_use", "Tài xế còn được tham chiếu bởi " + " và ".join(parts) + ".",
                            data={"vehicles": vehicles, "accounts": users})
    res = db.lwt("APP06_driver_delete", [driver_id])
    if not res.applied:
        if (res.current or {}).get("status") is None:
            return ActionResult(False, "not_found", f"Không tìm thấy tài xế {driver_id}.")
        return ActionResult(False, "driver_busy", "Tài xế không ở trạng thái OFFLINE nên chưa thể xóa.",
                            current=res.current)
    return ActionResult(True, "ok", f"Đã xóa tài xế {driver_id}.")


# -------------------------------------------------------------- vehicles
def list_vehicles(db) -> list[dict]:
    return sorted(db.rows("APP10_vehicles_scan"), key=lambda r: r["vehicle_id"])


def get_vehicle(db, vehicle_id: str) -> dict | None:
    return db.one("B04_vehicle_get", [vehicle_id])


def find_vehicle_by_plate(db, plate: str) -> list[dict]:
    """B05: tra qua materialized view vehicles_by_plate (partition key = biển số)."""
    return db.rows("B05_vehicle_by_plate", [(plate or "").strip()])


def _vehicle_precheck(db, f: VehicleForm) -> ActionResult | None:
    errs = validate_vehicle(f)
    if errs:
        return _invalid(errs)
    if db.one("B03_driver_get", [f.driver_id]) is None:
        return ActionResult(False, "invalid_input", f"Tài xế {f.driver_id} không tồn tại.")
    plate = f.license_plate.strip()
    owner = db.one("B05_vehicle_by_plate", [plate])
    if owner is not None and owner["vehicle_id"] != f.vehicle_id:
        return ActionResult(False, "duplicate_plate",
                            f"Biển số {plate} đã thuộc xe {owner['vehicle_id']}.", current=owner)
    return None


def create_vehicle(db, f: VehicleForm) -> ActionResult:
    bad = _vehicle_precheck(db, f)
    if bad:
        return bad
    res = db.lwt("APP11_vehicle_insert", [f.vehicle_id, f.driver_id, f.license_plate.strip(),
                                          _blank_to_none(f.model), _blank_to_none(f.color)])
    if not res.applied:
        return ActionResult(False, "duplicate", f"Mã xe {f.vehicle_id} đã tồn tại.", current=res.current)
    return ActionResult(True, "ok", f"Đã tạo xe {f.vehicle_id}.")


def update_vehicle(db, f: VehicleForm) -> ActionResult:
    bad = _vehicle_precheck(db, f)
    if bad:
        return bad
    params = [f.driver_id, f.license_plate.strip(), _blank_to_none(f.model), _blank_to_none(f.color), f.vehicle_id]
    if LWT_ON_MV_BASE_OK:  # APP12 có IF EXISTS
        if not db.lwt("APP12_vehicle_update", params).applied:
            return ActionResult(False, "not_found", f"Không tìm thấy xe {f.vehicle_id}.")
    else:  # probe cho thấy LWT trên bảng gốc có MV không dùng được: kiểm tồn tại bằng đọc rồi mới UPDATE
        if get_vehicle(db, f.vehicle_id) is None:
            return ActionResult(False, "not_found", f"Không tìm thấy xe {f.vehicle_id}.")
        db.exec("APP12_vehicle_update", params)
    return ActionResult(True, "ok", f"Đã cập nhật xe {f.vehicle_id} (view vehicles_by_plate tự cập nhật).")


def delete_vehicle(db, vehicle_id: str) -> ActionResult:
    if get_vehicle(db, vehicle_id) is None:
        return ActionResult(False, "not_found", f"Không tìm thấy xe {vehicle_id}.")
    db.exec("APP13_vehicle_delete", [vehicle_id])
    return ActionResult(True, "ok", f"Đã xóa xe {vehicle_id}.")


# ------------------------------------------------------------ promotions
def list_promos(db) -> list[dict]:
    return sorted(db.rows("APP16_promos_scan"), key=lambda r: r["promo_code"])


def get_promo(db, promo_code: str) -> dict | None:
    return db.one("B16_promo_get", [promo_code])


def create_promo(db, f: PromoForm) -> ActionResult:
    errs = validate_promo(f)
    if errs:
        return _invalid(errs)
    res = db.lwt("APP17_promo_insert", [f.promo_code, f.description, f.discount_percent, float(f.max_discount),
                                        float(f.min_fare), set(f.cities), f.usage_limit, f.valid_from, f.valid_to])
    if not res.applied:
        return ActionResult(False, "duplicate", f"Mã khuyến mãi {f.promo_code} đã tồn tại.", current=res.current)
    return ActionResult(True, "ok", f"Đã tạo mã khuyến mãi {f.promo_code}.")


def update_promo(db, f: PromoForm) -> ActionResult:
    """Không đụng `cities` (có thao tác thêm/bớt riêng) và `used_count`. APP18 dùng used_count vừa đọc làm điều kiện."""
    errs = validate_promo(f)
    if errs:
        return _invalid(errs)
    cur = get_promo(db, f.promo_code)
    if cur is None:
        return ActionResult(False, "not_found", f"Không tìm thấy mã khuyến mãi {f.promo_code}.")
    used = cur.get("used_count") or 0
    if f.usage_limit < used:
        return ActionResult(False, "invalid_input",
                            f"Giới hạn lượt dùng ({f.usage_limit}) không được nhỏ hơn số lượt đã dùng ({used}).")
    res = db.lwt("APP18_promo_update", [f.description, f.discount_percent, float(f.max_discount), float(f.min_fare),
                                        f.usage_limit, f.valid_from, f.valid_to, f.promo_code, used])
    if not res.applied:
        if (res.current or {}).get("used_count") is None and get_promo(db, f.promo_code) is None:
            return ActionResult(False, "not_found", f"Không tìm thấy mã khuyến mãi {f.promo_code}.")
        return ActionResult(False, "lwt_lost", "Số lượt dùng vừa thay đổi do có người đặt xe, hãy mở lại và sửa lần nữa.",
                            current=res.current)
    return ActionResult(True, "ok", f"Đã cập nhật mã khuyến mãi {f.promo_code}.")


def delete_promo(db, promo_code: str) -> ActionResult:
    res = db.lwt("APP19_promo_delete", [promo_code])
    if not res.applied:
        if (res.current or {}).get("used_count") is None:
            return ActionResult(False, "not_found", f"Không tìm thấy mã khuyến mãi {promo_code}.")
        return ActionResult(False, "in_use", "Mã đã có lượt sử dụng nên không thể xóa.", current=res.current)
    return ActionResult(True, "ok", f"Đã xóa mã khuyến mãi {promo_code}.")


def _change_city(db, name: str, code: str, city: str, verb: str) -> ActionResult:
    city = (city or "").strip().upper()
    if not CITY_RE.match(city):
        return _invalid([f"Mã thành phố '{city}' không hợp lệ (2-5 chữ in hoa)."])
    res = db.lwt(name, [{city}, code])
    if not res.applied:
        return ActionResult(False, "not_found", f"Không tìm thấy mã khuyến mãi {code}.")
    after = get_promo(db, code)
    cities = set((after or {}).get("cities") or ())
    return ActionResult(True, "ok", f"Đã {verb} thành phố {city} của mã {code}.", data={"cities": cities})


def add_promo_city(db, code: str, city: str) -> ActionResult:
    """T11: cities = cities + {city} IF EXISTS (không có mã thì không tạo dòng ma)."""
    return _change_city(db, "T11_promo_city_add", code, city, "thêm")


def remove_promo_city(db, code: str, city: str) -> ActionResult:
    return _change_city(db, "T11_promo_city_remove", code, city, "bỏ")
