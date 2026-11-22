"""Nhận chuyến LWT hai tầng (unit, FakeDb): drivers trước, rides sau, thua ở rides thì trả tài xế."""
from datetime import date

import pytest

from config import AREAS
from db.catalog import STATEMENTS
from db.repo import LwtResult
from domain.tz import parse_vn
from domain.write_matrix import WRITE_MATRIX
from services import driver_presence, rides_flow
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:04")
N_AREAS = sum(len(v) for v in AREAS.values())

RIDE = dict(ride_id="RIDE_1024", customer_id="CUST006", city="HCM", district="TAN_PHU",
            pickup_address="140 Lê Trọng Tấn, Tân Phú", destination_address="Aeon Mall Tân Phú",
            distance_km=1.8, fare=27000.0, status="REQUESTED", driver_id=None,
            ride_date=date(2026, 10, 4), requested_at=parse_vn("2026-10-04 10:00"))
AREA = dict(city="HCM", district="TAN_PHU", driver_id="DRV_551", full_name="Lý Văn Phúc",
            phone="0912000551", rating=4.8, vehicle_plate="51F-123.45", lat=10.8, lng=106.6)


def _db(**extra):
    responses = {"B06_ride_get": [dict(RIDE)], "A06_area_find_driver": [[dict(AREA)]]}
    responses.update(extra)
    return FakeDb(responses)


def test_win_branch_order_and_write_matrix():
    db = _db()
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert r.ok and r.code == "ok" and r.ride_id == "RIDE_1024"
    assert db.names() == (["B06_ride_get", "A06_area_find_driver", "APP07_driver_claim", "T05_ride_accept",
                           "T05_rbc_accept", "T05_rad_accept", "T05_rdm_insert"]
                          + ["T05_area_delete"] * N_AREAS)
    assert N_AREAS == 11
    written = {STATEMENTS[n].table for n in db.names() if STATEMENTS[n].kind in ("write", "lwt")}
    assert set(WRITE_MATRIX["accept"]["required"]) <= written


def test_win_branch_parameters_use_ride_keys_not_input():
    db = _db()
    rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    calls = {n: p for n, p in db.calls if not n.startswith(("B06", "A06", "T05_area"))}
    assert calls["APP07_driver_claim"] == ("DRV_551",)
    assert calls["T05_ride_accept"] == ("DRV_551", "Lý Văn Phúc", "51F-123.45", NOW, {NOW: "ACCEPTED"}, "RIDE_1024")
    assert calls["T05_rbc_accept"] == ("DRV_551", "CUST006", date(2026, 10, 4), "RIDE_1024")
    assert calls["T05_rad_accept"] == ("DRV_551", "HCM", "TAN_PHU", date(2026, 10, 4),
                                       RIDE["requested_at"], "RIDE_1024")
    assert calls["T05_rdm_insert"][:2] == ("DRV_551", 202610)
    # xóa ở MỌI khu vực cấu hình
    deletes = [p for n, p in db.calls if n == "T05_area_delete"]
    assert sorted((c, d) for c, d, _ in deletes) == sorted((c, d) for c, ds in AREAS.items() for d in ds)
    assert all(drv == "DRV_551" for _, _, drv in deletes)


def test_lost_at_rides_releases_driver_and_writes_nothing_else():
    db = _db(T05_ride_accept=[LwtResult(False, {"status": "ACCEPTED"})])
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert not r.ok and r.code == "lwt_lost" and r.current == {"status": "ACCEPTED"}
    names = db.names()
    assert names[names.index("T05_ride_accept") + 1:] == ["APP08_driver_release"]
    assert not any(n.startswith(("T05_rbc", "T05_rad", "T05_rdm", "T05_area")) for n in names)
    assert db.calls[-1] == ("APP08_driver_release", ("DRV_551",))


def test_claim_rejected_does_not_touch_rides():
    db = _db(APP07_driver_claim=[LwtResult(False, {"status": "BUSY"})])
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert not r.ok and r.code == "driver_not_available" and r.current == {"status": "BUSY"}
    assert "T05_ride_accept" not in db.names()
    assert "APP08_driver_release" not in db.names()  # chưa giữ tài xế thì không trả
    assert db.names()[-1] == "APP07_driver_claim"


def test_driver_not_online_never_claims():
    db = FakeDb({"B06_ride_get": [dict(RIDE)], "A06_area_find_driver": [[]]})
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_552", NOW)
    assert not r.ok and r.code == "driver_not_online"
    assert db.names() == ["B06_ride_get", "A06_area_find_driver"]


def test_ride_missing_and_wrong_status():
    db = FakeDb({"B06_ride_get": [None]})
    assert rides_flow.accept_ride(db, "RIDE_X", "DRV_551", NOW).code == "not_found"
    assert db.names() == ["B06_ride_get"]
    taken = dict(RIDE, status="ACCEPTED", driver_id="DRV_553")
    db = FakeDb({"B06_ride_get": [taken]})
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert not r.ok and r.code == "invalid_transition"
    assert r.current == {"status": "ACCEPTED", "driver_id": "DRV_553"}
    assert db.names() == ["B06_ride_get"]


def test_secondary_write_failure_after_win_is_partial_not_rollback():
    db = _db(T05_rad_accept=[RuntimeError("boom")])
    r = rides_flow.accept_ride(db, "RIDE_1024", "DRV_551", NOW)
    assert r.ok and r.code == "partial"
    assert "APP08_driver_release" not in db.names()


def test_find_area_rows_queries_each_city_with_in_list():
    db = FakeDb()
    assert driver_presence.find_area_rows(db, "DRV_551") == []
    assert db.calls == [("A06_area_find_driver", ("HCM", list(AREAS["HCM"]), "DRV_551")),
                        ("A06_area_find_driver", ("HN", list(AREAS["HN"]), "DRV_551"))]
    db = FakeDb()
    driver_presence.find_area_rows(db, "DRV_551", ["HN"])
    assert [p[0] for _, p in db.calls] == ["HN"]


def test_remove_from_all_areas_deletes_every_configured_area():
    db = FakeDb()
    pairs = driver_presence.remove_from_all_areas(db, "DRV_551")
    assert len(pairs) == N_AREAS == db.names().count("T05_area_delete")
    assert set(pairs) == {(c, d) for c, ds in AREAS.items() for d in ds}


def test_lost_race_results_carry_area_and_day():
    want = {"city": "HCM", "district": "TAN_PHU", "day": "2026-10-04"}
    lost = rides_flow.accept_ride(_db(T05_ride_accept=[LwtResult(False, {"status": "ACCEPTED"})]),
                                  "RIDE_1024", "DRV_551", NOW)
    assert lost.code == "lwt_lost" and lost.data == want
    taken_db = FakeDb({"B06_ride_get": [dict(RIDE, status="ACCEPTED", driver_id="DRV_553")]})
    taken = rides_flow.accept_ride(taken_db, "RIDE_1024", "DRV_551", NOW)
    assert taken.code == "invalid_transition" and taken.data == want
    assert taken_db.names() == ["B06_ride_get"]
