-- =====================================================================
-- 06_app_migration.cql - thay đổi schema DUY NHẤT của ứng dụng đặt xe
-- Lý do: thêm cột rides.rated_at (timestamp) để chặn đánh giá trùng bằng LWT:
--        UPDATE rides SET rated_at = ... WHERE ride_id = ? IF rated_at = null
-- Quy tắc: chỉ dùng ALTER TABLE ... ADD (không DROP, không đổi kiểu, không xóa cột).
-- Cách chạy (khuyến nghị, chạy lại nhiều lần được):
--     python -m tools.migrate --keyspace ride_booking      (cwd = DoAn/app)
-- Hoặc dùng cqlsh:  cqlsh -f 06_app_migration.cql
-- Cảnh báo: chạy lại bằng cqlsh sẽ báo lỗi "conflicts with an existing column"
--           vì cột đã tồn tại; hãy dùng python -m tools.migrate để an toàn khi chạy lại.
-- =====================================================================
USE ride_booking;
ALTER TABLE rides ADD rated_at timestamp;
