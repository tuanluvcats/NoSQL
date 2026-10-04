#!/usr/bin/env bash
# Xuất (export) toàn bộ bảng của một keyspace ra CSV bằng cqlsh COPY TO (chạy BÊN TRONG container).
#   docker exec nosql-cassandra bash /tmp/cassandra/scripts/export_csv.sh [keyspace] [thư_mục]
# Lấy về Windows:  docker cp nosql-cassandra:/backup/csv_ride_booking .
# Lưu ý: COPY không giữ TTL và WRITETIME của dữ liệu.
set -euo pipefail
KS="${1:-ride_booking}"
OUT="${2:-/backup/csv_$KS}"
mkdir -p "$OUT"
cqlsh -e "DESCRIBE KEYSPACE $KS" > "$OUT/schema.cql"
for table in $(cqlsh -e "SELECT table_name FROM system_schema.tables WHERE keyspace_name = '$KS';" | sed -n '4,$p' | sed '/^$/,$d' | tr -d ' '); do
  cqlsh -e "COPY $KS.$table TO '$OUT/$table.csv' WITH HEADER = true;" > /dev/null
  printf '%-24s %6s dòng\n' "$table" "$(($(wc -l < "$OUT/$table.csv") - 1))"
done
echo "Đã xuất vào $OUT"
