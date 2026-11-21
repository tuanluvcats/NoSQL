from datetime import date, datetime, timedelta, timezone

import pytest

from domain.tz import VN, fmt_vn, now_vn, parse_vn, to_date, to_vn, truncate_ms, vn_date, yyyymm

pytestmark = pytest.mark.business


def test_to_vn_naive_is_utc():
    assert to_vn(datetime(2026, 10, 31, 23, 30)) == datetime(2026, 11, 1, 6, 30, tzinfo=VN)
    assert to_vn(datetime(2026, 10, 31, 23, 30)).utcoffset() == timedelta(hours=7)


def test_vn_date_uses_plus7_not_utc():
    t = parse_vn('2026-11-01 06:30')
    assert vn_date(t) == date(2026, 11, 1)
    assert t.astimezone(timezone.utc).date() == date(2026, 10, 31)


def test_yyyymm_plus7():
    assert yyyymm(parse_vn('2026-11-01 06:30')) == 202611


def test_pay_date_just_after_midnight():
    assert vn_date(parse_vn('2026-11-01 00:10')) == date(2026, 11, 1)


def test_now_vn_millisecond_precision_and_aware():
    n = now_vn()
    assert n.microsecond % 1000 == 0
    assert n.utcoffset() == timedelta(hours=7)


def test_truncate_ms():
    t = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=VN)
    assert truncate_ms(t).microsecond == 123000


def test_parse_and_fmt():
    assert parse_vn('2026-11-01 06:30:15') == datetime(2026, 11, 1, 6, 30, 15, tzinfo=VN)
    assert fmt_vn(parse_vn('2026-11-01 06:30')) == '01/11/2026 06:30:00'


def test_to_date_variants():
    class FakeCassDate:
        def date(self):
            return date(2026, 11, 1)

    assert to_date(date(2026, 11, 1)) == date(2026, 11, 1)
    assert to_date('2026-11-01') == date(2026, 11, 1)
    assert to_date(FakeCassDate()) == date(2026, 11, 1)
