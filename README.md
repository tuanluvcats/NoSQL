# Đồ án NoSQL: DbSchema và Apache Cassandra

Đề tài: thiết kế và triển khai CSDL Cassandra cho hệ thống đặt xe công nghệ, mô hình hóa bằng DbSchema, kèm ứng dụng web minh họa.

## Cấu trúc

- `DoAn/CASSANDRA.MD`: tài liệu thiết kế CSDL (mô hình hướng truy vấn, lược đồ, truy vấn, sao lưu, kiểm chứng).
- `DoAn/cassandra/`: script CQL (lược đồ, dữ liệu, truy vấn cơ bản và nâng cao, giao dịch nhẹ LWT, reset), script backup/restore và công cụ sinh dữ liệu.
- `DoAn/app/`: ứng dụng web đặt xe (FastAPI, Jinja2, cassandra-driver) cùng bộ kiểm thử. Cách chạy xem `DoAn/app/README.md`.
- `docker-compose.yml`: dựng Cassandra 3.11 của đồ án (service `cassandra-doan`) khi máy không cài Cassandra trực tiếp.
- `HANDOFF.md`: trạng thái công việc và các việc còn mở của ứng dụng.

## Chạy nhanh

```powershell
docker compose up -d cassandra-doan
cd DoAn\app
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m tools.setup_db --keyspace ride_booking_demo --seed --yes
$env:CASSANDRA_KEYSPACE = "ride_booking_demo"
.venv\Scripts\python -m uvicorn main:app --port 8000
```

Dùng keyspace riêng `ride_booking_demo` để không ghi đè dữ liệu của keyspace `ride_booking` dùng trong báo cáo.
Chi tiết từng bước và tài khoản thử: `DoAn/app/README.md`.
