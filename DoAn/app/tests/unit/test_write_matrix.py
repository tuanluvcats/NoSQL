import pytest

from domain.write_matrix import WRITE_MATRIX

pytestmark = pytest.mark.nosql


def test_accept_required():
    assert set(WRITE_MATRIX['accept']['required']) == {
        'rides', 'rides_by_customer', 'rides_by_area_date', 'rides_by_driver_month', 'drivers', 'drivers_by_area'}


def test_events_and_keys():
    assert set(WRITE_MATRIX) == {'register', 'driver_online', 'book', 'accept', 'start', 'complete', 'cancel', 'rate'}
    for ev in WRITE_MATRIX.values():
        assert set(ev) == {'required', 'optional'}


def test_additions_over_section_3_7():
    assert 'promotions' in WRITE_MATRIX['book']['optional']
    assert 'promotions' in WRITE_MATRIX['cancel']['optional']
    assert WRITE_MATRIX['rate']['required'] == ('rides', 'ratings_by_driver', 'drivers')
    assert WRITE_MATRIX['rate']['optional'] == ('drivers_by_area',)


def test_cancel_optional_matches_parenthesized_cells():
    assert set(WRITE_MATRIX['cancel']['optional']) == {
        'rides_by_driver_month', 'drivers', 'drivers_by_area', 'promotions'}


def test_every_event_has_vietnamese_label():
    from domain.write_matrix import EVENT_LABELS
    assert set(EVENT_LABELS) == set(WRITE_MATRIX)
    assert EVENT_LABELS["book"] == "Đặt xe"


def test_panel_does_not_show_internal_identifier():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[2] / "templates" / "_trace.html").read_text(encoding="utf-8")
    assert "WRITE_MATRIX" not in text
