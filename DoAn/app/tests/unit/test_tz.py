from datetime import date, datetime, timedelta, timezone

import pytest

from domain.tz import (VN, fmt_ago, fmt_vn, month_label, now_vn, parse_day, parse_vn, shift_month, to_date, to_vn,
                       truncate_ms, vn_date, yyyymm)

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


def test_parse_day_accepts_vietnamese_and_iso():
    assert parse_day("04/10/2026") == date(2026, 10, 4)
    assert parse_day("2026-10-04") == date(2026, 10, 4)
    assert parse_day(" 4/10/2026 ") == date(2026, 10, 4)
    for bad in ("10/2026", "hôm-qua", "", "31/02/2026"):
        with pytest.raises(ValueError):
            parse_day(bad)


def test_fmt_ago_short_relative_times():
    now = parse_vn("2026-10-04 10:10")
    assert fmt_ago(parse_vn("2026-10-04 10:09:30"), now) == "vừa xong"
    assert fmt_ago(parse_vn("2026-10-04 10:09"), now) == "1 phút trước"
    assert fmt_ago(parse_vn("2026-10-04 10:00"), now) == "10 phút trước"
    assert fmt_ago(parse_vn("2026-10-04 07:10"), now) == "3 giờ trước"
    assert fmt_ago(parse_vn("2026-10-02 08:00"), now) == "02/10/2026 08:00"
    assert fmt_ago(datetime(2026, 10, 4, 3, 0), now) == "10 phút trước"  # naive = UTC = 10:00 +07
    assert fmt_ago(parse_vn("2026-10-04 10:20"), now) == "vừa xong"


def test_shift_month_and_label():
    assert shift_month(202601, -1) == 202512
    assert shift_month(202612, 1) == 202701
    assert shift_month(202610, 0) == 202610
    assert month_label(202609) == "09/2026"
