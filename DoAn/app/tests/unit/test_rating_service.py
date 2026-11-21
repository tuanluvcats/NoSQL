"""Đánh giá chuyến bằng LWT rated_at (unit, FakeDb)."""
import pytest

from db.catalog import STATEMENTS
from db.repo import LwtResult
from domain.tz import parse_vn
from domain.write_matrix import WRITE_MATRIX
from services import rating
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:50")
RIDE = dict(ride_id="RIDE_1010", customer_id="CUST003", driver_id="DRV_555", status="COMPLETED", rated_at=None)
AVG = {"so_danh_gia": 3, "diem_tb": 4.666666666666667}


def _db(ride=None, **extra):
    db = FakeDb({"B06_ride_get": [dict(RIDE if ride is None else ride)], "A05_rating_avg": [dict(AVG)], **extra})
    return db


def _written_tables(db):
    return {STATEMENTS[n].table for n in db.names() if STATEMENTS[n].kind in ("write", "lwt")}


def test_rate_order_when_driver_offline_and_no_area_write():
    db = _db()
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "Tốt", ["Lịch sự"], NOW)
    assert r.ok and r.code == "ok"
    assert db.names() == ["B06_ride_get", "APP14_ride_rate", "T09_rating_insert", "A05_rating_avg",
                          "T09_driver_rating", "A06_area_find_driver", "A06_area_find_driver"]
    assert "T09_area_rating" not in db.names()  # Review Focus 1: không có dòng khu vực thì không ghi (chống dòng ma)
    calls = dict(db.calls)
    assert calls["APP14_ride_rate"] == (NOW, "RIDE_1010", "CUST003")
    assert calls["T09_rating_insert"] == ("DRV_555", NOW, "RIDE_1010", "CUST003", 5.0, "Tốt", ["Lịch sự"])
    ts, avg, drv = calls["T09_driver_rating"]
    assert (avg, drv) == (4.67, "DRV_555")  # làm tròn 2 chữ số
    assert isinstance(ts, int) and ts > 1_600_000_000_000_000  # micro giây: USING TIMESTAMP
    assert set(WRITE_MATRIX["rate"]["required"]) <= _written_tables(db)


def test_rate_updates_every_area_row_with_rounded_average():
    area = {"city": "HCM", "district": "Q3", "driver_id": "DRV_555"}
    db = _db(A06_area_find_driver=[[area], []])
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "", [], NOW)
    assert r.ok
    assert db.names()[-3:] == ["A06_area_find_driver", "A06_area_find_driver", "T09_area_rating"]
    name, (ts, *rest) = db.calls[-1]
    assert name == "T09_area_rating" and tuple(rest) == (4.67, "HCM", "Q3", "DRV_555")
    assert ts == dict(db.calls)["T09_driver_rating"][0]  # cùng một mốc thời gian cho cả hai bảng
    assert set(WRITE_MATRIX["rate"]["optional"]) <= _written_tables(db)


def test_rating_timestamp_taken_before_average_read(monkeypatch):
    """Hai khách đánh giá cùng lúc: lệnh đọc AVG sau thấy nhiều dữ liệu hơn, nên phải mang timestamp lớn hơn để thắng
    (last-write-wins của Cassandra), dù lệnh ghi của nó tới sau hay trước."""
    import services.rating as mod
    seq = iter([100, 200])
    monkeypatch.setattr(mod, "_micros", lambda: next(seq))
    db1, db2 = _db(), _db()
    rating.rate_ride(db1, "RIDE_1010", "CUST003", 5, "", [], NOW)
    rating.rate_ride(db2, "RIDE_1010", "CUST003", 5, "", [], NOW)
    assert dict(db1.calls)["T09_driver_rating"][0] < dict(db2.calls)["T09_driver_rating"][0]


def test_rate_lwt_not_applied_means_already_rated_and_no_rating_row():
    db = _db(APP14_ride_rate=[LwtResult(False, {"rated_at": NOW, "status": "COMPLETED", "customer_id": "CUST003"})])
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "", [], NOW)
    assert not r.ok and r.code == "already_rated"
    assert r.current["status"] == "COMPLETED"
    assert db.names() == ["B06_ride_get", "APP14_ride_rate"]
    assert "T09_rating_insert" not in db.names()


def test_rate_guards_before_any_write():
    r = rating.rate_ride(FakeDb(), "RIDE_X", "CUST003", 5, "", [], NOW)
    assert r.code == "not_found"

    db = _db()
    assert rating.rate_ride(db, "RIDE_1010", "CUST001", 5, "", [], NOW).code == "forbidden"
    assert db.names() == ["B06_ride_get"]

    db = _db(dict(RIDE, status="ONGOING"))
    assert rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "", [], NOW).code == "invalid_transition"
    assert db.names() == ["B06_ride_get"]

    db = _db(dict(RIDE, rated_at=NOW))
    assert rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "", [], NOW).code == "already_rated"
    assert db.names() == ["B06_ride_get"]


@pytest.mark.parametrize("stars,comment,tags", [
    (0, "", []), (6, "", []), (True, "", []), ("5", "", []), (4.5, "", []),
    (5, "x" * 501, []), (5, "", ["Không có trong danh sách"]), (5, "", "Lịch sự"),
])
def test_rate_invalid_input_rejected_before_lwt(stars, comment, tags):
    db = _db()
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", stars, comment, tags, NOW)
    assert not r.ok and r.code == "invalid_input"
    assert db.names() == ["B06_ride_get"]


def test_rate_secondary_failure_after_lwt_is_partial_not_rollback():
    db = _db(T09_rating_insert=[RuntimeError("boom")])
    r = rating.rate_ride(db, "RIDE_1010", "CUST003", 5, "", [], NOW)
    assert r.ok and r.code == "partial"
    assert "APP14_ride_rate" in db.names()


def test_backfill_rated_at_counts_applied_only():
    t1, t2 = parse_vn("2026-10-03 08:52"), parse_vn("2026-10-02 15:41")
    db = FakeDb({
        "APP03_drivers_scan": [[{"driver_id": "DRV_555"}, {"driver_id": "DRV_556"}]],
        "B14_ratings": [[{"rated_at": t1, "ride_id": "RIDE_1001"}, {"rated_at": t2, "ride_id": "RIDE_1016"}], []],
        "APP21_ride_backfill_rated": [LwtResult(True, None), LwtResult(False, {"rated_at": t2})],
    })
    assert rating.backfill_rated_at(db) == 1
    assert dict(db.calls)["APP21_ride_backfill_rated"] in ((t1, "RIDE_1001"), (t2, "RIDE_1016"))
    assert db.names().count("APP21_ride_backfill_rated") == 2
