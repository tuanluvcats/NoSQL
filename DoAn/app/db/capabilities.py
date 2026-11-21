"""Hành vi Cassandra đã quan sát bằng tests/integration/test_cassandra_probe.py.

Chạy lại test đó trên máy khác (ví dụ Docker 3.11.19) để kiểm các giá trị này.
"""
# TRUNCATE bảng gốc có xóa luôn dữ liệu trong materialized view hay không
TRUNCATE_CLEARS_MV: bool = True
# UPDATE ... IF status IN ('A','B') chạy được (ứng dụng vẫn dùng IF status = ... theo quyết định D3)
LWT_IF_IN_SUPPORTED: bool = True
# LWT (IF EXISTS) trên bảng gốc có MV chạy được và MV được cập nhật đúng
LWT_ON_MV_BASE_OK: bool = True
# SELECT JSON rồi INSERT ... JSON khôi phục lại đúng mọi cột (timestamp, date, map, set, list, null)
JSON_ROUNDTRIP_OK: bool = True

PROBED_ON: str = "3.11.4 cài trực tiếp Windows, 2026-11-21"
