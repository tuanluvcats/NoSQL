#!/usr/bin/env bash
# Nhập (import) lại các file CSV do export_csv.sh tạo bằng cqlsh COPY FROM (chạy BÊN TRONG container).
#   docker exec nosql-cassandra bash /tmp/cassandra/scripts/import_csv.sh [keyspace] [thư_mục]
# Tạo lại lược đồ trước nếu keyspace chưa có (schema.cql nằm cùng thư mục CSV).
# Lưu ý: bảng counter được CỘNG DỒN khi nhập lại — hãy TRUNCATE bảng counter trước nếu không muốn cộng trùng.
set -euo pipefail
KS="${1:-ride_booking}"
DIR="${2:-/backup/csv_$KS}"
sed -E 's/^CREATE (KEYSPACE|TABLE|TYPE|INDEX|CUSTOM INDEX) /CREATE \1 IF NOT EXISTS /' "$DIR/schema.cql" > /tmp/import_schema.cql
cqlsh -f /tmp/import_schema.cql
for f in "$DIR"/*.csv; do
  table=$(basename "$f" .csv)
  cqlsh -e "COPY $KS.$table FROM '$f' WITH HEADER = true;" | tail -1
done
