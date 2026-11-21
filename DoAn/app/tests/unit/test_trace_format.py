"""Tham số trong panel CQL hiển thị theo cú pháp gần CQL, không theo repr của Python."""
from datetime import date, datetime, timedelta, timezone

import pytest

from db.trace import fmt_param

pytestmark = pytest.mark.nosql

VN = timezone(timedelta(hours=7))


def test_datetime_shown_as_cql_timestamp():
    assert fmt_param(datetime(2026, 11, 22, 1, 58, 41, 925000, tzinfo=VN)) == "'2026-11-22 01:58:41.925+0700'"


def test_map_with_timestamp_key():
    v = {datetime(2026, 11, 22, 1, 58, 41, tzinfo=VN): "ACCEPTED"}
    assert fmt_param(v) == "{'2026-11-22 01:58:41.000+0700': 'ACCEPTED'}"


def test_scalars_lists_sets():
    assert fmt_param("DRV_555") == "DRV_555"
    assert fmt_param(81000.0) == "81000.0"
    assert fmt_param(None) == "null"
    assert fmt_param(date(2026, 11, 22)) == "'2026-11-22'"
    assert fmt_param(["Q1", "Q3"]) == "['Q1', 'Q3']"
    assert fmt_param({"HCM"}) == "{'HCM'}"


def test_no_python_repr_in_rendered_panel():
    from routes.deps import templates
    assert "cql" in templates.env.filters


def test_repo_trace_params_have_no_python_repr():
    from db.repo import _redact_param
    v = {datetime(2026, 11, 22, 2, 0, 13, 770000, tzinfo=VN): "ACCEPTED"}
    assert _redact_param(v) == "{'2026-11-22 02:00:13.770+0700': 'ACCEPTED'}"
    assert "datetime" not in _redact_param(datetime(2026, 11, 22, tzinfo=VN))
