#!/usr/bin/env bash
# Khôi phục từ bản sao lưu do backup_snapshot.sh tạo (chạy BÊN TRONG container nosql-cassandra).
#   docker exec nosql-cassandra bash /tmp/cassandra/scripts/restore_snapshot.sh <tên_bản_sao_lưu> [keyspace] [--truncate]
# Đưa file từ Windows vào container trước (nếu cần):  docker cp .\<tên>.tar.gz nosql-cassandra:/backup/
# --truncate: xóa dữ liệu hiện tại của từng bảng trước khi nạp. BẮT BUỘC khi dữ liệu đã bị DELETE/UPDATE sai,
#             vì tombstone / bản ghi mới hơn sẽ "che" dữ liệu cũ được nạp lại (Cassandra giữ bản ghi có timestamp mới nhất).
set -euo pipefail
TAG="${1:?Cần tên bản sao lưu, ví dụ bk_20261004}"
KS="${2:-ride_booking}"
TRUNC="${3:-}"
DIR="/backup/$TAG"
if [ ! -d "$DIR" ] && [ -f "/backup/$TAG.tar.gz" ]; then
  tar -xzf "/backup/$TAG.tar.gz" -C /backup
fi
[ -d "$DIR/$KS" ] || { echo "Không thấy $DIR/$KS"; exit 1; }

echo "[1/3] Tạo lại keyspace / type / bảng / index nếu chưa có (thêm IF NOT EXISTS vào schema.cql)"
sed -E 's/^CREATE (KEYSPACE|TABLE|TYPE|INDEX|CUSTOM INDEX) /CREATE \1 IF NOT EXISTS /' "$DIR/schema.cql" > /tmp/restore_schema.cql
cqlsh -f /tmp/restore_schema.cql

echo "[2/3] Nạp SSTable từng bảng bằng nodetool import (-cd: sao chép, giữ nguyên bản sao lưu)"
for tdir in "$DIR/$KS"/*/; do
  table=$(basename "$tdir")
  if [ "$TRUNC" = "--truncate" ]; then
    cqlsh -e "TRUNCATE $KS.$table;"
  fi
  chown -R cassandra:cassandra "$tdir" 2>/dev/null || true
  nodetool import -cd -- "$KS" "$table" "$tdir"
  echo "      $table"
done

echo "[3/3] Kiểm tra số dòng sau khi khôi phục"
for tdir in "$DIR/$KS"/*/; do
  table=$(basename "$tdir")
  printf '      %-24s %s\n' "$table" "$(cqlsh -e "SELECT COUNT(*) FROM $KS.$table;" | sed -n 4p | tr -d ' ')"
done
