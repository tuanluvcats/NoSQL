# cqlsh 6.1 (Cassandra 4.1.12): COPY FROM hiểu ngược dấu độ lệch múi giờ; INSERT thường thì đúng
C="docker exec nosql-cassandra"
set -x
$C sh -c "printf 'customer_id,created_at\nTZ1,2026-10-04 08:00:00+0700\nTZ2,2026-10-04 08:00:00+0000\nTZ3,2026-10-04 08:00:00\nTZ4,2026-10-04 08:00:00-0500\n' > /tmp/tz.csv"
$C cqlsh -e "COPY ride_booking.customers (customer_id, created_at) FROM '/tmp/tz.csv' WITH HEADER = true;"
$C cqlsh -e "INSERT INTO ride_booking.customers (customer_id, created_at) VALUES ('TZ5', '2026-10-04 08:00:00+0700');"
$C cqlsh -e "SELECT customer_id, created_at FROM ride_booking.customers WHERE customer_id IN ('TZ1', 'TZ2', 'TZ3', 'TZ4', 'TZ5');"
$C cqlsh -e "COPY ride_booking.customers (customer_id, created_at) TO '/tmp/tz_out.csv' WITH HEADER = true;"
$C sh -c "grep TZ /tmp/tz_out.csv"
$C cqlsh -e "DELETE FROM ride_booking.customers WHERE customer_id IN ('TZ1', 'TZ2', 'TZ3', 'TZ4', 'TZ5');"
