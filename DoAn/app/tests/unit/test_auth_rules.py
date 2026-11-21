import pytest

from domain.auth import can_cancel_ride, can_view_ride, effective_role, lock_refusal

pytestmark = pytest.mark.auth


def test_effective_role():
    assert effective_role('OPERATOR') == 'ADMIN'
    assert effective_role('ADMIN') == 'ADMIN'
    assert effective_role('CUSTOMER') == 'CUSTOMER'
    assert effective_role('DRIVER') == 'DRIVER'
    assert effective_role('HACKER') is None
    assert effective_role(None) is None


def test_lock_refusal():
    assert lock_refusal({'username': 'admin', 'role': 'ADMIN', 'is_active': True}, 'admin', 2) == 'self_lock'
    assert lock_refusal({'username': 'dieuphoi', 'role': 'OPERATOR', 'is_active': True}, 'admin', 1) == 'last_admin'
    assert lock_refusal({'username': 'cust001', 'role': 'CUSTOMER', 'is_active': True}, 'admin', 1) is None
    assert lock_refusal({'username': 'dieuphoi', 'role': 'OPERATOR', 'is_active': True}, 'admin', 2) is None


def test_can_view_ride():
    assert not can_view_ride('CUSTOMER', 'CUST001', {'customer_id': 'CUST002', 'status': 'COMPLETED'})
    assert can_view_ride('CUSTOMER', 'CUST002', {'customer_id': 'CUST002', 'status': 'COMPLETED'})
    assert can_view_ride('DRIVER', 'DRV_551', {'driver_id': None, 'status': 'REQUESTED'})
    assert not can_view_ride('DRIVER', 'DRV_551', {'driver_id': 'DRV_552', 'status': 'ACCEPTED'})
    assert can_view_ride('DRIVER', 'DRV_551', {'driver_id': 'DRV_551', 'status': 'ONGOING'})
    assert can_view_ride('ADMIN', 'x', {'customer_id': 'CUST002', 'status': 'COMPLETED'})
    assert can_view_ride('OPERATOR', 'x', {'customer_id': 'CUST002', 'status': 'COMPLETED'})
    assert not can_view_ride('HACKER', 'x', {'customer_id': 'x', 'status': 'REQUESTED'})


def test_can_cancel_ride():
    assert not can_cancel_ride('DRIVER', 'DRV_551', {'driver_id': 'DRV_551', 'status': 'REQUESTED'})
    assert can_cancel_ride('DRIVER', 'DRV_551', {'driver_id': 'DRV_551', 'status': 'ACCEPTED'})
    assert not can_cancel_ride('CUSTOMER', 'CUST003', {'customer_id': 'CUST003', 'status': 'ONGOING'})
    assert can_cancel_ride('CUSTOMER', 'CUST003', {'customer_id': 'CUST003', 'status': 'REQUESTED'})
    assert not can_cancel_ride('CUSTOMER', 'CUST004', {'customer_id': 'CUST003', 'status': 'REQUESTED'})
    assert can_cancel_ride('ADMIN', 'x', {'customer_id': 'CUST003', 'status': 'ACCEPTED'})
    assert not can_cancel_ride('ADMIN', 'x', {'customer_id': 'CUST003', 'status': 'COMPLETED'})
