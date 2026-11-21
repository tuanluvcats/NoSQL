"""Xuất CSV: đúng cột, UTF-8 có BOM cho Excel, không lộ khóa nhạy cảm, chống công thức Excel."""
from datetime import date, datetime, timezone

import pytest

from services.reports import HISTORY_COLUMNS, PAYMENT_COLUMNS, history_csv, payments_csv

pytestmark = pytest.mark.business

RIDE_1021 = {"ride_date": date(2026, 10, 4), "ride_id": "RIDE_1021", "pickup_address": "12 Nguyễn Huệ, Q1",
             "destination_address": "Sân bay Tân Sơn Nhất", "driver_id": "DRV_551", "fare": 81000.0,
             "status": "COMPLETED"}


def _lines(text: str) -> list[str]:
    return text.splitlines()


def test_history_csv_has_bom_header_and_one_line_per_row():
    text = history_csv([RIDE_1021])
    assert text.startswith("﻿ride_date,ride_id,")
    lines = _lines(text)
    assert len(lines) == 2
    assert lines[0] == "﻿" + ",".join(HISTORY_COLUMNS)
    assert HISTORY_COLUMNS == ("ride_date", "ride_id", "pickup_address", "destination_address", "driver_id", "fare",
                               "status")
    assert lines[1] == "2026-10-04,RIDE_1021,\"12 Nguyễn Huệ, Q1\",Sân bay Tân Sơn Nhất,DRV_551,81000,COMPLETED"


def test_history_csv_empty_still_has_header():
    assert _lines(history_csv([])) == ["﻿" + ",".join(HISTORY_COLUMNS)]


def test_history_csv_ignores_columns_outside_the_header_so_secrets_never_leak():
    row = dict(RIDE_1021, password_hash="pbkdf2_sha256$100000$x$y", customer_phone="0901234567")
    text = history_csv([row])
    assert "password_hash" not in text and "pbkdf2" not in text and "0901234567" not in text


def test_history_csv_handles_missing_driver_and_vietnamese_roundtrip():
    row = dict(RIDE_1021, driver_id=None, status="REQUESTED")
    line = _lines(history_csv([row]))[1]
    assert ",,81000,REQUESTED" in line
    encoded = history_csv([row]).encode("utf-8")
    assert encoded[:3] == b"\xef\xbb\xbf"  # BOM UTF-8 để Excel nhận đúng tiếng Việt
    assert "Sân bay Tân Sơn Nhất" in encoded.decode("utf-8-sig")


def test_history_csv_neutralises_spreadsheet_formulas():
    row = dict(RIDE_1021, pickup_address="=HYPERLINK(\"http://x\")", destination_address="@cmd")
    line = _lines(history_csv([row]))[1]
    assert "'=HYPERLINK" in line and "'@cmd" in line
    assert ",=HYPERLINK" not in line


def test_payments_csv_columns_and_vn_time():
    row = {"payment_method": "MOMO", "paid_at": datetime(2026, 10, 3, 3, 15, tzinfo=timezone.utc),
           "ride_id": "RIDE_1013", "customer_id": "CUST001", "driver_id": "DRV_551", "district": "Q1",
           "amount": 26000.0, "discount": 0.0, "password_hash": "x"}
    text = payments_csv([row])
    lines = _lines(text)
    assert text.startswith("﻿payment_method,paid_at,")
    assert lines[0] == "﻿" + ",".join(PAYMENT_COLUMNS)
    assert lines[1] == "MOMO,2026-10-03 10:15:00,RIDE_1013,CUST001,DRV_551,Q1,26000,0"  # 03:15 UTC = 10:15 +07
    assert "password_hash" not in text
