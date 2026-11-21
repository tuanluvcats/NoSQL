# Kết quả đo hiệu năng và so sánh baseline

Môi trường: Cassandra 3.11.4, một node, 127.0.0.1; keyspace `ride_booking_bench_test` (schema và dữ liệu mẫu giống `ride_booking`, 36 chuyến). Thời điểm đo: 2026-11-22 01:33.

## 1. Thời gian Cassandra xử lý (ms, lấy từ query trace phía server)

| Thao tác | Số lần | p50 | p95 | max |
|---|---:|---:|---:|---:|
| Đọc theo partition key, 36 chuyến | 200 | 1.78 | 2.78 | 13.12 |
| Thiếu partition key (`ALLOW FILTERING`), 36 chuyến | 20 | 3.65 | 5.26 | 5.74 |
| Ghi thường (`UPDATE`) | 200 | 0.8 | 1.91 | 2.77 |
| Ghi có điều kiện (LWT `IF status = ...`) | 200 | 9.81 | 12.55 | 128.22 |
| Đọc theo partition key, 20036 chuyến | 200 | 0.82 | 1.17 | 2.54 |
| Thiếu partition key (`ALLOW FILTERING`), 20036 chuyến | 20 | 99.8 | 106.4 | 122.8 |

## 2. Tranh nhận cùng một chuyến

Mỗi vòng: tạo một chuyến REQUESTED, 8 luồng (tài xế) cùng nhận. Đúng nghiệp vụ: mỗi vòng đúng 1 người thắng.

| Cách làm | Số vòng | Vòng có đúng 1 người thắng | Vòng có từ 2 người thắng trở lên | Số người thắng nhiều nhất trong một vòng |
|---|---:|---:|---:|---:|
| Baseline: đọc trạng thái rồi UPDATE thường | 30 | 0 | 30 | 8 |
| Ứng dụng: LWT `IF status = 'REQUESTED'` | 30 | 30 | 0 | 1 |

Ghi chú: một node nên không có độ trễ giữa các bản sao; trên cụm nhiều node, LWT (Paxos, 4 vòng mạng) còn chậm hơn ghi thường rõ hơn. Đọc theo partition key gần như không đổi khi bảng lớn lên, còn ALLOW FILTERING phải quét cả bảng nên chậm dần theo số dòng. Các chuyến giả (mã BENCH_F...) chỉ nằm trong keyspace đo, không đụng `ride_booking`.
