C="docker exec nosql-cassandra"
set -x
$C cqlsh -e "CREATE TABLE IF NOT EXISTS probe.promo_codes (code text PRIMARY KEY, pct int); INSERT INTO probe.promo_codes (code, pct) VALUES ('GIAM20', 20) USING TTL 86400; SELECT code, pct, TTL(pct) FROM probe.promo_codes;"
$C cqlsh -e "COPY probe.promo_codes TO '/tmp/promo.csv' WITH HEADER=true;"
$C cat /tmp/promo.csv
$C cqlsh -e "TRUNCATE probe.promo_codes; COPY probe.promo_codes FROM '/tmp/promo.csv' WITH HEADER=true; SELECT code, pct, TTL(pct) FROM probe.promo_codes;"
