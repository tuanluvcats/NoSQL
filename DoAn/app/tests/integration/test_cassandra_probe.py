"""Thăm dò hành vi của Cassandra đang chạy (Task 1). Giá trị kỳ vọng nằm ở db/capabilities.py.

Chỉ chạy trên keyspace *_test; các bảng probe_* được DROP khi kết thúc.
"""
import json
import time
from datetime import date, datetime

import pytest
from cassandra import InvalidRequest

from db import capabilities as cap

pytestmark = pytest.mark.nosql


def _wait_count(session, table: str, expected: int, timeout: float = 5.0) -> int:
    end = time.time() + timeout
    n = -1
    while time.time() < end:
        n = len(list(session.execute(f"SELECT * FROM {table}")))
        if n == expected:
            return n
        time.sleep(0.2)
    return n


@pytest.fixture(scope="module")
def probe(cassandra_session, test_keyspace):
    s = cassandra_session
    s.set_keyspace(test_keyspace)
    for stmt in ("DROP MATERIALIZED VIEW IF EXISTS probe_v_by_plate",
                 "DROP TABLE IF EXISTS probe_v", "DROP TABLE IF EXISTS probe_r", "DROP TABLE IF EXISTS probe_j"):
        s.execute(stmt)
    s.execute("CREATE TABLE probe_v (vehicle_id text PRIMARY KEY, license_plate text)")
    s.execute(
        "CREATE MATERIALIZED VIEW probe_v_by_plate AS SELECT license_plate, vehicle_id FROM probe_v "
        "WHERE license_plate IS NOT NULL AND vehicle_id IS NOT NULL PRIMARY KEY (license_plate, vehicle_id)"
    )
    s.execute("CREATE TABLE probe_r (id text PRIMARY KEY, status text, rated text)")
    s.execute(
        "CREATE TABLE probe_j (id text PRIMARY KEY, ts timestamp, d date, m map<timestamp,text>, "
        "s set<text>, l list<text>, x double, b boolean, n text)"
    )
    yield s
    for stmt in ("DROP MATERIALIZED VIEW IF EXISTS probe_v_by_plate",
                 "DROP TABLE IF EXISTS probe_v", "DROP TABLE IF EXISTS probe_r", "DROP TABLE IF EXISTS probe_j"):
        s.execute(stmt)


def test_truncate_base_table_and_mv(probe):
    probe.execute("INSERT INTO probe_v (vehicle_id, license_plate) VALUES ('A','P1')")
    assert _wait_count(probe, "probe_v_by_plate", 1) == 1
    probe.execute("TRUNCATE probe_v")
    time.sleep(1)
    assert len(list(probe.execute("SELECT * FROM probe_v"))) == 0
    assert len(list(probe.execute("SELECT * FROM probe_v_by_plate"))) == (0 if cap.TRUNCATE_CLEARS_MV else 1)


def test_lwt_if_in(probe):
    probe.execute("INSERT INTO probe_r (id, status) VALUES ('R1','REQUESTED')")
    try:
        row = probe.execute(
            "UPDATE probe_r SET status='CANCELLED' WHERE id='R1' IF status IN ('REQUESTED','ACCEPTED')"
        ).one()
        applied = bool(row["[applied]"])
    except InvalidRequest:
        applied = False
    assert applied == cap.LWT_IF_IN_SUPPORTED


def test_lwt_on_base_table_with_mv(probe):
    probe.execute("INSERT INTO probe_v (vehicle_id, license_plate) VALUES ('B','P1')")
    try:
        row = probe.execute("UPDATE probe_v SET license_plate='P2' WHERE vehicle_id='B' IF EXISTS").one()
        applied = bool(row["[applied]"])
    except InvalidRequest:
        applied = False
    assert applied == cap.LWT_ON_MV_BASE_OK
    if applied:
        end = time.time() + 5
        while time.time() < end:
            plates = {r["license_plate"] for r in probe.execute("SELECT license_plate, vehicle_id FROM probe_v_by_plate")
                      if r["vehicle_id"] == "B"}
            if plates == {"P2"}:
                break
            time.sleep(0.2)
        assert plates == {"P2"}


def test_if_null_and_status_on_missing_row_creates_nothing(probe):
    row = probe.execute(
        "UPDATE probe_r SET rated='x' WHERE id='NOPE' IF rated = null AND status = 'COMPLETED'"
    ).one()
    assert row["[applied]"] is False
    assert list(probe.execute("SELECT id, status, rated FROM probe_r WHERE id='NOPE'")) == []


def _json_row(probe):
    return probe.execute("SELECT id, ts, d, m, s, l, x, b, n FROM probe_j WHERE id='J1'").one()


def test_json_roundtrip(probe):
    ts = datetime(2026, 10, 4, 3, 5, 6, 123000)
    k1, k2 = datetime(2026, 10, 4, 3, 5), datetime(2026, 10, 4, 3, 6)
    probe.execute(
        "INSERT INTO probe_j (id, ts, d, m, s, l, x, b, n) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        ("J1", ts, date(2026, 10, 4), {k1: "REQUESTED", k2: "ACCEPTED"}, {"HCM", "HN"},
         ["Đúng giờ", "Xe sạch"], 8.5, True, None),
    )
    original = _json_row(probe)
    js = probe.execute("SELECT JSON * FROM probe_j WHERE id='J1'").one()["[json]"]
    obj = json.loads(js)
    probe.execute("TRUNCATE probe_j")
    ok = True
    try:
        probe.execute("INSERT INTO probe_j JSON %s", (json.dumps(obj, ensure_ascii=False),))
        again = _json_row(probe)
        ok = again is not None and all(again[c] == original[c] for c in original)
    except Exception:  # noqa: BLE001 - mọi lỗi nghĩa là roundtrip không dùng được
        ok = False
    assert ok == cap.JSON_ROUNDTRIP_OK
