-- =====================================================================
-- 04_queries_advanced.cql — Truy vấn NÂNG CAO (chỉ đọc; thang điểm mục 5 & 7)
-- Hàm tổng hợp + GROUP BY, nhóm theo khung giờ, PER PARTITION LIMIT,
-- IN trên partition key, phân trang bằng token(), DISTINCT, cột static,
-- collection, UDT, TTL/WRITETIME, JSON, CAST, ALLOW FILTERING trong một partition.
-- Chạy:  docker exec nosql-cassandra cqlsh -f /tmp/cassandra/04_queries_advanced.cql
-- =====================================================================
USE ride_booking;

-- [A01] (Q10) Thu nhập tháng 10 của tài xế: chỉ tính chuyến COMPLETED.
--       ALLOW FILTERING ở đây an toàn vì đã cố định partition (driver_id, yyyymm) — chỉ lọc trong 1 partition.
SELECT COUNT(*) AS so_chuyen,
       CAST(SUM(fare) AS bigint) AS tong_cuoc,
       CAST(AVG(fare) AS bigint) AS cuoc_tb,
       MIN(fare) AS cuoc_thap_nhat,
       MAX(fare) AS cuoc_cao_nhat
FROM rides_by_driver_month
WHERE driver_id = 'DRV_551' AND yyyymm = 202610 AND status = 'COMPLETED'
ALLOW FILTERING;

-- [A02] (Q12) Doanh thu một ngày tại TP.HCM theo phương thức thanh toán (GROUP BY clustering column)
SELECT payment_method,
       COUNT(*) AS so_giao_dich,
       CAST(SUM(amount) AS bigint) AS doanh_thu,
       CAST(SUM(discount) AS bigint) AS tong_giam_gia
FROM payments_by_city_date
WHERE city = 'HCM' AND pay_date = '2026-10-03'
GROUP BY payment_method;

-- [A03] (Q12) Doanh thu nhiều ngày: IN trên partition key + GROUP BY theo ngày
--       (Cassandra cảnh báo "Aggregation query used on multiple partition keys" — chấp nhận được với vài partition)
SELECT pay_date, COUNT(*) AS so_giao_dich, CAST(SUM(amount) AS bigint) AS doanh_thu
FROM payments_by_city_date
WHERE city = 'HCM'
  AND pay_date IN ('2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04')
GROUP BY pay_date;

-- [A04] (Q11) Số chuyến theo từng khung giờ trong ngày tại một khu vực (GROUP BY floor() — có từ Cassandra 4.1)
SELECT floor(requested_at, 1h) AS khung_gio, COUNT(*) AS so_chuyen
FROM rides_by_area_date
WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04'
GROUP BY floor(requested_at, 1h);

-- [A05] (Q13) Tổng số chuyến cả tháng từ bảng counter
SELECT SUM(rides_requested) AS dat, SUM(rides_completed) AS hoan_thanh, SUM(rides_cancelled) AS huy
FROM ride_stats_by_city
WHERE city = 'HCM' AND yyyymm = 202610;

-- [A06] (Q15) Điểm đánh giá trung bình của tài xế (CAST sang double để AVG không chia nguyên)
SELECT COUNT(*) AS so_danh_gia,
       AVG(CAST(stars AS double)) AS diem_tb,
       MIN(stars) AS thap_nhat,
       MAX(stars) AS cao_nhat
FROM ratings_by_driver
WHERE driver_id = 'DRV_555';

-- [A07] (Q15) Đánh giá MỚI NHẤT của MỖI tài xế (PER PARTITION LIMIT 1, clustering rated_at DESC)
SELECT driver_id, rated_at, stars, comment
FROM ratings_by_driver
PER PARTITION LIMIT 1;

-- [A08] (Q5) Tìm tài xế rảnh ở nhiều quận lân cận cùng lúc (IN trên một phần của partition key)
SELECT district, driver_id, full_name, rating, vehicle.model, vehicle.license_plate
FROM drivers_by_area
WHERE city = 'HCM' AND district IN ('Q1', 'Q3', 'BINH_THANH');

-- [A09] (Q11) Khoảng thời gian trên clustering column + đảo thứ tự sắp xếp bằng ORDER BY
SELECT requested_at, ride_id, customer_id, status
FROM rides_by_area_date
WHERE city = 'HCM' AND district = 'TAN_PHU' AND ride_date = '2026-09-28'
  AND requested_at >= '2026-09-28 06:00:00+0700' AND requested_at < '2026-09-28 18:00:00+0700'
ORDER BY requested_at ASC;

-- [A10] (Q10) Cột STATIC: tên tài xế và biển số lưu MỘT lần cho cả partition (driver_id, yyyymm)
SELECT DISTINCT driver_id, yyyymm, driver_name, vehicle_plate
FROM rides_by_driver_month
WHERE driver_id = 'DRV_551' AND yyyymm = 202610;

-- [A11] (Q8) UDT: truy cập từng trường của frozen<vehicle_info> và frozen<geo_point>
SELECT ride_id, vehicle.license_plate, vehicle.model, pickup_point.lat, pickup_point.lng, dropoff_point
FROM rides WHERE ride_id = 'RIDE_1001';

-- [A12] (Q8) Collection: map<timestamp,text> lịch sử trạng thái, list<text> tags, set<text> thành phố áp dụng
SELECT ride_id, status_history FROM rides WHERE ride_id = 'RIDE_1007';
SELECT ride_id, stars, tags FROM ratings_by_driver WHERE driver_id = 'DRV_551' LIMIT 2;
SELECT promo_code, cities FROM promotions WHERE promo_code IN ('GIAM20', 'HCMXANH', 'HANOI10');

-- [A13] (Q16, Q14) TTL và WRITETIME: thời gian sống còn lại (giây) và thời điểm ghi (micro giây)
SELECT promo_code, TTL(description) AS con_lai_giay, WRITETIME(description) AS ghi_luc
FROM promotions WHERE promo_code = 'GIAM20';
SELECT ts, TTL(speed_kmh) AS con_lai_giay
FROM driver_locations WHERE driver_id = 'DRV_559' AND day = '2026-10-04' LIMIT 2;

-- [A14] (Q18) Phân trang toàn bảng customers theo token (thứ tự là thứ tự token Murmur3, không theo tên)
SELECT token(customer_id) AS tk, customer_id, full_name FROM customers LIMIT 5;
-- Trang tiếp theo: điều kiện token(...) > token(<customer_id cuối cùng của trang trước>) — ở đây là CUST010
SELECT token(customer_id) AS tk, customer_id, full_name FROM customers
WHERE token(customer_id) > token('CUST010') LIMIT 5;

-- [A15] (Q11) Liệt kê các partition (khu vực + ngày) đang có dữ liệu — DISTINCT trên partition key
SELECT DISTINCT city, district, ride_date FROM rides_by_area_date LIMIT 10;

-- [A16] (Q9) Lọc theo cột thường TRONG một partition: các chuyến đã hoàn thành của CUST001
SELECT ride_date, ride_id, fare, status
FROM rides_by_customer
WHERE customer_id = 'CUST001' AND status = 'COMPLETED'
ALLOW FILTERING;

-- [A17] (Q8) JSON, CAST và hàm thời gian
SELECT JSON ride_id, fare, status, vehicle FROM rides WHERE ride_id = 'RIDE_1001';
SELECT ride_id, CAST(fare AS bigint) AS cuoc, toDate(requested_at) AS ngay,
       toUnixTimestamp(requested_at) AS epoch_ms
FROM rides WHERE ride_id IN ('RIDE_1001', 'RIDE_1025');

-- [A18] (Q17) Truy vấn KHÔNG được phép nếu thiếu partition key — để thấy vì sao phải thiết kế theo truy vấn:
--       bỏ dấu -- ở dòng dưới sẽ nhận lỗi "Cannot execute this query as it might involve data filtering..."
-- SELECT * FROM rides WHERE customer_id = 'CUST001';
