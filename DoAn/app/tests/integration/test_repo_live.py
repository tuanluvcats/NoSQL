import pytest

pytestmark = pytest.mark.nosql


def test_vehicle_by_plate_via_mv(db):
    assert db.one("B05_vehicle_by_plate", ["51K-567.89"])["vehicle_id"] == "VEH_555"


def test_lwt_on_missing_row_not_applied_and_no_ghost(db):
    assert db.lwt("T02_account_lock", ["nobody_x"]).applied is False
    assert db.one("B01_account_get", ["nobody_x"]) is None


def test_every_catalog_statement_prepares(raw):
    """Mỗi câu CQL trong catalog phải được Cassandra thật prepare được (đúng cú pháp, đúng cột)."""
    from db.catalog import STATEMENTS

    failed = {}
    for name, s in STATEMENTS.items():
        try:
            raw.prepare(s.cql)
        except Exception as e:  # noqa: BLE001 - gom lỗi để báo hết một lần
            failed[name] = f"{type(e).__name__}: {e}"
    assert not failed, failed


def test_prepared_param_counts_match_catalog(raw):
    from db.catalog import STATEMENTS

    for name, s in STATEMENTS.items():
        p = raw.prepare(s.cql)
        assert len(p.column_metadata or []) == s.cql.count("?"), name


def test_lwt_reject_returns_current_and_trace(db):
    from db import trace

    trace.start_request()
    r = db.lwt("T05_ride_accept", ["DRV_X", "n", "p", None, {}, "RIDE_NOT_EXIST"])
    assert r.applied is False
    (e,) = trace.current()
    assert e.kind == "lwt" and e.applied is False and e.partition_key == {"ride_id": "RIDE_NOT_EXIST"}
    assert db.one("B06_ride_get", ["RIDE_NOT_EXIST"]) is None
