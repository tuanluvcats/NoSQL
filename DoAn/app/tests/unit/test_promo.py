from datetime import datetime

import pytest

from domain.promo import promo_error
from domain.tz import parse_vn

pytestmark = pytest.mark.business

NOW = parse_vn('2026-10-04 10:05')


def giam20(**kw):
    p = dict(code='GIAM20', valid_from=datetime(2026, 8, 31, 17, 0), valid_to=datetime(2026, 12, 31, 16, 59, 59),
             cities={'HCM', 'HN'}, min_fare=50000, usage_limit=500, used_count=5,
             discount_percent=20, max_discount=30000)
    p.update(kw)
    return p


def test_ok_cases():
    assert promo_error(giam20(), 'HCM', 81000, NOW) is None
    assert promo_error(giam20(), 'HN', 81000, NOW) is None


def test_city_and_min_fare():
    assert promo_error(giam20(), 'DN', 81000, NOW) == 'city'
    assert promo_error(giam20(), 'HCM', 27000, NOW) == 'min_fare'


def test_time_window():
    assert promo_error(giam20(), 'HCM', 81000, parse_vn('2027-01-01 00:00')) == 'expired'
    assert promo_error(giam20(), 'HCM', 81000, parse_vn('2026-08-31 23:59')) == 'not_started'


def test_exhausted_and_not_found():
    assert promo_error(giam20(used_count=500), 'HCM', 81000, NOW) == 'exhausted'
    assert promo_error(None, 'HCM', 81000, NOW) == 'not_found'


def test_null_cities_and_counts_tolerated():
    assert promo_error(giam20(cities=None), 'HCM', 81000, NOW) == 'city'
    assert promo_error(giam20(used_count=None), 'HCM', 81000, NOW) is None
