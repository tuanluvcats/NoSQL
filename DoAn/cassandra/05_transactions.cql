-- =====================================================================
-- 05_transactions.cql — Các luồng GHI nghiệp vụ của ứng dụng (truy vấn nâng cao)
-- LWT (IF NOT EXISTS / IF điều kiện), logged BATCH nhiều bảng, counter,
-- TTL, cập nhật collection (map / list / set).
-- Kịch bản: 10:00–10:40 ngày 04/10/2026, khách CUST001 đặt chuyến RIDE_2001 ra sân bay.
-- Chạy MỘT lần sau 02_data.cql:
--     docker exec nosql-cassandra cqlsh -f /tmp/cassandra/05_transactions.cql
-- Chạy lại: các câu LWT sẽ trả [applied] = False (đúng thiết kế) nhưng các counter sẽ cộng thêm,
-- vì vậy muốn chạy lại từ đầu hãy dùng 99_reset_data.cql rồi nạp lại 02_data.cql.
-- =====================================================================
USE ride_booking;

-- [T01] (Q1) Đăng ký tài khoản: username phải là duy nhất → LWT INSERT ... IF NOT EXISTS
INSERT INTO customers (customer_id, full_name, phone, email, address, created_at)
VALUES ('CUST016', 'Trịnh Bảo Ngọc', '0901000016', 'ngoc.trinh@gmail.com', '27 Cộng Hòa, Tân Bình, TP.HCM', '2026-10-04 10:01:00+0700');
INSERT INTO user_accounts (username, password_hash, role, ref_id, full_name, is_active, created_at)
VALUES ('cust016', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'CUSTOMER', 'CUST016', 'Trịnh Bảo Ngọc', true, '2026-10-04 10:01:00+0700')
IF NOT EXISTS;
-- Người khác đăng ký trùng username → [applied] = False, Cassandra trả về dòng đang tồn tại
INSERT INTO user_accounts (username, password_hash, role, ref_id, full_name, is_active, created_at)
VALUES ('cust016', 'xxx', 'CUSTOMER', 'CUST999', 'Người Khác', true, '2026-10-04 10:01:30+0700')
IF NOT EXISTS;

-- [T02] (Q1) Ghi nhận đăng nhập; quản trị viên khóa / mở khóa tài khoản
UPDATE user_accounts SET last_login_at = '2026-10-04 10:02:00+0700' WHERE username = 'cust016';
UPDATE user_accounts SET is_active = false WHERE username = 'cust016' IF is_active = true;
UPDATE user_accounts SET is_active = true  WHERE username = 'cust016' IF is_active = false;

-- [T03] (Q5, Q14) Tài xế DRV_555 bật ứng dụng ở Quận 1: tín hiệu "đang rảnh" chỉ sống 300 giây.
--       Ứng dụng tài xế gửi lại tín hiệu mỗi phút; nếu mất kết nối, dòng tự biến mất khỏi kết quả tìm tài xế.
BEGIN BATCH
  UPDATE drivers SET status = 'AVAILABLE' WHERE driver_id = 'DRV_555';
  INSERT INTO drivers_by_area (city, district, driver_id, full_name, phone, rating, vehicle, location, last_seen)
  VALUES ('HCM', 'Q1', 'DRV_555', 'Nguyễn Hữu Thắng', '0912000555', 4.5,
          {vehicle_id: 'VEH_555', license_plate: '51K-567.89', model: 'Toyota Innova', color: 'Xám'},
          {lat: 10.7815, lng: 106.6985}, '2026-10-04 10:04:00+0700')
  USING TTL 300;
APPLY BATCH;
INSERT INTO driver_locations (driver_id, day, ts, location, speed_kmh)
VALUES ('DRV_555', '2026-10-04', '2026-10-04 10:04:00+0700', {lat: 10.7815, lng: 106.6985}, 0.0);
SELECT driver_id, full_name, rating, TTL(last_seen) AS con_song_giay
FROM drivers_by_area WHERE city = 'HCM' AND district = 'Q1';

-- [T04] (Q6) Khách CUST001 đặt chuyến RIDE_2001. IF NOT EXISTS chống tạo trùng khi ứng dụng gửi lại yêu cầu.
INSERT INTO rides (ride_id, customer_id, customer_name, customer_phone, city, district,
                   pickup_address, destination_address, pickup_point, dropoff_point,
                   distance_km, fare, discount, payment_method, status, ride_date, requested_at, status_history)
VALUES ('RIDE_2001', 'CUST001', 'Nguyễn Văn An', '0901000001', 'HCM', 'Q1',
        '456 Lê Duẩn, Q1', 'Sân bay Tân Sơn Nhất, Tân Bình', {lat: 10.782, lng: 106.699}, {lat: 10.8185, lng: 106.6588},
        8.1, 81000.0, 0.0, 'MOMO', 'REQUESTED', '2026-10-04', '2026-10-04 10:05:00+0700',
        {'2026-10-04 10:05:00+0700': 'REQUESTED'})
IF NOT EXISTS;
BEGIN BATCH
  INSERT INTO rides_by_customer (customer_id, ride_date, ride_id, pickup_address, destination_address, driver_id, fare, status)
  VALUES ('CUST001', '2026-10-04', 'RIDE_2001', '456 Lê Duẩn, Q1', 'Sân bay Tân Sơn Nhất, Tân Bình', null, 81000.0, 'REQUESTED');
  INSERT INTO rides_by_area_date (city, district, ride_date, requested_at, ride_id, customer_id, driver_id,
                                  pickup_address, destination_address, fare, status, payment_method)
  VALUES ('HCM', 'Q1', '2026-10-04', '2026-10-04 10:05:00+0700', 'RIDE_2001', 'CUST001', null,
          '456 Lê Duẩn, Q1', 'Sân bay Tân Sơn Nhất, Tân Bình', 81000.0, 'REQUESTED', 'MOMO');
APPLY BATCH;
UPDATE ride_stats_by_city SET rides_requested = rides_requested + 1
WHERE city = 'HCM' AND yyyymm = 202610 AND ride_date = '2026-10-04';

-- [T05] (Q7) Hai tài xế cùng bấm "Nhận chuyến": LWT trên cột thường status bảo đảm chỉ MỘT người thắng.
UPDATE rides SET driver_id = 'DRV_555', driver_name = 'Nguyễn Hữu Thắng',
                 vehicle = {vehicle_id: 'VEH_555', license_plate: '51K-567.89', model: 'Toyota Innova', color: 'Xám'},
                 status = 'ACCEPTED', accepted_at = '2026-10-04 10:06:00+0700',
                 status_history = status_history + {'2026-10-04 10:06:00+0700': 'ACCEPTED'}
WHERE ride_id = 'RIDE_2001' IF status = 'REQUESTED';
-- Tài xế DRV_554 bấm chậm hơn vài mili giây → [applied] = False, kèm status hiện tại là ACCEPTED
UPDATE rides SET driver_id = 'DRV_554', driver_name = 'Phan Văn Tài', status = 'ACCEPTED',
                 accepted_at = '2026-10-04 10:06:01+0700'
WHERE ride_id = 'RIDE_2001' IF status = 'REQUESTED';
-- Người thắng: cập nhật mọi bảng phi chuẩn hóa trong MỘT logged BATCH (hoặc tất cả, hoặc không)
BEGIN BATCH
  UPDATE rides_by_customer SET driver_id = 'DRV_555', status = 'ACCEPTED'
  WHERE customer_id = 'CUST001' AND ride_date = '2026-10-04' AND ride_id = 'RIDE_2001';
  UPDATE rides_by_area_date SET driver_id = 'DRV_555', status = 'ACCEPTED'
  WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04'
    AND requested_at = '2026-10-04 10:05:00+0700' AND ride_id = 'RIDE_2001';
  INSERT INTO rides_by_driver_month (driver_id, yyyymm, requested_at, ride_id, driver_name, vehicle_plate,
                                     customer_id, pickup_address, destination_address, distance_km, fare, status)
  VALUES ('DRV_555', 202610, '2026-10-04 10:05:00+0700', 'RIDE_2001', 'Nguyễn Hữu Thắng', '51K-567.89',
          'CUST001', '456 Lê Duẩn, Q1', 'Sân bay Tân Sơn Nhất, Tân Bình', 8.1, 81000.0, 'ACCEPTED');
  UPDATE drivers SET status = 'BUSY' WHERE driver_id = 'DRV_555';
  DELETE FROM drivers_by_area WHERE city = 'HCM' AND district = 'Q1' AND driver_id = 'DRV_555';
APPLY BATCH;

-- [T06] Bắt đầu chuyến (chỉ tài xế đã nhận mới chuyển được sang ONGOING)
UPDATE rides SET status = 'ONGOING', started_at = '2026-10-04 10:12:00+0700',
                 status_history = status_history + {'2026-10-04 10:12:00+0700': 'ONGOING'}
WHERE ride_id = 'RIDE_2001' IF status = 'ACCEPTED' AND driver_id = 'DRV_555';
BEGIN BATCH
  UPDATE rides_by_customer SET status = 'ONGOING'
  WHERE customer_id = 'CUST001' AND ride_date = '2026-10-04' AND ride_id = 'RIDE_2001';
  UPDATE rides_by_area_date SET status = 'ONGOING'
  WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04'
    AND requested_at = '2026-10-04 10:05:00+0700' AND ride_id = 'RIDE_2001';
  UPDATE rides_by_driver_month SET status = 'ONGOING'
  WHERE driver_id = 'DRV_555' AND yyyymm = 202610 AND requested_at = '2026-10-04 10:05:00+0700' AND ride_id = 'RIDE_2001';
APPLY BATCH;
INSERT INTO driver_locations (driver_id, day, ts, location, speed_kmh)
VALUES ('DRV_555', '2026-10-04', '2026-10-04 10:20:00+0700', {lat: 10.7995, lng: 106.6790}, 34.0);

-- [T07] (Q16) Áp mã GIAM20 — tăng used_count có điều kiện (optimistic locking bằng LWT).
--       Ứng dụng đọc used_count (= 5 trong dữ liệu mẫu) rồi ghi 6 kèm IF used_count = 5.
--       USING TTL được ghi lại để cột used_count hết hạn cùng lúc với mã khuyến mãi.
SELECT promo_code, used_count, usage_limit FROM promotions WHERE promo_code = 'GIAM20';
UPDATE promotions USING TTL 7776000 SET used_count = 6 WHERE promo_code = 'GIAM20' IF used_count = 5;
-- Một yêu cầu khác cũng đọc được 5 và ghi muộn hơn → [applied] = False, phải đọc lại và thử lại
UPDATE promotions USING TTL 7776000 SET used_count = 6 WHERE promo_code = 'GIAM20' IF used_count = 5;

-- [T08] Hoàn thành chuyến: giảm 20% (tối đa 30.000đ) → giảm 16.000đ, khách trả 65.000đ qua MoMo
UPDATE rides SET status = 'COMPLETED', completed_at = '2026-10-04 10:35:00+0700',
                 promo_code = 'GIAM20', discount = 16000.0,
                 status_history = status_history + {'2026-10-04 10:35:00+0700': 'COMPLETED'}
WHERE ride_id = 'RIDE_2001' IF status = 'ONGOING';
BEGIN BATCH
  UPDATE rides_by_customer SET status = 'COMPLETED'
  WHERE customer_id = 'CUST001' AND ride_date = '2026-10-04' AND ride_id = 'RIDE_2001';
  UPDATE rides_by_area_date SET status = 'COMPLETED'
  WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04'
    AND requested_at = '2026-10-04 10:05:00+0700' AND ride_id = 'RIDE_2001';
  UPDATE rides_by_driver_month SET status = 'COMPLETED'
  WHERE driver_id = 'DRV_555' AND yyyymm = 202610 AND requested_at = '2026-10-04 10:05:00+0700' AND ride_id = 'RIDE_2001';
  INSERT INTO payments_by_city_date (city, pay_date, payment_method, paid_at, ride_id, customer_id, driver_id, district, amount, discount)
  VALUES ('HCM', '2026-10-04', 'MOMO', '2026-10-04 10:35:00+0700', 'RIDE_2001', 'CUST001', 'DRV_555', 'Q1', 65000.0, 16000.0);
  UPDATE drivers SET status = 'AVAILABLE' WHERE driver_id = 'DRV_555';
  INSERT INTO drivers_by_area (city, district, driver_id, full_name, phone, rating, vehicle, location, last_seen)
  VALUES ('HCM', 'TAN_BINH', 'DRV_555', 'Nguyễn Hữu Thắng', '0912000555', 4.5,
          {vehicle_id: 'VEH_555', license_plate: '51K-567.89', model: 'Toyota Innova', color: 'Xám'},
          {lat: 10.8185, lng: 106.6588}, '2026-10-04 10:35:00+0700')
  USING TTL 300;
APPLY BATCH;
UPDATE ride_stats_by_city SET rides_completed = rides_completed + 1
WHERE city = 'HCM' AND yyyymm = 202610 AND ride_date = '2026-10-04';

-- [T09] (Q15) Khách đánh giá 5 sao → thêm tag vào list → tính lại điểm trung bình của tài xế
INSERT INTO ratings_by_driver (driver_id, rated_at, ride_id, customer_id, stars, comment, tags)
VALUES ('DRV_555', '2026-10-04 10:40:00+0700', 'RIDE_2001', 'CUST001', 5, 'Ra sân bay đúng giờ', ['Đúng giờ']);
UPDATE ratings_by_driver SET tags = tags + ['Lịch sự']
WHERE driver_id = 'DRV_555' AND rated_at = '2026-10-04 10:40:00+0700' AND ride_id = 'RIDE_2001';
SELECT COUNT(*) AS so_danh_gia, AVG(CAST(stars AS double)) AS diem_tb
FROM ratings_by_driver WHERE driver_id = 'DRV_555';
-- Ứng dụng lấy kết quả AVG ở trên (14/3 = 4.67) rồi ghi vào hồ sơ tài xế
UPDATE drivers SET rating = 4.67 WHERE driver_id = 'DRV_555';

-- [T10] Hủy chuyến khi chưa có tài xế: RIDE_2002 của CUST006 tại Tân Phú (LWT với IF ... IN)
INSERT INTO rides (ride_id, customer_id, customer_name, customer_phone, city, district,
                   pickup_address, destination_address, pickup_point, dropoff_point,
                   distance_km, fare, discount, payment_method, status, ride_date, requested_at, status_history)
VALUES ('RIDE_2002', 'CUST006', 'Võ Ngọc Hân', '0901000006', 'HCM', 'TAN_PHU',
        '140 Lê Trọng Tấn, Tân Phú', 'Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng', {lat: 10.8066, lng: 106.6283}, {lat: 10.8015, lng: 106.6176},
        1.8, 27000.0, 0.0, 'CASH', 'REQUESTED', '2026-10-04', '2026-10-04 10:20:00+0700',
        {'2026-10-04 10:20:00+0700': 'REQUESTED'})
IF NOT EXISTS;
BEGIN BATCH
  INSERT INTO rides_by_customer (customer_id, ride_date, ride_id, pickup_address, destination_address, driver_id, fare, status)
  VALUES ('CUST006', '2026-10-04', 'RIDE_2002', '140 Lê Trọng Tấn, Tân Phú', 'Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng', null, 27000.0, 'REQUESTED');
  INSERT INTO rides_by_area_date (city, district, ride_date, requested_at, ride_id, customer_id, driver_id,
                                  pickup_address, destination_address, fare, status, payment_method)
  VALUES ('HCM', 'TAN_PHU', '2026-10-04', '2026-10-04 10:20:00+0700', 'RIDE_2002', 'CUST006', null,
          '140 Lê Trọng Tấn, Tân Phú', 'Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng', 27000.0, 'REQUESTED', 'CASH');
APPLY BATCH;
UPDATE ride_stats_by_city SET rides_requested = rides_requested + 1
WHERE city = 'HCM' AND yyyymm = 202610 AND ride_date = '2026-10-04';
UPDATE rides SET status = 'CANCELLED', cancel_reason = 'Khách đổi ý',
                 status_history = status_history + {'2026-10-04 10:23:00+0700': 'CANCELLED'}
WHERE ride_id = 'RIDE_2002' IF status IN ('REQUESTED', 'ACCEPTED');
BEGIN BATCH
  UPDATE rides_by_customer SET status = 'CANCELLED'
  WHERE customer_id = 'CUST006' AND ride_date = '2026-10-04' AND ride_id = 'RIDE_2002';
  UPDATE rides_by_area_date SET status = 'CANCELLED'
  WHERE city = 'HCM' AND district = 'TAN_PHU' AND ride_date = '2026-10-04'
    AND requested_at = '2026-10-04 10:20:00+0700' AND ride_id = 'RIDE_2002';
APPLY BATCH;
UPDATE ride_stats_by_city SET rides_cancelled = rides_cancelled + 1
WHERE city = 'HCM' AND yyyymm = 202610 AND ride_date = '2026-10-04';

-- [T11] Collection set: mở rộng mã GIAM20 sang Đà Nẵng rồi thu hồi
UPDATE promotions SET cities = cities + {'DN'} WHERE promo_code = 'GIAM20';
SELECT promo_code, cities FROM promotions WHERE promo_code = 'GIAM20';
UPDATE promotions SET cities = cities - {'DN'} WHERE promo_code = 'GIAM20';

-- [T12] Kiểm tra lại kết quả sau toàn bộ kịch bản
SELECT ride_id, status, driver_id, fare, discount, promo_code, status_history FROM rides WHERE ride_id IN ('RIDE_2001', 'RIDE_2002');
SELECT ride_date, ride_id, driver_id, fare, status FROM rides_by_customer WHERE customer_id = 'CUST001' AND ride_date = '2026-10-04';
SELECT ride_date, rides_requested, rides_completed, rides_cancelled
FROM ride_stats_by_city WHERE city = 'HCM' AND yyyymm = 202610 AND ride_date = '2026-10-04';
SELECT driver_id, rating, status FROM drivers WHERE driver_id = 'DRV_555';
