-- =====================================================================
-- 01_schema.cql  —  Keyspace ride_booking (Quản lý dữ liệu đặt xe công nghệ)
-- Cassandra 4.1 (image cassandra:4.1 trong docker-compose.yml)
-- Chạy:  docker exec nosql-cassandra cqlsh -f /tmp/cassandra/01_schema.cql
-- Mọi lệnh đều dùng IF NOT EXISTS nên chạy lại nhiều lần không lỗi và
-- KHÔNG thay đổi 4 bảng đã tạo trong báo cáo giữa kỳ.
-- =====================================================================

CREATE KEYSPACE IF NOT EXISTS ride_booking
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
  AND durable_writes = true;

USE ride_booking;

-- ---------------------------------------------------------------------
-- Kiểu dữ liệu do người dùng định nghĩa (UDT)
-- ---------------------------------------------------------------------
CREATE TYPE IF NOT EXISTS geo_point (
  lat double,
  lng double
);

CREATE TYPE IF NOT EXISTS vehicle_info (
  vehicle_id    text,
  license_plate text,
  model         text,
  color         text
);

-- ---------------------------------------------------------------------
-- NHÓM 1. Bốn bảng đã có trong báo cáo giữa kỳ (giữ nguyên cấu trúc)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
  customer_id text PRIMARY KEY,
  address     text,
  created_at  timestamp,
  email       text,
  full_name   text,
  phone       text
);

CREATE TABLE IF NOT EXISTS drivers (
  driver_id      text PRIMARY KEY,
  full_name      text,
  license_number text,
  phone          text,
  rating         double,
  status         text
);

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id    text PRIMARY KEY,
  driver_id     text,
  license_plate text,
  model         text,
  color         text
);

CREATE TABLE IF NOT EXISTS rides_by_customer (
  customer_id         text,
  ride_date           date,
  ride_id             text,
  destination_address text,
  driver_id           text,
  fare                double,
  pickup_address      text,
  status              text,
  PRIMARY KEY ((customer_id), ride_date, ride_id)
);

-- Chỉ mục phụ (secondary index) trên bảng nhỏ vehicles: tra xe theo tài xế / biển số
CREATE INDEX IF NOT EXISTS vehicles_driver_id_idx     ON vehicles (driver_id);
CREATE INDEX IF NOT EXISTS vehicles_license_plate_idx ON vehicles (license_plate);

-- ---------------------------------------------------------------------
-- NHÓM 2. Tài khoản đăng nhập (quản trị người dùng)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_accounts (
  username      text PRIMARY KEY,
  password_hash text,
  role          text,        -- ADMIN | OPERATOR | CUSTOMER | DRIVER
  ref_id        text,        -- customer_id hoặc driver_id tương ứng
  full_name     text,
  is_active     boolean,
  created_at    timestamp,
  last_login_at timestamp
) WITH comment = 'Q1. Đăng nhập: tìm tài khoản theo username (LWT IF NOT EXISTS khi đăng ký)';

-- ---------------------------------------------------------------------
-- NHÓM 3. Chuyến đi (bảng gốc + các bảng phi chuẩn hóa theo truy vấn)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rides (
  ride_id             text PRIMARY KEY,
  customer_id         text,
  customer_name       text,
  customer_phone      text,
  driver_id           text,
  driver_name         text,
  vehicle             frozen<vehicle_info>,
  city                text,
  district            text,
  pickup_address      text,
  destination_address text,
  pickup_point        frozen<geo_point>,
  dropoff_point       frozen<geo_point>,
  distance_km         double,
  fare                double,
  discount            double,
  promo_code          text,
  payment_method      text,  -- CASH | MOMO | ZALOPAY | CARD
  status              text,  -- REQUESTED | ACCEPTED | ONGOING | COMPLETED | CANCELLED
  ride_date           date,
  requested_at        timestamp,
  accepted_at         timestamp,
  started_at          timestamp,
  completed_at        timestamp,
  cancel_reason       text,
  status_history      map<timestamp, text>
) WITH comment = 'Q6 đặt xe (LWT IF NOT EXISTS), Q7 nhận chuyến (LWT IF status), Q8 chi tiết chuyến theo ride_id';

CREATE TABLE IF NOT EXISTS rides_by_driver_month (
  driver_id           text,
  yyyymm              int,
  requested_at        timestamp,
  ride_id             text,
  driver_name         text static,
  vehicle_plate       text static,
  customer_id         text,
  pickup_address      text,
  destination_address text,
  distance_km         double,
  fare                double,
  status              text,
  PRIMARY KEY ((driver_id, yyyymm), requested_at, ride_id)
) WITH CLUSTERING ORDER BY (requested_at DESC, ride_id ASC)
  AND comment = 'Q10. Lịch sử chuyến và thu nhập của tài xế theo tháng, mới nhất trước';

CREATE TABLE IF NOT EXISTS rides_by_area_date (
  city                text,
  district            text,
  ride_date           date,
  requested_at        timestamp,
  ride_id             text,
  customer_id         text,
  driver_id           text,
  pickup_address      text,
  destination_address text,
  fare                double,
  status              text,
  payment_method      text,
  PRIMARY KEY ((city, district, ride_date), requested_at, ride_id)
) WITH CLUSTERING ORDER BY (requested_at DESC, ride_id ASC)
  AND comment = 'Q11. Điều phối: các chuyến trong một khu vực (thành phố + quận) theo ngày';

-- ---------------------------------------------------------------------
-- NHÓM 4. Tài xế trực tuyến và vị trí GPS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drivers_by_area (
  city      text,
  district  text,
  driver_id text,
  full_name text,
  phone     text,
  rating    double,
  vehicle   frozen<vehicle_info>,
  location  frozen<geo_point>,
  last_seen timestamp,
  PRIMARY KEY ((city, district), driver_id)
) WITH comment = 'Q5. Tài xế đang rảnh trong một khu vực; ứng dụng ghi lại mỗi lần tài xế gửi tín hiệu (USING TTL)';

CREATE TABLE IF NOT EXISTS driver_locations (
  driver_id text,
  day       date,
  ts        timestamp,
  location  frozen<geo_point>,
  speed_kmh double,
  PRIMARY KEY ((driver_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 86400
  AND compaction = {'class': 'TimeWindowCompactionStrategy',
                    'compaction_window_unit': 'HOURS',
                    'compaction_window_size': 1}
  AND comment = 'Q14. Vị trí GPS mới nhất và lộ trình trong ngày của tài xế (tự xóa sau 24 giờ)';

-- ---------------------------------------------------------------------
-- NHÓM 5. Đánh giá, thanh toán, khuyến mãi, thống kê
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ratings_by_driver (
  driver_id   text,
  rated_at    timestamp,
  ride_id     text,
  customer_id text,
  stars       int,
  comment     text,
  tags        list<text>,
  PRIMARY KEY ((driver_id), rated_at, ride_id)
) WITH CLUSTERING ORDER BY (rated_at DESC, ride_id ASC)
  AND comment = 'Q15. Đánh giá của một tài xế, mới nhất trước; AVG(stars)';

CREATE TABLE IF NOT EXISTS payments_by_city_date (
  city           text,
  pay_date       date,
  payment_method text,
  paid_at        timestamp,
  ride_id        text,
  customer_id    text,
  driver_id      text,
  district       text,
  amount         double,
  discount       double,
  PRIMARY KEY ((city, pay_date), payment_method, paid_at, ride_id)
) WITH CLUSTERING ORDER BY (payment_method ASC, paid_at DESC, ride_id ASC)
  AND comment = 'Q12. Doanh thu theo ngày của thành phố, nhóm theo phương thức thanh toán (GROUP BY)';

CREATE TABLE IF NOT EXISTS promotions (
  promo_code       text PRIMARY KEY,
  description      text,
  discount_percent int,
  max_discount     double,
  min_fare         double,
  cities           set<text>,
  usage_limit      int,
  used_count       int,
  valid_from       timestamp,
  valid_to         timestamp
) WITH comment = 'Q16. Kiểm tra và áp dụng mã khuyến mãi (TTL tự hết hạn, LWT trên used_count)';

CREATE TABLE IF NOT EXISTS ride_stats_by_city (
  city            text,
  yyyymm          int,
  ride_date       date,
  rides_requested counter,
  rides_completed counter,
  rides_cancelled counter,
  PRIMARY KEY ((city, yyyymm), ride_date)
) WITH comment = 'Q13. Số chuyến đặt / hoàn thành / hủy theo ngày trong tháng (counter)';
