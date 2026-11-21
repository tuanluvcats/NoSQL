import re
from datetime import datetime, timezone

import pytest

from domain.ids import RIDE_ID_RE, is_new_ride_id, new_customer_id, new_ride_id
from domain.tz import parse_vn

pytestmark = pytest.mark.business


def test_new_ride_id_plus7():
    assert new_ride_id(parse_vn('2026-10-04 10:05'), rand=lambda: 'A1B2') == 'RIDE_20261004100500_A1B2'


def test_new_ride_id_utc_input_converted():
    t = datetime(2026, 10, 4, 3, 5, tzinfo=timezone.utc)
    assert new_ride_id(t, rand=lambda: 'A1B2') == 'RIDE_20261004100500_A1B2'


def test_default_rand_matches_regex():
    rid = new_ride_id(parse_vn('2026-10-04 10:05'))
    assert re.match(RIDE_ID_RE, rid)
    assert is_new_ride_id(rid)


def test_seed_id_is_not_new_format():
    assert is_new_ride_id('RIDE_1001') is False


def test_new_customer_id():
    t = parse_vn('2026-10-04 10:05')
    assert new_customer_id(t, rand=lambda: 'FF01') == 'CUST_20261004100500_FF01'
    assert re.match(r'^CUST_\d{14}_[0-9A-F]{4}$', new_customer_id(t))
