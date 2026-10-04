-- CHI CHAY tren container thu nghiem rieng (c41-auth) da mount cassandra.yaml bat PasswordAuthenticator + MV.
-- KHONG chay tren nosql-cassandra that: script tao keyspace ride_booking, bang rides va materialized view.
-- Chay: cqlsh -u cassandra -p cassandra -f t3_auth.cql
CREATE KEYSPACE ride_booking WITH replication = {'class':'NetworkTopologyStrategy','HCM':1};
CREATE TABLE ride_booking.rides (ride_id uuid PRIMARY KEY, customer_id text, status text, fare bigint);
CREATE MATERIALIZED VIEW ride_booking.rides_by_status AS SELECT * FROM ride_booking.rides WHERE status IS NOT NULL AND ride_id IS NOT NULL PRIMARY KEY (status, ride_id);
CREATE ROLE app_admin WITH PASSWORD = 'Admin@123' AND LOGIN = true;
CREATE ROLE app_reader WITH PASSWORD = 'Reader@123' AND LOGIN = true;
GRANT ALL PERMISSIONS ON KEYSPACE ride_booking TO app_admin;
GRANT SELECT ON KEYSPACE ride_booking TO app_reader;
LIST ROLES;
LIST ALL PERMISSIONS OF app_reader;
