-- =====================================================================
-- 99_reset_data.cql — XÓA SẠCH DỮ LIỆU (giữ nguyên cấu trúc bảng) của keyspace ride_booking
-- Dùng khi: (1) muốn bỏ 100 dòng dữ liệu ngẫu nhiên do DbSchema Data Generator sinh ra
--           trong báo cáo giữa kỳ, hoặc (2) muốn chạy lại 02_data.cql / 05_transactions.cql từ đầu.
-- An toàn: auto_snapshot = true nên mỗi TRUNCATE tự tạo snapshot "truncated-..." trước khi xóa
--          (xem bằng: docker exec nosql-cassandra nodetool listsnapshots).
-- Nên chụp snapshot chủ động trước:  docker exec nosql-cassandra nodetool snapshot -t truoc_reset ride_booking
-- Chạy:  docker exec nosql-cassandra cqlsh -f /tmp/cassandra/99_reset_data.cql
-- =====================================================================
USE ride_booking;
TRUNCATE customers;
TRUNCATE drivers;
TRUNCATE vehicles;
TRUNCATE rides_by_customer;
TRUNCATE user_accounts;
TRUNCATE rides;
TRUNCATE rides_by_driver_month;
TRUNCATE rides_by_area_date;
TRUNCATE drivers_by_area;
TRUNCATE driver_locations;
TRUNCATE ratings_by_driver;
TRUNCATE payments_by_city_date;
TRUNCATE promotions;
TRUNCATE ride_stats_by_city;
