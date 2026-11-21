import threading
from datetime import date

import pytest

from db import trace
from domain.ids import new_ride_id
from domain.tz import parse_vn, to_date, to_vn, yyyymm
from domain.write_matrix import WRITE_MATRIX
from services import booking
from services.booking import BookingForm

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:05")
PICKUP = "456 Lê Duẩn, Q1"
DEST = "Sân bay Tân Sơn Nhất, Tân Bình"


def _form(ride_id=None, **kw):
    base = dict(ride_id=ride_id or new_ride_id(NOW, rand=lambda: "AAAA"), city="HCM", district="Q1",
                pickup_address=PICKUP, destination_address=DEST, distance_km=8.1,
                payment_method="MOMO", promo_code="GIAM20")
    base.update(kw)
    return BookingForm(**base)


def _history(db, customer_id):
    return db.rows("B07_customer_history", [customer_id])


def test_book_with_promo_writes_ride_and_aux_tables_per_matrix(db):
    f = _form()
    trace.start_request()
    r = booking.book_ride(db, "CUST001", f, NOW)
    written = trace.tables_written(trace.current())
    assert r.ok and r.code == "ok" and r.ride_id == f.ride_id

    spec = WRITE_MATRIX["book"]
    assert set(spec["required"]) <= set(written) and "promotions" in written
    assert written.index("promotions") < written.index("rides") < written.index("rides_by_customer")

    ride = db.one("B06_ride_get", [f.ride_id])
    assert ride["fare"] == 81000.0 and ride["discount"] == 16000.0
    assert ride["promo_code"] == "GIAM20" and ride["status"] == "REQUESTED"
    assert to_date(ride["ride_date"]) == date(2026, 10, 4)
    assert len(ride["status_history"]) == 1
    assert ride["customer_name"] and ride["customer_phone"]
    assert ride["driver_id"] is None

    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6

    # khóa của các bảng phụ khớp chính xác với dòng rides vừa đọc
    rbc = [x for x in _history(db, "CUST001") if x["ride_id"] == f.ride_id]
    assert len(rbc) == 1 and rbc[0]["driver_id"] is None and rbc[0]["status"] == "REQUESTED"
    assert to_date(rbc[0]["ride_date"]) == to_date(ride["ride_date"])
    area = [x for x in db.rows("B11_area_day", ["HCM", "Q1", date(2026, 10, 4)]) if x["ride_id"] == f.ride_id]
    assert len(area) == 1
    assert area[0]["requested_at"] == ride["requested_at"]
    assert area[0]["customer_id"] == "CUST001" and area[0]["driver_id"] is None
    assert area[0]["payment_method"] == "MOMO" and area[0]["fare"] == 81000.0


def test_resubmit_same_ride_id_keeps_single_ride_and_single_promo_slot(db):
    f = _form()
    first = booking.book_ride(db, "CUST001", f, NOW)
    assert first.ok and first.code == "ok"
    again = booking.book_ride(db, "CUST001", f, NOW)
    assert again.ok and again.code == "duplicate_ok"
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6
    hist = _history(db, "CUST001")
    assert len(hist) == 5  # 4 seed + 1
    assert [h["ride_id"] for h in hist].count(f.ride_id) == 1


def test_resubmit_with_later_clock_still_single_ride(db):
    f = _form()
    assert booking.book_ride(db, "CUST001", f, NOW).code == "ok"
    later = parse_vn("2026-10-04 10:09:30")
    assert booking.book_ride(db, "CUST001", f, later).code == "duplicate_ok"
    assert len(_history(db, "CUST001")) == 5
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6


def test_same_ride_id_from_other_customer_is_duplicate_and_promo_untouched(db):
    f = _form()
    assert booking.book_ride(db, "CUST001", f, NOW).ok
    other = booking.book_ride(db, "CUST002", f, NOW)
    assert not other.ok and other.code == "duplicate"
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 6
    assert len(_history(db, "CUST002")) == 5  # seed, không thêm


def test_promo_city_mismatch_is_rejected_without_ride(db):
    f = _form(promo_code="HCMXANH", city="HN", district="HOAN_KIEM")
    r = booking.book_ride(db, "CUST001", f, NOW)
    assert not r.ok and r.code == "promo_invalid" and r.data["reason"] == "city"
    assert db.one("B06_ride_get", [f.ride_id]) is None
    assert db.one("B16_promo_get", ["HCMXANH"])["used_count"] == 3
    assert len(_history(db, "CUST001")) == 4


def test_quote_no_code(db):
    q = booking.quote(db, _form(distance_km=1.8, promo_code=None), NOW)
    assert q == booking.Quote(27000.0, 0.0, 27000.0, None)


def test_quote_with_code_does_not_consume_a_slot(db):
    q = booking.quote(db, _form(), NOW)
    assert (q.fare, q.discount, q.payable) == (81000.0, 16000.0, 65000.0)
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 5


def test_release_promo_gives_slot_back(db):
    assert booking.release_promo(db, "GIAM20") is True
    assert db.one("B16_promo_get", ["GIAM20"])["used_count"] == 4


def test_promo_race_never_exceeds_limit(db, raw):
    raw.execute(
        "INSERT INTO promotions (promo_code, description, discount_percent, max_discount, min_fare, cities, "
        "usage_limit, used_count, valid_from, valid_to) VALUES ('RACE3', 'race', 10, 10000.0, 0.0, {'HCM'}, 3, 0, "
        "'2026-09-01 00:00:00+0700', '2026-12-31 23:59:59+0700')")
    barrier = threading.Barrier(8)
    results: dict[int, object] = {}
    ids = {i: new_ride_id(NOW, rand=lambda i=i: f"{i:04X}") for i in range(1, 9)}

    def worker(i: int):
        f = _form(ride_id=ids[i], district="TAN_PHU", distance_km=5.0, payment_method="CASH", promo_code="RACE3")
        barrier.wait()
        try:
            results[i] = booking.book_ride(db, f"CUST{i:03d}", f, NOW)
        except BaseException as e:  # noqa: BLE001
            results[i] = e

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, 9)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert len(results) == 8 and not any(isinstance(v, BaseException) for v in results.values()), results
    ok = [v for v in results.values() if v.ok]
    lost = [v for v in results.values() if not v.ok]
    assert len(ok) == 3 and all(v.code == "ok" for v in ok)
    assert len(lost) == 5 and all(v.code == "promo_exhausted" for v in lost)
    promo = db.one("B16_promo_get", ["RACE3"])
    assert promo["used_count"] == 3 and promo["used_count"] <= promo["usage_limit"]
    existing = [i for i in ids if db.one("B06_ride_get", [ids[i]]) is not None]
    assert len(existing) == 3
    for i in existing:
        ride = db.one("B06_ride_get", [ids[i]])
        assert ride["fare"] == 54000.0 and ride["discount"] == 5000.0


def test_vn_morning_ride_uses_plus7_date_in_every_table(db):
    clock = parse_vn("2026-11-01 06:30")  # 2026-10-31 23:30 UTC
    f = _form(ride_id=new_ride_id(clock, rand=lambda: "BEEF"), district="TAN_PHU", promo_code=None)
    assert booking.book_ride(db, "CUST002", f, clock).ok
    ride = db.one("B06_ride_get", [f.ride_id])
    assert to_date(ride["ride_date"]) == date(2026, 11, 1)
    assert to_vn(ride["requested_at"]).hour == 6 and yyyymm(clock) == 202611
    hist = [h for h in _history(db, "CUST002") if h["ride_id"] == f.ride_id]
    assert len(hist) == 1 and to_date(hist[0]["ride_date"]) == date(2026, 11, 1)
    assert db.rows("B08_customer_history_range", ["CUST002", date(2026, 10, 31), date(2026, 10, 31)]) == []
    in_day = db.rows("B08_customer_history_range", ["CUST002", date(2026, 11, 1), date(2026, 11, 1)])
    assert [h["ride_id"] for h in in_day] == [f.ride_id]
    on_1st = [x for x in db.rows("B11_area_day", ["HCM", "TAN_PHU", date(2026, 11, 1)]) if x["ride_id"] == f.ride_id]
    on_31st = [x for x in db.rows("B11_area_day", ["HCM", "TAN_PHU", date(2026, 10, 31)]) if x["ride_id"] == f.ride_id]
    assert len(on_1st) == 1 and on_31st == []
