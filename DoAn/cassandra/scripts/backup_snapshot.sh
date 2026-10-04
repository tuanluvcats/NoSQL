#!/usr/bin/env bash
# Sao lưu VẬT LÝ một keyspace bằng nodetool snapshot (chạy BÊN TRONG container nosql-cassandra).
#   docker exec nosql-cassandra bash /tmp/cassandra/scripts/backup_snapshot.sh [keyspace] [tên_bản_sao_lưu]
# Kết quả: /backup/<tên>/schema.cql + /backup/<tên>/<keyspace>/<bảng>/*.db và file nén /backup/<tên>.tar.gz
# Lấy về Windows:  docker cp nosql-cassandra:/backup/<tên>.tar.gz .
set -euo pipefail
KS="${1:-ride_booking}"
TAG="${2:-bk_$(date +%Y%m%d_%H%M%S)}"
OUT="/backup/$TAG"
DATA=/var/lib/cassandra/data
[ -e "$OUT" ] && { echo "Đã tồn tại $OUT — hãy chọn tên khác"; exit 1; }
mkdir -p "$OUT"

echo "[1/4] Sao lưu lược đồ (DESCRIBE KEYSPACE) -> $OUT/schema.cql"
cqlsh -e "DESCRIBE KEYSPACE $KS" > "$OUT/schema.cql"

echo "[2/4] Ghi memtable xuống đĩa và chụp snapshot '$TAG'"
nodetool flush "$KS"
nodetool snapshot -t "$TAG" "$KS"

echo "[3/4] Gom file SSTable của snapshot theo cấu trúc <keyspace>/<bảng>/"
n=0
for snap in "$DATA/$KS"/*/snapshots/"$TAG"; do
  [ -d "$snap" ] || continue
  dir=$(basename "$(dirname "$(dirname "$snap")")")   # <bảng>-<id>
  table="${dir%-*}"
  mkdir -p "$OUT/$KS/$table"
  find "$snap" -maxdepth 1 -type f -exec cp {} "$OUT/$KS/$table/" \;
  n=$((n + 1))
done
echo "      $n bảng"

echo "[4/4] Nén -> /backup/$TAG.tar.gz"
tar -czf "/backup/$TAG.tar.gz" -C /backup "$TAG"
du -sh "/backup/$TAG.tar.gz"
echo "Xong. Snapshot gốc vẫn nằm trong $DATA/$KS/*/snapshots/$TAG (xóa bằng: nodetool clearsnapshot -t $TAG -- $KS)"
