-- =====================================================================
-- 03_queries_basic.cql — Truy vấn CƠ BẢN (thang điểm mục 5 & 7)
-- Mỗi truy vấn chỉ đọc MỘT partition, chỉ định đủ partition key.
-- Chạy:  docker exec nosql-cassandra cqlsh -f /tmp/cassandra/03_queries_basic.cql
-- Hoặc chạy từng câu trong DbSchema (SQL Editor / Query Builder).
-- Lưu ý: cqlsh hiển thị thời gian theo UTC (+0000) — 08:15 giờ VN hiện là 01:15.
-- =====================================================================
USE ride_booking;

-- [B01] (Q1) Đăng nhập: lấy tài khoản theo username
SELECT username, role, ref_id, full_name, is_active, password_hash
FROM user_accounts WHERE username = 'cust001';

-- [B02] (Q2) Hồ sơ khách hàng theo mã
SELECT customer_id, full_name, phone, email, address, created_at
FROM customers WHERE customer_id = 'CUST001';

-- [B03] (Q3) Hồ sơ tài xế theo mã
SELECT driver_id, full_name, phone, license_number, rating, status
FROM drivers WHERE driver_id = 'DRV_555';

-- [B04] (Q4) Thông tin xe theo mã xe
SELECT vehicle_id, driver_id, license_plate, model, color
FROM vehicles WHERE vehicle_id = 'VEH_555';

-- [B05] (Q4) Tra xe theo biển số / theo tài xế — dùng secondary index trên bảng nhỏ vehicles
SELECT vehicle_id, driver_id, license_plate, model FROM vehicles WHERE license_plate = '51K-567.89';
SELECT vehicle_id, driver_id, license_plate, model FROM vehicles WHERE driver_id = 'DRV_555';

-- [B06] (Q8) Chi tiết một chuyến theo ride_id
SELECT ride_id, customer_name, driver_name, pickup_address, destination_address,
       distance_km, fare, discount, payment_method, status, requested_at, completed_at
FROM rides WHERE ride_id = 'RIDE_1001';

-- [B07] (Q9) Lịch sử chuyến của một khách, mới nhất trước
SELECT ride_date, ride_id, pickup_address, destination_address, driver_id, fare, status
FROM rides_by_customer
WHERE customer_id = 'CUST001'
ORDER BY ride_date DESC, ride_id DESC;

-- [B08] (Q9) Lịch sử chuyến trong một khoảng ngày (range trên clustering column)
SELECT ride_date, ride_id, destination_address, fare, status
FROM rides_by_customer
WHERE customer_id = 'CUST001'
  AND ride_date >= '2026-10-01' AND ride_date <= '2026-10-04';

-- [B09] (Q9) 3 chuyến gần nhất của khách (LIMIT)
SELECT ride_date, ride_id, destination_address, status
FROM rides_by_customer
WHERE customer_id = 'CUST006'
ORDER BY ride_date DESC, ride_id DESC
LIMIT 3;

-- [B10] (Q10) Các chuyến của tài xế trong tháng 10/2026 (đã sắp xếp mới nhất trước do CLUSTERING ORDER DESC)
SELECT requested_at, ride_id, customer_id, destination_address, fare, status
FROM rides_by_driver_month
WHERE driver_id = 'DRV_551' AND yyyymm = 202610;

-- [B11] (Q11) Điều phối: các chuyến trong ngày tại một khu vực
SELECT requested_at, ride_id, customer_id, driver_id, pickup_address, status
FROM rides_by_area_date
WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04';

-- [B12] (Q5) Tài xế đang rảnh trong khu vực Tân Phú (TP.HCM)
SELECT driver_id, full_name, phone, rating, last_seen
FROM drivers_by_area
WHERE city = 'HCM' AND district = 'TAN_PHU';

-- [B13] (Q14) Vị trí GPS mới nhất của tài xế trong ngày (LIMIT 1 vì ts sắp xếp giảm dần)
SELECT ts, location, speed_kmh
FROM driver_locations
WHERE driver_id = 'DRV_552' AND day = '2026-10-04'
LIMIT 1;

-- [B14] (Q15) Đánh giá của một tài xế, mới nhất trước
SELECT rated_at, ride_id, customer_id, stars, comment, tags
FROM ratings_by_driver
WHERE driver_id = 'DRV_551';

-- [B15] (Q12) Các giao dịch thanh toán trong ngày tại TP.HCM
SELECT payment_method, paid_at, ride_id, customer_id, amount, discount
FROM payments_by_city_date
WHERE city = 'HCM' AND pay_date = '2026-10-03';

-- [B16] (Q16) Kiểm tra mã khuyến mãi
SELECT promo_code, description, discount_percent, max_discount, min_fare, cities, usage_limit, used_count, valid_to
FROM promotions WHERE promo_code = 'GIAM20';

-- [B17] (Q13) Thống kê số chuyến theo ngày trong tháng (bảng counter)
SELECT ride_date, rides_requested, rides_completed, rides_cancelled
FROM ride_stats_by_city
WHERE city = 'HCM' AND yyyymm = 202610;

-- ---------------------------------------------------------------------
-- CRUD cơ bản (thêm – sửa – xóa) trên một khách hàng thử nghiệm, chạy xong dữ liệu trở về như cũ
-- ---------------------------------------------------------------------
-- [B18] Thêm
INSERT INTO customers (customer_id, full_name, phone, email, address, created_at)
VALUES ('CUST999', 'Khách Thử Nghiệm', '0909999999', 'test@huit.edu.vn', '140 Lê Trọng Tấn, Tân Phú, TP.HCM', '2026-10-04 10:30:00+0700');
SELECT customer_id, full_name, phone FROM customers WHERE customer_id = 'CUST999';

-- [B19] Sửa (UPDATE cũng là upsert: nếu chưa có dòng thì sẽ tạo mới)
UPDATE customers SET phone = '0908888888', address = '12 Nguyễn Văn Bảo, Gò Vấp, TP.HCM'
WHERE customer_id = 'CUST999';
SELECT customer_id, full_name, phone, address FROM customers WHERE customer_id = 'CUST999';

-- [B20] Xóa một cột rồi xóa cả dòng
DELETE email FROM customers WHERE customer_id = 'CUST999';
DELETE FROM customers WHERE customer_id = 'CUST999';
SELECT customer_id FROM customers WHERE customer_id = 'CUST999';
