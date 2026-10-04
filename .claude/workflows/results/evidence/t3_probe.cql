-- Task 3 probe: Cassandra 4.1 behaviour checks (run with cqlsh -f, errors are expected for some lines)
CREATE KEYSPACE IF NOT EXISTS probe WITH replication = {'class':'SimpleStrategy','replication_factor':1};
USE probe;

-- [1] Materialized view (expected: disabled)
CREATE TABLE IF NOT EXISTS rides (ride_id uuid PRIMARY KEY, customer_id text, driver_id text, status text, fare bigint, booked_at timestamp);
CREATE MATERIALIZED VIEW rides_by_status AS SELECT * FROM rides WHERE status IS NOT NULL AND ride_id IS NOT NULL PRIMARY KEY (status, ride_id);

-- [2] SAI (5.0) and SASI (experimental, disabled)
CREATE INDEX rides_status_sai ON rides (status) USING 'StorageAttachedIndex';
CREATE CUSTOM INDEX rides_status_sasi ON rides (status) USING 'org.apache.cassandra.index.sasi.SASIIndex';
-- legacy secondary index (enabled)
CREATE INDEX IF NOT EXISTS rides_status_2i ON rides (status);

-- [3] UDF (expected: disabled)
CREATE FUNCTION vnd_to_k (v bigint) RETURNS NULL ON NULL INPUT RETURNS bigint LANGUAGE java AS 'return v / 1000;';

-- [4] aggregates + GROUP BY
CREATE TABLE IF NOT EXISTS rides_by_customer (customer_id text, booked_at timestamp, ride_id uuid, driver_id text, status text, fare bigint, PRIMARY KEY ((customer_id), booked_at, ride_id)) WITH CLUSTERING ORDER BY (booked_at DESC, ride_id ASC);
INSERT INTO rides_by_customer (customer_id, booked_at, ride_id, driver_id, status, fare) VALUES ('CUST001', '2026-09-01 08:00:00+0000', 11111111-1111-1111-1111-111111111111, 'DRV01', 'COMPLETED', 52000);
INSERT INTO rides_by_customer (customer_id, booked_at, ride_id, driver_id, status, fare) VALUES ('CUST001', '2026-09-02 09:00:00+0000', 22222222-2222-2222-2222-222222222222, 'DRV02', 'COMPLETED', 87000);
INSERT INTO rides_by_customer (customer_id, booked_at, ride_id, driver_id, status, fare) VALUES ('CUST001', '2026-09-02 18:00:00+0000', 33333333-3333-3333-3333-333333333333, 'DRV01', 'CANCELLED', 0);
INSERT INTO rides_by_customer (customer_id, booked_at, ride_id, driver_id, status, fare) VALUES ('CUST002', '2026-09-03 10:00:00+0000', 44444444-4444-4444-4444-444444444444, 'DRV03', 'COMPLETED', 120000);
SELECT customer_id, COUNT(*) AS n, SUM(fare) AS total, AVG(fare) AS avg_fare, MIN(fare), MAX(fare) FROM rides_by_customer GROUP BY customer_id;
SELECT customer_id, booked_at, COUNT(*) FROM rides_by_customer WHERE customer_id = 'CUST001' GROUP BY customer_id, booked_at;
-- GROUP BY on a regular column (expected error)
SELECT status, COUNT(*) FROM rides_by_customer GROUP BY status;
-- GROUP BY skipping the partition key (expected error)
SELECT booked_at, COUNT(*) FROM rides_by_customer GROUP BY booked_at;
-- GROUP BY time bucket with floor() (5.0 feature, expected error in 4.1)
SELECT customer_id, floor(booked_at, 1d), COUNT(*) FROM rides_by_customer WHERE customer_id = 'CUST001' GROUP BY customer_id, floor(booked_at, 1d);
-- AVG on bigint is integer division (52000+87000+0)/3
SELECT AVG(fare), AVG(CAST(fare AS double)) FROM rides_by_customer WHERE customer_id = 'CUST001';

-- [5] PER PARTITION LIMIT, token() paging, ALLOW FILTERING
SELECT customer_id, booked_at, fare FROM rides_by_customer PER PARTITION LIMIT 1;
SELECT customer_id, token(customer_id) FROM rides_by_customer PER PARTITION LIMIT 1;
SELECT customer_id, booked_at FROM rides_by_customer WHERE token(customer_id) > token('CUST001') LIMIT 10;
SELECT * FROM rides_by_customer WHERE fare > 50000;
SELECT customer_id, fare FROM rides_by_customer WHERE fare > 50000 ALLOW FILTERING;
SELECT customer_id, fare FROM rides_by_customer WHERE customer_id = 'CUST001' AND status = 'COMPLETED' ALLOW FILTERING;

-- [6] LWT
INSERT INTO rides (ride_id, customer_id, status, fare) VALUES (55555555-5555-5555-5555-555555555555, 'CUST001', 'REQUESTED', 60000) IF NOT EXISTS;
INSERT INTO rides (ride_id, customer_id, status, fare) VALUES (55555555-5555-5555-5555-555555555555, 'CUST009', 'REQUESTED', 1) IF NOT EXISTS;
UPDATE rides SET driver_id = 'DRV01', status = 'ACCEPTED' WHERE ride_id = 55555555-5555-5555-5555-555555555555 IF status = 'REQUESTED';
UPDATE rides SET driver_id = 'DRV02', status = 'ACCEPTED' WHERE ride_id = 55555555-5555-5555-5555-555555555555 IF status = 'REQUESTED';
SERIAL CONSISTENCY LOCAL_SERIAL;
UPDATE rides SET status = 'ONGOING' WHERE ride_id = 55555555-5555-5555-5555-555555555555 IF status = 'ACCEPTED' AND driver_id = 'DRV01';
-- conditional batch spanning two partitions (expected error)
BEGIN BATCH
  UPDATE rides SET status = 'COMPLETED' WHERE ride_id = 55555555-5555-5555-5555-555555555555 IF status = 'ONGOING';
  UPDATE rides SET status = 'COMPLETED' WHERE ride_id = 11111111-1111-1111-1111-111111111111 IF status = 'ONGOING';
APPLY BATCH;

-- [7] static, set<text>, UDT, TTL, WRITETIME
CREATE TABLE bad_static (k int PRIMARY KEY, s int static);
CREATE TABLE IF NOT EXISTS rides_by_driver (driver_id text, ride_id uuid, driver_name text static, vehicle_plate text static, fare bigint, PRIMARY KEY ((driver_id), ride_id));
INSERT INTO rides_by_driver (driver_id, ride_id, driver_name, vehicle_plate, fare) VALUES ('DRV01', 11111111-1111-1111-1111-111111111111, 'Nguyen Van A', '51A-12345', 52000);
INSERT INTO rides_by_driver (driver_id, ride_id, fare) VALUES ('DRV01', 33333333-3333-3333-3333-333333333333, 0);
UPDATE rides_by_driver SET vehicle_plate = '51A-99999' WHERE driver_id = 'DRV01';
SELECT driver_id, ride_id, driver_name, vehicle_plate, fare FROM rides_by_driver WHERE driver_id = 'DRV01';
CREATE TYPE IF NOT EXISTS address (street text, ward text, city text, lat double, lon double);
CREATE TABLE IF NOT EXISTS customers (customer_id text PRIMARY KEY, full_name text, phones set<text>, home frozen<address>, saved_places map<text, frozen<address>>);
INSERT INTO customers (customer_id, full_name, phones, home) VALUES ('CUST001', 'Tran B', {'0901000001'}, {street: '140 Le Trong Tan', ward: 'Tay Thanh', city: 'HCM', lat: 10.806, lon: 106.628}) USING TTL 3600;
UPDATE customers SET phones = phones + {'0901000002'} WHERE customer_id = 'CUST001';
SELECT customer_id, phones, home.city, TTL(full_name), WRITETIME(full_name) FROM customers WHERE customer_id = 'CUST001';
-- WRITETIME/TTL on a non-frozen collection (5.0 feature, expected error in 4.1)
SELECT WRITETIME(phones) FROM customers WHERE customer_id = 'CUST001';

-- [8] counters
CREATE TABLE IF NOT EXISTS revenue_by_day (city text, yyyymm int, day int, total_vnd counter, rides counter, PRIMARY KEY ((city, yyyymm), day));
CREATE TABLE bad_counter (k int PRIMARY KEY, c counter, note text);
UPDATE revenue_by_day SET total_vnd = total_vnd + 52000, rides = rides + 1 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 1;
INSERT INTO revenue_by_day (city, yyyymm, day, total_vnd) VALUES ('HCM', 202609, 2, 1);
UPDATE revenue_by_day USING TTL 60 SET rides = rides + 1 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 1;
UPDATE revenue_by_day SET total_vnd = 100 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 1;
BEGIN BATCH
  UPDATE revenue_by_day SET rides = rides + 1 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 1;
  INSERT INTO rides (ride_id, status) VALUES (66666666-6666-6666-6666-666666666666, 'REQUESTED');
APPLY BATCH;
BEGIN COUNTER BATCH
  UPDATE revenue_by_day SET total_vnd = total_vnd + 87000, rides = rides + 1 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 2;
  UPDATE revenue_by_day SET total_vnd = total_vnd + 120000, rides = rides + 1 WHERE city = 'HN' AND yyyymm = 202609 AND day = 3;
APPLY BATCH;
UPDATE revenue_by_day SET total_vnd = total_vnd + 1 WHERE city = 'HCM' AND yyyymm = 202609 AND day = 1 IF EXISTS;
SELECT * FROM revenue_by_day;

-- [9] driver_locations: default TTL + TWCS
CREATE TABLE IF NOT EXISTS driver_locations (driver_id text, day date, ts timestamp, lat double, lon double, PRIMARY KEY ((driver_id, day), ts)) WITH CLUSTERING ORDER BY (ts DESC) AND default_time_to_live = 86400 AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_unit': 'HOURS', 'compaction_window_size': 1};
INSERT INTO driver_locations (driver_id, day, ts, lat, lon) VALUES ('DRV01', '2026-10-04', toTimestamp(now()), 10.80, 106.63);
SELECT driver_id, ts, TTL(lat) FROM driver_locations WHERE driver_id = 'DRV01' AND day = '2026-10-04' LIMIT 1;

-- [10] drivers_by_area: status/rating inside the primary key
CREATE TABLE IF NOT EXISTS drivers_by_area (area text, status text, rating float, driver_id text, full_name text, PRIMARY KEY ((area, status), rating, driver_id)) WITH CLUSTERING ORDER BY (rating DESC, driver_id ASC);
INSERT INTO drivers_by_area (area, status, rating, driver_id, full_name) VALUES ('HCM-TanPhu', 'AVAILABLE', 4.8, 'DRV01', 'Nguyen Van A');
UPDATE drivers_by_area SET status = 'BUSY' WHERE area = 'HCM-TanPhu' AND status = 'AVAILABLE' AND rating = 4.8 AND driver_id = 'DRV01';
UPDATE drivers_by_area SET rating = 4.9 WHERE area = 'HCM-TanPhu' AND status = 'AVAILABLE' AND driver_id = 'DRV01';
BEGIN BATCH
  DELETE FROM drivers_by_area WHERE area = 'HCM-TanPhu' AND status = 'AVAILABLE' AND rating = 4.8 AND driver_id = 'DRV01';
  INSERT INTO drivers_by_area (area, status, rating, driver_id, full_name) VALUES ('HCM-TanPhu', 'BUSY', 4.8, 'DRV01', 'Nguyen Van A');
APPLY BATCH;
SELECT * FROM drivers_by_area WHERE area = 'HCM-TanPhu' AND status = 'AVAILABLE';
SELECT * FROM drivers_by_area WHERE area = 'HCM-TanPhu' AND status = 'BUSY';

-- [11] roles under the default AllowAllAuthenticator/AllowAllAuthorizer
CREATE ROLE app_user WITH PASSWORD = 'secret' AND LOGIN = true;
CREATE ROLE app_reader;
GRANT SELECT ON KEYSPACE probe TO app_reader;
LIST ROLES;
