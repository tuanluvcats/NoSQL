"""Kiểm file backup (validate_backup), đường dẫn an toàn (resolve_backup), tên file có dấu thời gian +07."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from config import BASE_TABLES
from domain.tz import parse_vn
from services import backup
from tests.fakes import FakeDb

pytestmark = pytest.mark.backup

SCHEMA = {
    "customers": {"customer_id": "text", "full_name": "text", "created_at": "timestamp"},
    "rides": {"ride_id": "text", "fare": "double", "status_history": "map<timestamp, text>"},
    "promotions": {"promo_code": "text", "cities": "set<text>", "used_count": "int", "active": "boolean"},
}


def _full_schema():
    out = {t: {"id": "text"} for t in BASE_TABLES}
    out.update(copy.deepcopy(SCHEMA))
    return out


def _valid_data():
    schema = _full_schema()
    tables = {t: {"columns": dict(cols), "rows": []} for t, cols in schema.items()}
    tables["customers"]["rows"] = [{"customer_id": "C1", "full_name": "A", "created_at": "2026-10-01 00:00:00.000Z"}]
    tables["rides"]["rows"] = [{"ride_id": "R1", "fare": 81000.0,
                                "status_history": {"2026-10-01 00:00:00.000Z": "REQUESTED"}}]
    tables["promotions"]["rows"] = [{"promo_code": "P", "cities": ["HCM", "HN"], "used_count": 1, "active": True}]
    return {
        "format": backup.BACKUP_FORMAT, "keyspace": "ride_booking_test",
        "created_at": "2026-10-04T10:10:05+07:00", "release_version": "3.11.4",
        "tables": tables, "counts": {t: len(v["rows"]) for t, v in tables.items()},
    }


def test_valid_data_has_no_errors():
    assert backup.validate_backup(_valid_data(), _full_schema()) == []


def test_missing_rides_table_is_reported():
    data = _valid_data()
    del data["tables"]["rides"]
    del data["counts"]["rides"]
    errs = backup.validate_backup(data, _full_schema())
    assert errs and any("rides" in e for e in errs)


def test_extra_table_is_reported():
    data = _valid_data()
    data["tables"]["vehicles_by_plate"] = {"columns": {}, "rows": []}
    errs = backup.validate_backup(data, _full_schema())
    assert any("vehicles_by_plate" in e for e in errs)


def test_count_mismatch_is_reported():
    data = _valid_data()
    data["counts"]["customers"] = 5
    errs = backup.validate_backup(data, _full_schema())
    assert any("customers" in e for e in errs)


def test_unknown_column_is_reported():
    data = _valid_data()
    data["tables"]["customers"]["columns"]["foo"] = "text"
    errs = backup.validate_backup(data, _full_schema())
    assert any("customers" in e and "foo" in e for e in errs)


def test_column_type_change_is_reported():
    data = _valid_data()
    data["tables"]["customers"]["columns"]["full_name"] = "int"
    errs = backup.validate_backup(data, _full_schema())
    assert any("full_name" in e for e in errs)


def test_row_key_outside_file_columns_is_reported():
    data = _valid_data()
    data["tables"]["customers"]["rows"][0]["bar"] = "x"
    errs = backup.validate_backup(data, _full_schema())
    assert any("bar" in e for e in errs)


def test_wrong_format_and_non_dict_are_reported():
    data = _valid_data()
    data["format"] = "other"
    assert any("format" in e for e in backup.validate_backup(data, _full_schema()))
    assert backup.validate_backup([], _full_schema())
    assert backup.validate_backup({"format": backup.BACKUP_FORMAT}, _full_schema())


@pytest.mark.parametrize("table,col,bad", [
    ("rides", "fare", "abc"),               # chữ vào cột double
    ("customers", "full_name", 12),         # số vào cột text
    ("promotions", "active", "yes"),        # chuỗi vào cột boolean
    ("promotions", "cities", "HCM"),        # chuỗi vào cột set
    ("rides", "status_history", ["x"]),     # list vào cột map
    ("promotions", "used_count", 1.5),      # số thực vào cột int
])
def test_bad_cell_value_type_is_reported_before_any_truncate(table, col, bad):
    data = _valid_data()
    data["tables"][table]["rows"][0][col] = bad
    errs = backup.validate_backup(data, _full_schema())
    assert any(table in e and col in e for e in errs)


def test_null_cell_is_allowed():
    data = _valid_data()
    data["tables"]["rides"]["rows"][0]["fare"] = None
    assert backup.validate_backup(data, _full_schema()) == []


# ------------------------------------------------------------------ resolve_backup
def test_resolve_rejects_path_traversal(tmp_path):
    for bad in ("../x.json", "..\\x.json", "/etc/passwd", "a/../../x_20261004_101005.json",
                "x.json", "ride_booking_20261004_101005.json.exe", "", "ride_booking_20261004_101005.JSON"):
        with pytest.raises(ValueError):
            backup.resolve_backup(tmp_path, bad)


def test_resolve_accepts_regular_name_inside_dir(tmp_path):
    p = backup.resolve_backup(tmp_path, "ride_booking_20261004_101005_prerestore.json")
    assert p.parent == tmp_path.resolve()


def test_resolve_rejects_symlink_leaving_the_dir(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "ride_booking_20261004_101005.json").write_text("{}")
    inner = tmp_path / "inner"
    inner.mkdir()
    link = inner / "ride_booking_20261004_101005.json"
    try:
        link.symlink_to(outside / "ride_booking_20261004_101005.json")
    except (OSError, NotImplementedError):
        pytest.skip("không tạo được symlink trên máy này")
    with pytest.raises(ValueError):
        backup.resolve_backup(inner, link.name)


def test_backup_name_regex_matches_spec():
    assert backup.BACKUP_NAME_RE == r"^[a-z0-9_]+_\d{8}_\d{6}(_[a-z]+)?\.json$"


def test_list_backups_newest_first_ignores_foreign_files(tmp_path):
    for n in ("ride_booking_20261004_101005.json", "ride_booking_20261005_090000.json",
              "ride_booking_20261004_101005_prerestore.json", "notes.txt", "x.json"):
        (tmp_path / n).write_text("{}")
    assert backup.list_backups(tmp_path) == [
        "ride_booking_20261005_090000.json",
        "ride_booking_20261004_101005_prerestore.json",
        "ride_booking_20261004_101005.json",
    ]
    assert backup.list_backups(tmp_path / "missing") == []


# ------------------------------------------------------------------ create_backup (FakeDb)
def _fake_db_for_backup():
    cols = []
    for t in BASE_TABLES:
        cols.append({"table_name": t, "column_name": "id", "type": "text"})
    cols.append({"table_name": "vehicles_by_plate", "column_name": "license_plate", "type": "text"})  # MV bị bỏ
    exports = [[{"[json]": json.dumps({"id": f"{t}-1", "note": None})}] for t in BASE_TABLES]
    return FakeDb({"SYS_columns": [cols], "SYS_local": [{"release_version": "3.11.4"}], "BK_export": exports})


def test_backup_file_name_has_vn_timestamp(tmp_path):
    db = _fake_db_for_backup()
    p = backup.create_backup(db, tmp_path, parse_vn("2026-10-04 10:10:05"))
    assert p.name == "ride_booking_test_20261004_101005.json"
    assert p.parent == tmp_path


def test_backup_file_name_converts_utc_to_plus7(tmp_path):
    db = _fake_db_for_backup()
    utc = datetime(2026, 10, 4, 20, 30, 0, tzinfo=timezone.utc)  # 03:30 +07 ngày hôm sau
    p = backup.create_backup(db, tmp_path, utc, label="prerestore")
    assert p.name == "ride_booking_test_20261005_033000_prerestore.json"
    assert backup.BACKUP_NAME_RE and __import__("re").match(backup.BACKUP_NAME_RE, p.name)


def test_backup_content_shape_and_no_overwrite(tmp_path):
    db = _fake_db_for_backup()
    now = parse_vn("2026-10-04 10:10:05")
    p = backup.create_backup(db, tmp_path, now)
    data = backup.load_backup(p)
    assert data["format"] == backup.BACKUP_FORMAT
    assert set(data["tables"]) == set(BASE_TABLES) and "vehicles_by_plate" not in data["tables"]
    assert data["created_at"].endswith("+07:00")
    assert data["release_version"] == "3.11.4"
    assert data["counts"]["customers"] == 1
    assert data["tables"]["customers"]["rows"] == [{"id": "customers-1", "note": None}]
    assert data["tables"]["customers"]["columns"] == {"id": "text"}
    # cùng giây, cùng nhãn: không ghi đè file cũ
    p2 = backup.create_backup(_fake_db_for_backup(), tmp_path, now)
    assert p2 != p and p.exists() and p2.exists()
    assert Path(p2).name == "ride_booking_test_20261004_101006.json"


def test_create_backup_rejects_bad_label(tmp_path):
    with pytest.raises(ValueError):
        backup.create_backup(_fake_db_for_backup(), tmp_path, parse_vn("2026-10-04 10:10:05"), label="../x")
