"""Backup/restore JSON logical trên Cassandra thật (_test): đếm dòng VÀ so nội dung, kiểm file hỏng trước TRUNCATE,
lỗi INSERT giữa chừng, chế độ bảo trì chặn ghi, đường dẫn an toàn, phân quyền HTTP."""
import dataclasses
import json
import re
import time

import pytest

from config import BASE_TABLES
from domain.tz import parse_vn
from services import backup
from services.maintenance import MaintenanceState
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.backup

NOW = parse_vn("2026-10-04 10:10:05")
SEED_COUNTS = {"customers": 10, "drivers": 10, "vehicles": 10, "user_accounts": 22, "rides": 36,
               "rides_by_customer": 36, "rides_by_area_date": 36, "rides_by_driver_month": 34,
               "payments_by_city_date": 27, "ratings_by_driver": 23, "drivers_by_area": 6,
               "driver_locations": 18, "promotions": 3, "vehicles_by_plate": 10}


def _wait_mv(db, expected=10, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if backup.table_counts(db)["vehicles_by_plate"] == expected:
            return
        time.sleep(0.1)


def _dump(session):
    """Nội dung đầy đủ của 13 bảng thật (không chỉ số dòng), sắp xếp để so sánh ổn định."""
    out = {}
    for t in BASE_TABLES:
        out[t] = sorted(repr(sorted(r.items())) for r in session.execute(f"SELECT * FROM {t}", timeout=60))
    return out


def _fail_insert_on(session, monkeypatch, table):
    """Ép mọi INSERT ... JSON vào `table` lỗi (các lệnh khác đi qua bộ theo dõi bảng bẩn như bình thường)."""
    orig = session.execute_async

    def wrapper(query, *a, **kw):
        qs = getattr(query, "query_string", None) or (query if isinstance(query, str) else "")
        if re.match(rf"^\s*INSERT\s+INTO\s+{table}\s+JSON", qs, re.I):
            raise RuntimeError(f"lỗi giả lập khi INSERT vào {table}")
        return orig(query, *a, **kw)

    monkeypatch.setattr(session, "execute_async", wrapper)


def test_table_counts_of_seed(db):
    _wait_mv(db)
    assert backup.table_counts(db) == SEED_COUNTS


def test_backup_delete_restore_counts_and_content_equal(db, raw, tmp_path):
    _wait_mv(db)
    before = backup.table_counts(db)
    assert before == SEED_COUNTS
    content_before = _dump(raw)
    history_before = db.one("B06_ride_get", ["RIDE_1007"])["status_history"]
    path = backup.create_backup(db, tmp_path, NOW)
    assert path.name == "ride_booking_test_20261004_101005.json"

    # phá dữ liệu
    raw.execute("DELETE FROM customers WHERE customer_id='CUST001'")
    raw.execute("TRUNCATE payments_by_city_date", timeout=60)
    raw.execute("INSERT INTO promotions (promo_code, discount_percent) VALUES ('EXTRA', 5)")
    raw.execute("UPDATE rides SET status='CANCELLED' WHERE ride_id='RIDE_1007'")
    assert backup.table_counts(db) != before

    state = MaintenanceState()
    res = backup.restore_backup(db, tmp_path, path.name, state, parse_vn("2026-10-04 10:20:00"))
    assert res.ok and res.code == "ok", res.message
    assert state.active is False
    _wait_mv(db)
    assert backup.table_counts(db) == before
    assert res.data["counts_before"] != before and res.data["counts_after"] == before
    assert _dump(raw) == content_before  # nội dung từng bảng khớp, không chỉ số dòng
    assert db.one("B16_promo_get", ["EXTRA"]) is None
    assert db.one("B06_ride_get", ["RIDE_1007"])["status_history"] == history_before
    assert set(db.one("B16_promo_get", ["GIAM20"])["cities"]) == {"HCM", "HN"}
    assert db.rows("B05_vehicle_by_plate", ["51K-567.89"])[0]["vehicle_id"] == "VEH_555"
    assert res.data["safety_backup"].endswith("_prerestore.json")
    assert (tmp_path / res.data["safety_backup"]).exists()
    assert len(list(tmp_path.glob("*_prerestore.json"))) == 1


def test_restore_rejects_invalid_file_before_truncate(db, raw, tmp_path):
    """Chống mất dữ liệu: file hỏng/khác schema phải bị từ chối TRƯỚC mọi TRUNCATE."""
    _wait_mv(db)
    before = backup.table_counts(db)
    content_before = _dump(raw)
    path = backup.create_backup(db, tmp_path, NOW)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["tables"]["rides"]
    del data["counts"]["rides"]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    state = MaintenanceState()
    res = backup.restore_backup(db, tmp_path, path.name, state, NOW)
    assert res.ok is False and res.code == "backup_invalid"
    assert any("rides" in e for e in res.data["errors"])
    assert state.active is False
    assert backup.table_counts(db) == before and before["rides"] == 36
    assert _dump(raw) == content_before
    assert list(tmp_path.glob("*_prerestore.json")) == []  # chưa kịp (và không cần) tạo bản an toàn


@pytest.mark.parametrize("mutate", [
    lambda d: d["tables"]["rides"]["rows"][0].__setitem__("fare", "không phải số"),   # kiểu giá trị sai
    lambda d: d["tables"]["customers"]["columns"].__setitem__("foo", "text"),         # cột lạ
    lambda d: d.__setitem__("format", "other"),                                      # sai phiên bản
    lambda d: d["counts"].__setitem__("drivers", 99),                                # số dòng lệch
])
def test_restore_rejects_other_invalid_variants_without_touching_data(db, raw, tmp_path, mutate):
    before = backup.table_counts(db)
    path = backup.create_backup(db, tmp_path, NOW)
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    state = MaintenanceState()
    res = backup.restore_backup(db, tmp_path, path.name, state, NOW)
    assert res.code == "backup_invalid" and not state.active
    assert backup.table_counts(db) == before


def test_restore_rejects_garbage_file_and_traversal_name(db, raw, tmp_path):
    before = backup.table_counts(db)
    (tmp_path / "ride_booking_test_20261004_101005.json").write_text("{không phải json", encoding="utf-8")
    state = MaintenanceState()
    res = backup.restore_backup(db, tmp_path, "ride_booking_test_20261004_101005.json", state, NOW)
    assert res.code == "backup_invalid" and not state.active
    res = backup.restore_backup(db, tmp_path, "../ride_booking_test_20261004_101005.json", state, NOW)
    assert res.code == "backup_invalid" and not state.active
    res = backup.restore_backup(db, tmp_path, "ride_booking_test_20250101_000000.json", state, NOW)
    assert res.ok is False and res.code == "not_found" and not state.active
    assert backup.table_counts(db) == before


def test_restore_refused_while_maintenance(db, raw, tmp_path):
    path = backup.create_backup(db, tmp_path, NOW)
    before = backup.table_counts(db)
    state = MaintenanceState()
    assert state.begin() is True
    res = backup.restore_backup(db, tmp_path, path.name, state, NOW)
    assert res.ok is False and res.code == "maintenance"
    assert state.active is True  # restore bị từ chối không được tắt cờ của người khác
    assert backup.table_counts(db) == before


def test_restore_failure_midway_reports_clearly_ends_maintenance_and_can_be_recovered(db, raw, tmp_path, monkeypatch):
    _wait_mv(db)
    before = backup.table_counts(db)
    content_before = _dump(raw)
    path = backup.create_backup(db, tmp_path, NOW)
    state = MaintenanceState()
    with monkeypatch.context() as m:
        _fail_insert_on(raw, m, "rides_by_area_date")
        res = backup.restore_backup(db, tmp_path, path.name, state, parse_vn("2026-10-04 10:20:00"))
    assert res.ok is False
    assert res.code == "partial"
    assert "rides_by_area_date" in res.message and "lỗi giả lập" in res.message
    assert res.data["failed_table"] == "rides_by_area_date"
    assert state.active is False  # luôn tắt chế độ bảo trì khi lỗi
    safety = res.data["safety_backup"]
    assert safety in res.message and (tmp_path / safety).exists()
    assert backup.table_counts(db)["rides_by_area_date"] == 0  # đã TRUNCATE rồi mới lỗi: đúng như thông báo

    # bản an toàn tạo ngay trước TRUNCATE nên khôi phục lại được trạng thái ban đầu
    res2 = backup.restore_backup(db, tmp_path, safety, state, parse_vn("2026-10-04 10:30:00"))
    assert res2.ok, res2.message
    _wait_mv(db)
    assert backup.table_counts(db) == before
    assert _dump(raw) == content_before


def test_restore_with_trace_does_not_flood_panel_with_row_inserts(db, raw, tmp_path):
    """Mỗi bảng chỉ để lại một dòng trace INSERT (không phải mỗi dòng dữ liệu một dòng)."""
    from db import trace

    path = backup.create_backup(db, tmp_path, NOW)
    trace.start_request()
    state = MaintenanceState()
    assert backup.restore_backup(db, tmp_path, path.name, state, NOW).ok
    entries = trace.current()
    inserts = [e for e in entries if e.kind == "write" and e.cql.startswith("INSERT INTO")]
    assert len(inserts) <= len(BASE_TABLES)
    assert len(entries) < 150


# ------------------------------------------------------------------ HTTP
def _app_client(settings_test, db, tmp_path):
    from fastapi.testclient import TestClient

    from main import create_app

    app = create_app(dataclasses.replace(settings_test, backup_dir=tmp_path), db=db, clock=lambda: NOW)
    return app, TestClient(app, follow_redirects=False)


def test_http_admin_create_and_restore_roundtrip(db, raw, settings_test, tmp_path):
    _wait_mv(db)
    app, c = _app_client(settings_test, db, tmp_path)
    assert http_login(c, "admin").status_code == 303  # ghi last_login_at, nên chụp nội dung SAU khi đăng nhập
    content_before = _dump(raw)
    r = c.post("/admin/backup/create", data={"label": ""})
    assert r.status_code == 303
    files = backup.list_backups(tmp_path)
    assert len(files) == 1 and re.match(backup.BACKUP_NAME_RE, files[0])
    page = c.get("/admin/backup")
    assert page.status_code == 200 and files[0] in page.text and "Đang khôi phục" not in page.text
    assert "snapshot" not in page.text.lower()  # không có nút nodetool snapshot

    raw.execute("TRUNCATE rides_by_customer", timeout=60)
    raw.execute("DELETE FROM customers WHERE customer_id='CUST002'")
    r = c.post("/admin/backup/restore", data={"name": files[0]})
    assert r.status_code == 303
    assert app.state.maintenance.active is False
    _wait_mv(db)
    assert _dump(raw) == content_before
    # sau restore, session cũ vẫn dùng được vì user_accounts được nạp lại đúng như lúc backup
    assert c.get("/admin/backup").status_code == 200


def test_http_restore_with_traversal_name_is_rejected_and_touches_nothing(db, raw, settings_test, tmp_path):
    app, c = _app_client(settings_test, db, tmp_path)
    assert http_login(c, "admin").status_code == 303
    before = backup.table_counts(db)
    r = c.post("/admin/backup/restore", data={"name": "../../x.json"})
    assert r.status_code == 303
    assert backup.table_counts(db) == before
    assert app.state.maintenance.active is False


def test_http_non_admin_cannot_backup_or_restore(db, raw, settings_test, tmp_path):
    app, c = _app_client(settings_test, db, tmp_path)
    assert http_login(c, "cust001").status_code == 303
    assert c.get("/admin/backup").status_code == 403
    assert c.post("/admin/backup/create", data={}).status_code == 403
    assert c.post("/admin/backup/restore", data={"name": "x"}).status_code == 403
    assert backup.list_backups(tmp_path) == []
    anon = _app_client(settings_test, db, tmp_path)[1]
    assert anon.get("/admin/backup").status_code == 303


def test_http_operator_is_allowed(db, raw, settings_test, tmp_path):
    app, c = _app_client(settings_test, db, tmp_path)
    assert http_login(c, "dieuphoi").status_code == 303
    assert c.get("/admin/backup").status_code == 200


def test_writes_are_rejected_while_maintenance_and_nothing_is_written(db, raw, settings_test, tmp_path):
    app, c = _app_client(settings_test, db, tmp_path)
    before = backup.table_counts(db)
    assert app.state.maintenance.begin() is True
    try:
        r = c.post("/register", data={"username": "newuser1", "password": "matkhau1", "full_name": "Nguyễn Văn A",
                                      "phone": "0912345678", "email": "a@b.vn", "address": "1 Lê Lợi"})
        assert r.status_code == 503 and "Đang khôi phục dữ liệu" in r.text
        assert c.post("/admin/backup/create", data={}).status_code == 503
    finally:
        app.state.maintenance.end()
    assert backup.table_counts(db) == before
    assert db.one("B01_account_get", ["newuser1"]) is None
