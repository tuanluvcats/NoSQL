"""Bộ lọc Jinja dùng chung: tiền kèm "đ", ngày giờ theo +07; đăng ký ở routes.deps nên mọi template và test đều thấy."""
from datetime import datetime

import pytest

from routes.deps import templates

pytestmark = pytest.mark.business


def test_vnd_appends_dong_sign():
    vnd = templates.env.filters["vnd"]
    assert vnd(65000) == "65.000đ"
    assert vnd(1269000.0) == "1.269.000đ"
    assert vnd(None) == "0đ"


def test_dmy_hm_shows_vietnam_time():
    dmy_hm = templates.env.filters["dmy_hm"]
    assert dmy_hm(datetime(2026, 10, 3, 17, 30)) == "04/10/2026 00:30"  # naive = UTC
    assert dmy_hm(None) == "-"


def test_date_and_money_filters_are_registered_by_deps():
    for name in ("vnd", "hm", "dmy", "dmy_hms", "dmy_hm"):
        assert name in templates.env.filters, name
    assert "ride_headline" in templates.env.globals
