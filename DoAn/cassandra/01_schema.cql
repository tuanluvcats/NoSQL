CREATE KEYSPACE IF NOT EXISTS ride_booking
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
  AND durable_writes = true;

USE ride_booking;

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

CREATE MATERIALIZED VIEW IF NOT EXISTS vehicles_by_plate AS
  SELECT license_plate, vehicle_id, driver_id, model, color
  FROM vehicles
  WHERE license_plate IS NOT NULL AND vehicle_id IS NOT NULL
  PRIMARY KEY (license_plate, vehicle_id);


CREATE TABLE IF NOT EXISTS user_accounts (
  username      text PRIMARY KEY,
  password_hash text,
  role          text,        
  ref_id        text,        -- customer_id hoặc driver_id tương ứng
  full_name     text,
  is_active     boolean,
  created_at    timestamp,
  last_login_at timestamp
);

CREATE TABLE IF NOT EXISTS rides (
  ride_id             text PRIMARY KEY,
  customer_id         text,
  customer_name       text,
  customer_phone      text,
  driver_id           text,
  driver_name         text,
  vehicle_plate       text,
  city                text,
  district            text,
  pickup_address      text,
  destination_address text,
  distance_km         double,
  fare                double,
  discount            double,
  promo_code          text,
  payment_method      text,  
  status              text,  
  ride_date           date,
  requested_at        timestamp,
  accepted_at         timestamp,
  started_at          timestamp,
  completed_at        timestamp,
  cancel_reason       text,
  status_history      map<timestamp, text>
);

CREATE TABLE IF NOT EXISTS rides_by_driver_month (
  driver_id           text,
  yyyymm              int,
  requested_at        timestamp,
  ride_id             text,
  customer_id         text,
  pickup_address      text,
  destination_address text,
  distance_km         double,
  fare                double,
  status              text,
  PRIMARY KEY ((driver_id, yyyymm), requested_at, ride_id)
) WITH CLUSTERING ORDER BY (requested_at DESC, ride_id ASC);

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
) WITH CLUSTERING ORDER BY (requested_at DESC, ride_id ASC);

CREATE TABLE IF NOT EXISTS drivers_by_area (
  city          text,
  district      text,
  driver_id     text,
  full_name     text,
  phone         text,
  rating        double,
  vehicle_plate text,
  lat           double,
  lng           double,
  last_seen     timestamp,
  PRIMARY KEY ((city, district), driver_id)
);

CREATE TABLE IF NOT EXISTS driver_locations (
  driver_id text,
  day       date,
  ts        timestamp,
  lat       double,
  lng       double,
  speed_kmh double,
  PRIMARY KEY ((driver_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS ratings_by_driver (
  driver_id   text,
  rated_at    timestamp,
  ride_id     text,
  customer_id text,
  stars       double,
  comment     text,
  tags        list<text>,
  PRIMARY KEY ((driver_id), rated_at, ride_id)
) WITH CLUSTERING ORDER BY (rated_at DESC, ride_id ASC);

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
) WITH CLUSTERING ORDER BY (payment_method ASC, paid_at DESC, ride_id ASC);

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
);

SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'ride_booking';

SELECT column_name, kind, position, type FROM system_schema.columns
WHERE keyspace_name = 'ride_booking' AND table_name = 'rides_by_driver_month';
