import pytest

from config import BASE_TABLES, Settings, UnsafeKeyspaceError, assert_test_keyspace


def test_defaults():
    s = Settings.from_env({})
    assert s.hosts == ("127.0.0.1",)
    assert s.port == 9042
    assert s.keyspace == "ride_booking"
    assert s.local_dc == "datacenter1"
    assert s.first_month == 202609


def test_hosts_are_split_and_stripped():
    s = Settings.from_env({"CASSANDRA_HOSTS": " 10.0.0.5, 10.0.0.6 "})
    assert s.hosts == ("10.0.0.5", "10.0.0.6")


def test_invalid_keyspace_name_raises():
    with pytest.raises(ValueError):
        Settings.from_env({"CASSANDRA_KEYSPACE": "Ride-Booking"})


@pytest.mark.parametrize("name", ["ride_booking", "ride_booking_test_old"])
def test_guard_rejects_non_test_keyspace(name):
    with pytest.raises(UnsafeKeyspaceError):
        assert_test_keyspace(name)


def test_guard_accepts_test_keyspace():
    assert_test_keyspace("ride_booking_test")


def test_base_tables():
    assert len(BASE_TABLES) == 13
    assert "vehicles_by_plate" not in BASE_TABLES
