import pytest
from cassandra import WriteTimeout, WriteType

from db.repo import LwtResult
from domain.tz import parse_vn
from services import booking
from services.booking import BookingForm
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:05")
RIDE_ID = "RIDE_20261004100500_ABCD"


def _form(**kw):
    base = dict(ride_id=RIDE_ID, city="HCM", district="Q1", pickup_address="456 Lê Duẩn, Q1",
                destination_address="Sân bay Tân Sơn Nhất, Tân Bình", distance_km=8.1,
                payment_method="MOMO", promo_code="GIAM20")
    base.update(kw)
    return BookingForm(**base)


def _promo(used=5, **kw):
    base = dict(promo_code="GIAM20", description="x", discount_percent=20, max_discount=30000.0,
                min_fare=50000.0, cities={"HCM", "HN"}, usage_limit=500, used_count=used,
                valid_from=parse_vn("2026-09-01 00:00:00"), valid_to=parse_vn("2026-12-31 23:59:59"))
    base.update(kw)
    return base


CUST = {"customer_id": "CUST001", "full_name": "Nguyễn Văn A", "phone": "0901000001",
        "email": "a@x.vn", "address": None, "created_at": None}


# ---------------- validate_booking ----------------
def test_validate_booking_accepts_good_form():
    assert booking.validate_booking(_form()) == []


@pytest.mark.parametrize("kw", [
    dict(ride_id="RIDE_1001"),
    dict(city="DN"),
    dict(district="HOAN_KIEM"),
    dict(pickup_address=""),
    dict(pickup_address="x" * 201),
    dict(destination_address="456 Lê Duẩn, Q1"),
    dict(distance_km=0.0),
    dict(distance_km=500),
    dict(payment_method="BITCOIN"),
])
def test_validate_booking_rejects(kw):
    assert booking.validate_booking(_form(**kw))


# ---------------- quote ----------------
def test_quote_without_code_reads_nothing():
    db = FakeDb()
    q = booking.quote(db, _form(distance_km=1.8, promo_code=None), NOW)
    assert q == booking.Quote(27000.0, 0.0, 27000.0, None)
    assert db.calls == []


def test_quote_with_code_matches_t08_example_and_does_not_reserve():
    db = FakeDb({"B16_promo_get": [_promo()]})
    q = booking.quote(db, _form(), NOW)
    assert (q.fare, q.discount, q.payable, q.promo_error) == (81000.0, 16000.0, 65000.0, None)
    assert db.names() == ["B16_promo_get"]


def test_quote_reports_promo_error_and_keeps_full_price():
    db = FakeDb({"B16_promo_get": [_promo(cities={"HCM"})]})
    q = booking.quote(db, _form(city="HN", district="HOAN_KIEM"), NOW)
    assert q.promo_error == "city" and q.discount == 0.0 and q.payable == q.fare


# ---------------- reserve / release ----------------
def test_reserve_promo_sends_optimistic_lwt():
    db = FakeDb({"B16_promo_get": [_promo(used=5)]})
    res = booking.reserve_promo(db, "GIAM20", "HCM", 81000.0, NOW)
    assert res.ok and res.discount == 16000.0 and res.error is None
    assert db.calls[1] == ("T07_promo_use", (6, "GIAM20", 5))


def test_reserve_promo_exhausted_never_writes():
    db = FakeDb({"B16_promo_get": [_promo(used=500)]})
    res = booking.reserve_promo(db, "GIAM20", "HCM", 81000.0, NOW)
    assert (res.ok, res.error) == (False, "promo_exhausted")
    assert "T07_promo_use" not in db.names()


def test_reserve_promo_retries_after_lost_lwt_then_wins():
    db = FakeDb({"B16_promo_get": [_promo(used=5), _promo(used=6)],
                 "T07_promo_use": [LwtResult(False, {"used_count": 6}), LwtResult(True, None)]})
    res = booking.reserve_promo(db, "GIAM20", "HCM", 81000.0, NOW)
    assert res.ok
    t07 = [p for n, p in db.calls if n == "T07_promo_use"]
    assert t07 == [(6, "GIAM20", 5), (7, "GIAM20", 6)]


def test_reserve_promo_gives_up_as_busy():
    db = FakeDb({"B16_promo_get": [_promo(used=5)] * 3,
                 "T07_promo_use": [LwtResult(False, None)] * 3})
    res = booking.reserve_promo(db, "GIAM20", "HCM", 81000.0, NOW, max_attempts=3)
    assert (res.ok, res.error) == (False, "promo_busy")


def test_reserve_promo_write_timeout_rereads_and_continues():
    timeout = WriteTimeout("cas timeout", write_type=WriteType.CAS)
    db = FakeDb({"B16_promo_get": [_promo(used=5), _promo(used=5)],
                 "T07_promo_use": [timeout, LwtResult(True, None)]})
    res = booking.reserve_promo(db, "GIAM20", "HCM", 81000.0, NOW)
    assert res.ok
    assert db.names().count("B16_promo_get") == 2


def test_reserve_promo_invalid_reason_is_prefixed():
    db = FakeDb({"B16_promo_get": [None]})
    res = booking.reserve_promo(db, "NOPE", "HCM", 81000.0, NOW)
    assert (res.ok, res.error) == (False, "promo_invalid:not_found")


def test_release_promo_decrements_with_expected_value():
    db = FakeDb({"B16_promo_get": [_promo(used=6)]})
    assert booking.release_promo(db, "GIAM20") is True
    assert db.calls[1] == ("T07_promo_use", (5, "GIAM20", 6))


def test_release_promo_never_goes_below_zero():
    db = FakeDb({"B16_promo_get": [_promo(used=0)]})
    assert booking.release_promo(db, "GIAM20") is False
    assert "T07_promo_use" not in db.names()


# ---------------- book_ride ----------------
def test_book_with_promo_orders_reservation_before_ride_insert():
    db = FakeDb({"B02_customer_get": [CUST], "B16_promo_get": [_promo(used=5)]})
    r = booking.book_ride(db, "CUST001", _form(), NOW)
    assert r.ok and r.code == "ok" and r.ride_id == RIDE_ID
    names = db.names()
    assert names.index("T07_promo_use") < names.index("T04_ride_insert")
    assert names[names.index("T04_ride_insert"):] == ["T04_ride_insert", "T04_rbc_insert", "T04_rad_insert"]
    assert names.index("B06_ride_get") < names.index("T07_promo_use")


def test_book_without_promo_touches_no_promotion():
    db = FakeDb({"B02_customer_get": [CUST]})
    r = booking.book_ride(db, "CUST001", _form(promo_code=None), NOW)
    assert r.ok
    assert not any("promo" in n.lower() or n.startswith("B16") or n.startswith("T07") for n in db.names())


def test_book_insert_params_and_aux_keys_share_the_same_values():
    db = FakeDb({"B02_customer_get": [CUST], "B16_promo_get": [_promo(used=5)]})
    booking.book_ride(db, "CUST001", _form(), NOW)
    ride = dict(zip(["ride_id", "customer_id", "name", "phone", "city", "district", "pickup", "dest", "km",
                     "fare", "discount", "promo", "pay", "ride_date", "requested_at", "history"],
                    db.calls[db.names().index("T04_ride_insert")][1]))
    assert ride["fare"] == 81000.0 and ride["discount"] == 16000.0 and ride["promo"] == "GIAM20"
    assert ride["history"] == {NOW: "REQUESTED"}
    rbc = db.calls[db.names().index("T04_rbc_insert")][1]
    rad = db.calls[db.names().index("T04_rad_insert")][1]
    assert rbc[0] == "CUST001" and rbc[1] == ride["ride_date"] and rbc[2] == RIDE_ID and rbc[5] is None
    assert rad[:5] == ("HCM", "Q1", ride["ride_date"], ride["requested_at"], RIDE_ID)


def test_book_duplicate_ride_lwt_returns_slot_and_reports_duplicate_ok():
    db = FakeDb({"B02_customer_get": [CUST],
                 "B16_promo_get": [_promo(used=5), _promo(used=6)],
                 "T04_ride_insert": [LwtResult(False, {"customer_id": "CUST001", "ride_id": RIDE_ID})]})
    r = booking.book_ride(db, "CUST001", _form(), NOW)
    assert r.ok and r.code == "duplicate_ok"
    t07 = [p for n, p in db.calls if n == "T07_promo_use"]
    assert t07 == [(6, "GIAM20", 5), (5, "GIAM20", 6)]
    assert "T04_rbc_insert" not in db.names() and "T04_rad_insert" not in db.names()


def test_book_existing_ride_of_same_customer_is_duplicate_ok_without_touching_promo():
    db = FakeDb({"B02_customer_get": [CUST], "B06_ride_get": [{"ride_id": RIDE_ID, "customer_id": "CUST001"}]})
    r = booking.book_ride(db, "CUST001", _form(), NOW)
    assert r.ok and r.code == "duplicate_ok"
    assert not any(n.startswith(("B16", "T07", "T04")) for n in db.names())


def test_book_existing_ride_of_other_customer_is_duplicate():
    db = FakeDb({"B02_customer_get": [CUST], "B06_ride_get": [{"ride_id": RIDE_ID, "customer_id": "CUST002"}]})
    r = booking.book_ride(db, "CUST001", _form(), NOW)
    assert not r.ok and r.code == "duplicate"


def test_book_unknown_customer_and_invalid_input_touch_nothing_else():
    db = FakeDb()
    assert booking.book_ride(db, "CUST001", _form(), NOW).code == "not_found"
    db2 = FakeDb()
    r = booking.book_ride(db2, "CUST001", _form(city="DN"), NOW)
    assert r.code == "invalid_input" and db2.calls == []


@pytest.mark.parametrize("promo,code,reason", [
    (None, "promo_invalid", "not_found"),
    (_promo(cities={"HN"}), "promo_invalid", "city"),
    (_promo(used=500), "promo_exhausted", None),
])
def test_book_promo_failure_writes_no_ride(promo, code, reason):
    db = FakeDb({"B02_customer_get": [CUST], "B16_promo_get": [promo]})
    r = booking.book_ride(db, "CUST001", _form(), NOW)
    assert not r.ok and r.code == code
    if reason:
        assert r.data["reason"] == reason
    assert "T04_ride_insert" not in db.names()


def test_book_aux_failure_after_lwt_is_partial_not_rolled_back():
    db = FakeDb({"B02_customer_get": [CUST], "T04_rad_insert": [RuntimeError("boom")]})
    r = booking.book_ride(db, "CUST001", _form(promo_code=None), NOW)
    assert r.ok and r.code == "partial"


def test_promo_reason_maps_codes_to_plain_vietnamese():
    assert booking.promo_reason("not_found") == "Mã khuyến mãi không tồn tại."
    assert booking.promo_reason("exhausted") == "Mã khuyến mãi đã hết lượt."
    assert booking.promo_reason("weird") == "Mã khuyến mãi không hợp lệ."
    assert booking.promo_reason(None) is None
