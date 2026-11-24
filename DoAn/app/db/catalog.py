"""Catalog các câu CQL prepared của ứng dụng, mỗi câu gắn mã B/A/T/Q của CASSANDRA.MD.

Quy ước:
- Mọi SELECT đều liệt kê cột (D12), không dùng SELECT * vì protocol v4 giữ metadata cũ sau ALTER ADD.
- Không BATCH, không TTL, không counter.
- `pk` là danh sách (tên cột khóa partition, vị trí tham số `?`), được suy ra tự động từ CQL.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

try:  # db/capabilities.py ghi kết quả thăm dò hành vi Cassandra (test_cassandra_probe); chưa có thì dùng giá trị mặc định
    from db.capabilities import LWT_ON_MV_BASE_OK
except ImportError:  # pragma: no cover - phụ thuộc việc đã có db/capabilities.py hay chưa
    LWT_ON_MV_BASE_OK = True

Kind = Literal["read", "scan", "write", "lwt"]

PARTITION_KEYS: dict[str, tuple[str, ...]] = {
    "customers": ("customer_id",),
    "drivers": ("driver_id",),
    "vehicles": ("vehicle_id",),
    "vehicles_by_plate": ("license_plate",),
    "rides_by_customer": ("customer_id",),
    "user_accounts": ("username",),
    "rides": ("ride_id",),
    "rides_by_driver_month": ("driver_id", "yyyymm"),
    "rides_by_area_date": ("city", "district", "ride_date"),
    "drivers_by_area": ("city", "district"),
    "driver_locations": ("driver_id", "day"),
    "ratings_by_driver": ("driver_id",),
    "payments_by_city_date": ("city", "pay_date"),
    "promotions": ("promo_code",),
}

RIDE_COLS = (
    "ride_id", "customer_id", "customer_name", "customer_phone", "driver_id", "driver_name",
    "vehicle_plate", "city", "district", "pickup_address", "destination_address", "distance_km",
    "fare", "discount", "promo_code", "payment_method", "status", "ride_date", "requested_at",
    "accepted_at", "started_at", "completed_at", "cancel_reason", "status_history", "rated_at",
)

_RIDE_SELECT = ", ".join(RIDE_COLS)
_HISTORY_COLS = "ride_date, ride_id, pickup_address, destination_address, driver_id, fare, status"
_AREA_RIDE_COLS = ("requested_at, ride_id, customer_id, driver_id, pickup_address, "
                   "destination_address, fare, status, payment_method")
_PROMO_COLS = ("promo_code, description, discount_percent, max_discount, min_fare, cities, "
               "usage_limit, used_count, valid_from, valid_to")


@dataclass(frozen=True)
class Stmt:
    name: str
    code: str
    q: str
    table: str
    kind: Kind
    cql: str
    pk: tuple[tuple[str, int], ...] = ()


_INSERT_RE = re.compile(r"^INSERT INTO \w+ \((?P<cols>[^)]*)\) VALUES \((?P<vals>.*?)\)(?: IF NOT EXISTS)?$")
_WHERE_END = (" IF ", " ORDER BY ", " LIMIT ", " ALLOW FILTERING")
_COND_RE = re.compile(r"^(\w+) (?:=|IN) \?$")


def derive_pk(table: str, cql: str) -> tuple[tuple[str, int], ...]:
    """Suy ra (cột khóa partition, vị trí `?`) từ CQL. Lệnh scan/hệ thống trả ()."""
    keys = PARTITION_KEYS.get(table)
    if not keys:
        return ()
    m = _INSERT_RE.match(cql)
    if m:
        cols = [c.strip() for c in m.group("cols").split(",")]
        vals = [v.strip() for v in m.group("vals").split(",")]
        out, n = [], 0
        for col, val in zip(cols, vals):
            if val == "?":
                if col in keys:
                    out.append((col, n))
                n += 1
        return tuple(out)
    if " WHERE " not in cql:
        return ()
    head, where = cql.split(" WHERE ", 1)
    cut = len(where)
    for marker in _WHERE_END:
        i = where.find(marker)
        if i != -1:
            cut = min(cut, i)
    where = where[:cut]
    n = head.count("?")
    out = []
    for cond in where.split(" AND "):
        if "?" not in cond:
            continue
        mc = _COND_RE.match(cond.strip())
        if mc and mc.group(1) in keys:
            out.append((mc.group(1), n))
        n += cond.count("?")
    return tuple(out)


STATEMENTS: dict[str, Stmt] = {}


def _add(name: str, code: str, q: str, table: str, kind: Kind, cql: str) -> None:
    if name in STATEMENTS:
        raise ValueError(f"Trùng tên câu CQL: {name}")
    STATEMENTS[name] = Stmt(name, code, q, table, kind, cql, derive_pk(table, cql))


# ---- Q1 user_accounts ----
_add("B01_account_get", "B01", "Q1", "user_accounts", "read",
     "SELECT username, password_hash, role, ref_id, full_name, is_active, created_at, last_login_at "
     "FROM user_accounts WHERE username = ?")
_add("T01_account_insert", "T01", "Q1", "user_accounts", "lwt",
     "INSERT INTO user_accounts (username, password_hash, role, ref_id, full_name, is_active, created_at) "
     "VALUES (?, ?, ?, ?, ?, true, ?) IF NOT EXISTS")
_add("T02_login_touch", "T02", "Q1", "user_accounts", "write",
     "UPDATE user_accounts SET last_login_at = ? WHERE username = ?")
_add("T02_account_lock", "T02", "Q1", "user_accounts", "lwt",
     "UPDATE user_accounts SET is_active = false WHERE username = ? IF is_active = true")
_add("T02_account_unlock", "T02", "Q1", "user_accounts", "lwt",
     "UPDATE user_accounts SET is_active = true WHERE username = ? IF is_active = false")
_add("APP01_accounts_scan", "APP01", "Q1", "user_accounts", "scan",
     "SELECT username, role, ref_id, full_name, is_active, last_login_at FROM user_accounts")

# ---- Q2 customers ----
_add("B02_customer_get", "B02", "Q2", "customers", "read",
     "SELECT customer_id, full_name, phone, email, address, created_at FROM customers WHERE customer_id = ?")
_add("B18_customer_insert", "B18", "Q2", "customers", "lwt",
     "INSERT INTO customers (customer_id, full_name, phone, email, address, created_at) "
     "VALUES (?, ?, ?, ?, ?, ?) IF NOT EXISTS")
_add("B19_customer_update", "B19", "Q2", "customers", "lwt",
     "UPDATE customers SET full_name = ?, phone = ?, email = ?, address = ? WHERE customer_id = ? IF EXISTS")
_add("B20_customer_delete", "B20", "Q2", "customers", "write",
     "DELETE FROM customers WHERE customer_id = ?")
_add("APP02_customers_scan", "APP02", "Q2", "customers", "scan",
     "SELECT customer_id, full_name, phone, email, address, created_at FROM customers")

# ---- Q3/Q5/Q7 drivers ----
_add("B03_driver_get", "B03", "Q3", "drivers", "read",
     "SELECT driver_id, full_name, phone, license_number, rating, status FROM drivers WHERE driver_id = ?")
_add("APP03_drivers_scan", "APP03", "Q3", "drivers", "scan",
     "SELECT driver_id, full_name, phone, license_number, rating, status FROM drivers")
_add("APP04_driver_insert", "APP04", "Q3", "drivers", "lwt",
     "INSERT INTO drivers (driver_id, full_name, license_number, phone, rating, status) "
     "VALUES (?, ?, ?, ?, 5.0, 'OFFLINE') IF NOT EXISTS")
_add("APP05_driver_update", "APP05", "Q3", "drivers", "lwt",
     "UPDATE drivers SET full_name = ?, license_number = ?, phone = ? WHERE driver_id = ? IF EXISTS")
_add("APP06_driver_delete", "APP06", "Q3", "drivers", "lwt",
     "DELETE FROM drivers WHERE driver_id = ? IF status = 'OFFLINE'")
_add("APP20_driver_online", "APP20", "Q5", "drivers", "lwt",
     "UPDATE drivers SET status = 'AVAILABLE' WHERE driver_id = ? IF status = 'OFFLINE'")
_add("APP07_driver_claim", "APP07", "Q7", "drivers", "lwt",
     "UPDATE drivers SET status = 'BUSY' WHERE driver_id = ? IF status = 'AVAILABLE'")
_add("APP08_driver_release", "APP08", "Q7", "drivers", "lwt",
     "UPDATE drivers SET status = 'AVAILABLE' WHERE driver_id = ? IF status = 'BUSY'")
_add("APP09_driver_offline", "APP09", "Q5", "drivers", "lwt",
     "UPDATE drivers SET status = 'OFFLINE' WHERE driver_id = ? IF status = 'AVAILABLE'")
_add("T09_driver_rating", "T09", "Q15", "drivers", "write",
     "UPDATE drivers USING TIMESTAMP ? SET rating = ? WHERE driver_id = ?")

# ---- Q4 vehicles (+ MV vehicles_by_plate) ----
_add("B04_vehicle_get", "B04", "Q4", "vehicles", "read",
     "SELECT vehicle_id, driver_id, license_plate, model, color FROM vehicles WHERE vehicle_id = ?")
_add("B05_vehicle_by_plate", "B05", "Q4", "vehicles_by_plate", "read",
     "SELECT vehicle_id, driver_id, license_plate, model, color FROM vehicles_by_plate WHERE license_plate = ?")
_add("APP10_vehicles_scan", "APP10", "Q4", "vehicles", "scan",
     "SELECT vehicle_id, driver_id, license_plate, model, color FROM vehicles")
_add("APP11_vehicle_insert", "APP11", "Q4", "vehicles", "lwt",
     "INSERT INTO vehicles (vehicle_id, driver_id, license_plate, model, color) "
     "VALUES (?, ?, ?, ?, ?) IF NOT EXISTS")
# Nếu thăm dò hành vi Cassandra (db/capabilities.py) cho thấy LWT trên bảng gốc có MV không dùng được thì bỏ IF EXISTS (kind write)
_add("APP12_vehicle_update", "APP12", "Q4", "vehicles", "lwt" if LWT_ON_MV_BASE_OK else "write",
     "UPDATE vehicles SET driver_id = ?, license_plate = ?, model = ?, color = ? WHERE vehicle_id = ?"
     + (" IF EXISTS" if LWT_ON_MV_BASE_OK else ""))
_add("APP13_vehicle_delete", "APP13", "Q4", "vehicles", "write",
     "DELETE FROM vehicles WHERE vehicle_id = ?")

# ---- Q5 drivers_by_area, Q14 driver_locations ----
_add("B12_area_drivers", "B12", "Q5", "drivers_by_area", "read",
     "SELECT city, district, driver_id, full_name, phone, rating, vehicle_plate, lat, lng, last_seen "
     "FROM drivers_by_area WHERE city = ? AND district = ?")
_add("A06_area_multi", "A06", "Q5", "drivers_by_area", "read",
     "SELECT city, district, driver_id, full_name, rating, vehicle_plate "
     "FROM drivers_by_area WHERE city = ? AND district IN ?")
_add("A06_area_find_driver", "A06", "Q5", "drivers_by_area", "read",
     "SELECT city, district, driver_id, full_name, phone, rating, vehicle_plate, lat, lng "
     "FROM drivers_by_area WHERE city = ? AND district IN ? AND driver_id = ?")
_add("T03_area_insert", "T03", "Q5", "drivers_by_area", "write",
     "INSERT INTO drivers_by_area (city, district, driver_id, full_name, phone, rating, vehicle_plate, "
     "lat, lng, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
_add("T05_area_delete", "T05", "Q5", "drivers_by_area", "write",
     "DELETE FROM drivers_by_area WHERE city = ? AND district = ? AND driver_id = ?")
_add("T09_area_rating", "T09", "Q5", "drivers_by_area", "write",
     "UPDATE drivers_by_area USING TIMESTAMP ? SET rating = ? WHERE city = ? AND district = ? AND driver_id = ?")
_add("T03_location_insert", "T03", "Q14", "driver_locations", "write",
     "INSERT INTO driver_locations (driver_id, day, ts, lat, lng, speed_kmh) VALUES (?, ?, ?, ?, ?, ?)")
_add("B13_location_latest", "B13", "Q14", "driver_locations", "read",
     "SELECT ts, lat, lng, speed_kmh FROM driver_locations WHERE driver_id = ? AND day = ? LIMIT 1")
_add("Q14_location_track", "B13", "Q14", "driver_locations", "read",
     "SELECT ts, lat, lng, speed_kmh FROM driver_locations WHERE driver_id = ? AND day = ?")

# ---- Q6..Q11 rides và các bảng phi chuẩn hóa ----
_add("B06_ride_get", "B06", "Q8", "rides", "read",
     f"SELECT {_RIDE_SELECT} FROM rides WHERE ride_id = ?")
_add("T04_ride_insert", "T04", "Q6", "rides", "lwt",
     "INSERT INTO rides (ride_id, customer_id, customer_name, customer_phone, city, district, "
     "pickup_address, destination_address, distance_km, fare, discount, promo_code, payment_method, "
     "status, ride_date, requested_at, status_history) "
     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'REQUESTED', ?, ?, ?) IF NOT EXISTS")
_add("T04_rbc_insert", "T04", "Q9", "rides_by_customer", "write",
     "INSERT INTO rides_by_customer (customer_id, ride_date, ride_id, pickup_address, "
     "destination_address, driver_id, fare, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
_add("T04_rad_insert", "T04", "Q11", "rides_by_area_date", "write",
     "INSERT INTO rides_by_area_date (city, district, ride_date, requested_at, ride_id, customer_id, "
     "driver_id, pickup_address, destination_address, fare, status, payment_method) "
     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
_add("T05_ride_accept", "T05", "Q7", "rides", "lwt",
     "UPDATE rides SET driver_id = ?, driver_name = ?, vehicle_plate = ?, status = 'ACCEPTED', "
     "accepted_at = ?, status_history = status_history + ? WHERE ride_id = ? IF status = 'REQUESTED'")
_add("T05_rbc_accept", "T05", "Q9", "rides_by_customer", "write",
     "UPDATE rides_by_customer SET driver_id = ?, status = 'ACCEPTED' "
     "WHERE customer_id = ? AND ride_date = ? AND ride_id = ?")
_add("T05_rad_accept", "T05", "Q11", "rides_by_area_date", "write",
     "UPDATE rides_by_area_date SET driver_id = ?, status = 'ACCEPTED' "
     "WHERE city = ? AND district = ? AND ride_date = ? AND requested_at = ? AND ride_id = ?")
_add("T05_rdm_insert", "T05", "Q10", "rides_by_driver_month", "write",
     "INSERT INTO rides_by_driver_month (driver_id, yyyymm, requested_at, ride_id, customer_id, "
     "pickup_address, destination_address, distance_km, fare, status) "
     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
_add("T06_ride_start", "T06", "Q8", "rides", "lwt",
     "UPDATE rides SET status = 'ONGOING', started_at = ?, status_history = status_history + ? "
     "WHERE ride_id = ? IF status = 'ACCEPTED' AND driver_id = ?")
_add("T06_rbc_status", "T06", "Q9", "rides_by_customer", "write",
     "UPDATE rides_by_customer SET status = ? WHERE customer_id = ? AND ride_date = ? AND ride_id = ?")
_add("T06_rad_status", "T06", "Q11", "rides_by_area_date", "write",
     "UPDATE rides_by_area_date SET status = ? "
     "WHERE city = ? AND district = ? AND ride_date = ? AND requested_at = ? AND ride_id = ?")
_add("T06_rdm_status", "T06", "Q10", "rides_by_driver_month", "write",
     "UPDATE rides_by_driver_month SET status = ? "
     "WHERE driver_id = ? AND yyyymm = ? AND requested_at = ? AND ride_id = ?")
_add("T08_ride_complete", "T08", "Q8", "rides", "lwt",
     "UPDATE rides SET status = 'COMPLETED', completed_at = ?, status_history = status_history + ? "
     "WHERE ride_id = ? IF status = 'ONGOING' AND driver_id = ?")
_add("T08_payment_insert", "T08", "Q12", "payments_by_city_date", "write",
     "INSERT INTO payments_by_city_date (city, pay_date, payment_method, paid_at, ride_id, customer_id, "
     "driver_id, district, amount, discount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
_add("T10_ride_cancel", "T10", "Q8", "rides", "lwt",
     "UPDATE rides SET status = 'CANCELLED', cancel_reason = ?, status_history = status_history + ? "
     "WHERE ride_id = ? IF status = ?")
_add("APP14_ride_rate", "APP14", "Q15", "rides", "lwt",
     "UPDATE rides SET rated_at = ? WHERE ride_id = ? "
     "IF rated_at = null AND status = 'COMPLETED' AND customer_id = ?")
_add("APP21_ride_backfill_rated", "APP21", "Q15", "rides", "lwt",
     "UPDATE rides SET rated_at = ? WHERE ride_id = ? IF rated_at = null AND status = 'COMPLETED'")

# ---- đọc lịch sử, thống kê ----
_add("B07_customer_history", "B07", "Q9", "rides_by_customer", "read",
     f"SELECT {_HISTORY_COLS} FROM rides_by_customer WHERE customer_id = ? "
     "ORDER BY ride_date DESC, ride_id DESC")
_add("B08_customer_history_range", "B08", "Q9", "rides_by_customer", "read",
     f"SELECT {_HISTORY_COLS} FROM rides_by_customer "
     "WHERE customer_id = ? AND ride_date >= ? AND ride_date <= ? ORDER BY ride_date DESC, ride_id DESC")
_add("B09_customer_has_rides", "B09", "Q9", "rides_by_customer", "read",
     "SELECT ride_id FROM rides_by_customer WHERE customer_id = ? LIMIT 1")
_add("APP23_rbc_get", "APP23", "Q9", "rides_by_customer", "read",
     "SELECT driver_id, fare, status FROM rides_by_customer "
     "WHERE customer_id = ? AND ride_date = ? AND ride_id = ?")
_add("B10_driver_month", "B10", "Q10", "rides_by_driver_month", "read",
     "SELECT requested_at, ride_id, customer_id, pickup_address, destination_address, distance_km, "
     "fare, status FROM rides_by_driver_month WHERE driver_id = ? AND yyyymm = ?")
_add("APP22_driver_has_rides", "APP22", "Q10", "rides_by_driver_month", "read",
     "SELECT ride_id FROM rides_by_driver_month WHERE driver_id = ? AND yyyymm = ? LIMIT 1")
_add("APP25_rdm_get", "APP25", "Q10", "rides_by_driver_month", "read",
     "SELECT fare, status FROM rides_by_driver_month "
     "WHERE driver_id = ? AND yyyymm = ? AND requested_at = ? AND ride_id = ?")
_add("A01_driver_income", "A01", "Q10", "rides_by_driver_month", "read",
     "SELECT COUNT(*) AS so_chuyen, SUM(fare) AS tong_cuoc, AVG(fare) AS cuoc_tb, "
     "MIN(fare) AS cuoc_thap_nhat, MAX(fare) AS cuoc_cao_nhat FROM rides_by_driver_month "
     "WHERE driver_id = ? AND yyyymm = ? AND status = 'COMPLETED' ALLOW FILTERING")
_add("B11_area_day", "B11", "Q11", "rides_by_area_date", "read",
     f"SELECT {_AREA_RIDE_COLS} FROM rides_by_area_date WHERE city = ? AND district = ? AND ride_date = ?")
_add("APP15_area_waiting", "APP15", "Q11", "rides_by_area_date", "read",
     f"SELECT {_AREA_RIDE_COLS} FROM rides_by_area_date "
     "WHERE city = ? AND district = ? AND ride_date = ? AND status = 'REQUESTED' ALLOW FILTERING")
_add("APP24_rad_get", "APP24", "Q11", "rides_by_area_date", "read",
     "SELECT driver_id, fare, status FROM rides_by_area_date "
     "WHERE city = ? AND district = ? AND ride_date = ? AND requested_at = ? AND ride_id = ?")
_add("A04_area_stats", "A04", "Q13", "rides_by_area_date", "read",
     "SELECT COUNT(*) AS so_chuyen, MIN(requested_at) AS som_nhat, MAX(requested_at) AS muon_nhat, "
     "SUM(fare) AS tong_cuoc FROM rides_by_area_date WHERE city = ? AND district = ? AND ride_date = ?")

# ---- Q15 đánh giá ----
_add("B14_ratings", "B14", "Q15", "ratings_by_driver", "read",
     "SELECT rated_at, ride_id, customer_id, stars, comment, tags FROM ratings_by_driver WHERE driver_id = ?")
_add("A08_rating_tags", "A08", "Q15", "ratings_by_driver", "read",
     "SELECT ride_id, stars, tags FROM ratings_by_driver WHERE driver_id = ? LIMIT 2")
_add("T09_rating_insert", "T09", "Q15", "ratings_by_driver", "write",
     "INSERT INTO ratings_by_driver (driver_id, rated_at, ride_id, customer_id, stars, comment, tags) "
     "VALUES (?, ?, ?, ?, ?, ?, ?)")
_add("A05_rating_avg", "A05", "Q15", "ratings_by_driver", "read",
     "SELECT COUNT(*) AS so_danh_gia, AVG(stars) AS diem_tb FROM ratings_by_driver WHERE driver_id = ?")

# ---- Q12 thanh toán ----
_add("B15_payments_day", "B15", "Q12", "payments_by_city_date", "read",
     "SELECT payment_method, paid_at, ride_id, customer_id, driver_id, district, amount, discount "
     "FROM payments_by_city_date WHERE city = ? AND pay_date = ?")
_add("APP26_payment_get", "APP26", "Q12", "payments_by_city_date", "read",
     "SELECT amount, discount FROM payments_by_city_date "
     "WHERE city = ? AND pay_date = ? AND payment_method = ? AND paid_at = ? AND ride_id = ?")
_add("A02_revenue_method", "A02", "Q12", "payments_by_city_date", "read",
     "SELECT COUNT(*) AS so_giao_dich, SUM(amount) AS doanh_thu, SUM(discount) AS tong_giam_gia "
     "FROM payments_by_city_date WHERE city = ? AND pay_date = ? AND payment_method = ?")
_add("A03_revenue_days", "A03", "Q12", "payments_by_city_date", "read",
     "SELECT COUNT(*) AS so_giao_dich, SUM(amount) AS doanh_thu FROM payments_by_city_date "
     "WHERE city = ? AND pay_date IN ?")

# ---- Q16 promotions ----
_add("B16_promo_get", "B16", "Q16", "promotions", "read",
     f"SELECT {_PROMO_COLS} FROM promotions WHERE promo_code = ?")
_add("A08_promo_cities", "A08", "Q16", "promotions", "read",
     "SELECT promo_code, cities FROM promotions WHERE promo_code IN ?")
_add("APP16_promos_scan", "APP16", "Q16", "promotions", "scan",
     f"SELECT {_PROMO_COLS} FROM promotions")
_add("APP17_promo_insert", "APP17", "Q16", "promotions", "lwt",
     "INSERT INTO promotions (promo_code, description, discount_percent, max_discount, min_fare, cities, "
     "usage_limit, used_count, valid_from, valid_to) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?) IF NOT EXISTS")
_add("APP18_promo_update", "APP18", "Q16", "promotions", "lwt",
     "UPDATE promotions SET description = ?, discount_percent = ?, max_discount = ?, min_fare = ?, "
     "usage_limit = ?, valid_from = ?, valid_to = ? WHERE promo_code = ? IF used_count = ?")
_add("APP19_promo_delete", "APP19", "Q16", "promotions", "lwt",
     "DELETE FROM promotions WHERE promo_code = ? IF used_count = 0")
_add("T07_promo_use", "T07", "Q16", "promotions", "lwt",
     "UPDATE promotions SET used_count = ? WHERE promo_code = ? IF used_count = ?")
_add("T11_promo_city_add", "T11", "Q16", "promotions", "lwt",
     "UPDATE promotions SET cities = cities + ? WHERE promo_code = ? IF EXISTS")
_add("T11_promo_city_remove", "T11", "Q16", "promotions", "lwt",
     "UPDATE promotions SET cities = cities - ? WHERE promo_code = ? IF EXISTS")

# ---- Hệ thống (trang Kết nối, backup) ----
_add("SYS_local", "SYS", "SYS", "system.local", "read",
     "SELECT release_version, cluster_name, data_center, cql_version FROM system.local")
_add("SYS_tables", "SYS", "SYS", "system_schema.tables", "read",
     "SELECT table_name FROM system_schema.tables WHERE keyspace_name = ?")
_add("SYS_views", "SYS", "SYS", "system_schema.views", "read",
     "SELECT view_name FROM system_schema.views WHERE keyspace_name = ?")
_add("SYS_columns", "SYS", "SYS", "system_schema.columns", "read",
     "SELECT table_name, column_name, type FROM system_schema.columns WHERE keyspace_name = ?")
