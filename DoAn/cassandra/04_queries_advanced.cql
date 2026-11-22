-- =====================================================================
-- 04_queries_advanced.cql — Truy vấn NÂNG CAO (chỉ đọc; thang điểm mục 5 & 7)
-- Hàm tổng hợp COUNT/SUM/AVG/MIN/MAX, IN trên partition key, lọc khoảng + ORDER BY,
-- collection (map / list / set), ALLOW FILTERING trong một partition.
-- Chạy:  docker exec nosql-cassandra-doan cqlsh -f /doan/04_queries_advanced.cql
-- =====================================================================
USE ride_booking;

-- [A01] (Q10) Thu nhập tháng 10 của tài xế: chỉ tính chuyến COMPLETED.
--       ALLOW FILTERING ở đây an toàn vì đã cố định partition (driver_id, yyyymm) — chỉ lọc trong 1 partition.
SELECT COUNT(*) AS so_chuyen,
       SUM(fare) AS tong_cuoc,
       AVG(fare) AS cuoc_tb,
       MIN(fare) AS cuoc_thap_nhat,
       MAX(fare) AS cuoc_cao_nhat
FROM rides_by_driver_month
WHERE driver_id = 'DRV_551' AND yyyymm = 202610 AND status = 'COMPLETED'
ALLOW FILTERING;

-- [A02] (Q12) Doanh thu một ngày tại TP.HCM của một phương thức thanh toán
--       (payment_method là cột gom nhóm đầu tiên nên lọc bằng dấu = được)
SELECT COUNT(*) AS so_giao_dich, SUM(amount) AS doanh_thu, SUM(discount) AS tong_giam_gia
FROM payments_by_city_date
WHERE city = 'HCM' AND pay_date = '2026-10-03' AND payment_method = 'CASH';

-- [A03] (Q12) Doanh thu bảy ngày: IN trên partition key
--       (Cassandra cảnh báo "Aggregation query used on multiple partition keys" — chấp nhận được với vài partition)
SELECT COUNT(*) AS so_giao_dich, SUM(amount) AS doanh_thu
FROM payments_by_city_date
WHERE city = 'HCM'
  AND pay_date IN ('2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04');

-- [A04] (Q11, Q13) Thống kê một khu vực trong ngày: số chuyến, chuyến sớm nhất/muộn nhất, tổng cước
SELECT COUNT(*) AS so_chuyen, MIN(requested_at) AS som_nhat, MAX(requested_at) AS muon_nhat,
       SUM(fare) AS tong_cuoc
FROM rides_by_area_date
WHERE city = 'HCM' AND district = 'Q1' AND ride_date = '2026-10-04';

-- [A05] (Q15) Điểm đánh giá trung bình của tài xế
SELECT COUNT(*) AS so_danh_gia,
       AVG(stars) AS diem_tb,
       MIN(stars) AS thap_nhat,
       MAX(stars) AS cao_nhat
FROM ratings_by_driver
WHERE driver_id = 'DRV_555';

-- [A06] (Q5) Tìm tài xế rảnh ở nhiều quận lân cận cùng lúc (IN trên một phần của partition key)
SELECT district, driver_id, full_name, rating, vehicle_plate
FROM drivers_by_area
WHERE city = 'HCM' AND district IN ('Q1', 'Q3', 'BINH_THANH');

-- [A07] (Q11) Khoảng thời gian trên clustering column + đảo thứ tự sắp xếp bằng ORDER BY
SELECT requested_at, ride_id, customer_id, status
FROM rides_by_area_date
WHERE city = 'HCM' AND district = 'TAN_PHU' AND ride_date = '2026-09-28'
  AND requested_at >= '2026-09-28 06:00:00+0700' AND requested_at < '2026-09-28 18:00:00+0700'
ORDER BY requested_at ASC;

-- [A08] (Q8) Collection: map<timestamp,text> lịch sử trạng thái, list<text> tags, set<text> thành phố áp dụng
SELECT ride_id, status_history FROM rides WHERE ride_id = 'RIDE_1007';
SELECT ride_id, stars, tags FROM ratings_by_driver WHERE driver_id = 'DRV_551' LIMIT 2;
SELECT promo_code, cities FROM promotions WHERE promo_code IN ('GIAM20', 'HCMXANH', 'HANOI10');

-- [A09] (Q9) Lọc theo cột thường TRONG một partition: các chuyến đã hoàn thành của CUST001
SELECT ride_date, ride_id, fare, status
FROM rides_by_customer
WHERE customer_id = 'CUST001' AND status = 'COMPLETED'
ALLOW FILTERING;

-- [A10] (Q17) Truy vấn KHÔNG được phép nếu thiếu partition key — để thấy vì sao phải thiết kế theo truy vấn:
--       bỏ dấu -- ở dòng dưới sẽ nhận lỗi "Cannot execute this query as it might involve data filtering..."
-- SELECT * FROM rides WHERE customer_id = 'CUST001';
