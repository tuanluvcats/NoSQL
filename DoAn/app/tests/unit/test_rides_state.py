from datetime import datetime

import pytest

from domain.rides import CANCELLABLE, STATUSES, can_transition, history_entries
from domain.tz import VN

pytestmark = pytest.mark.business


def test_valid_transitions():
    assert can_transition('REQUESTED', 'ACCEPTED')
    assert can_transition('REQUESTED', 'CANCELLED')
    assert can_transition('ACCEPTED', 'ONGOING')
    assert can_transition('ONGOING', 'COMPLETED')
    assert can_transition(None, 'REQUESTED')


def test_invalid_transitions():
    assert not can_transition('ONGOING', 'CANCELLED')
    assert not can_transition('ACCEPTED', 'COMPLETED')
    assert not can_transition('COMPLETED', 'CANCELLED')
    assert not can_transition(None, 'ACCEPTED')


def test_constants():
    assert CANCELLABLE == ('REQUESTED', 'ACCEPTED')
    assert set(STATUSES) == {'REQUESTED', 'ACCEPTED', 'ONGOING', 'COMPLETED', 'CANCELLED'}


def test_history_entries_sorted_and_plus7():
    out = history_entries({datetime(2026, 10, 4, 3, 6): 'ACCEPTED', datetime(2026, 10, 4, 3, 5): 'REQUESTED'})
    assert [s for _, s in out] == ['REQUESTED', 'ACCEPTED']
    assert out[0][0] == datetime(2026, 10, 4, 10, 5, tzinfo=VN)


def test_history_entries_empty():
    assert history_entries(None) == []
    assert history_entries({}) == []
