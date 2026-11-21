"""Ma trận ghi CASSANDRA.MD §3.7 (ô có ngoặc là optional) + bổ sung của plan."""
from __future__ import annotations

WRITE_MATRIX: dict[str, dict[str, tuple[str, ...]]] = {
    'register': {
        'required': ('user_accounts', 'customers'),
        'optional': (),
    },
    'driver_online': {
        'required': ('drivers', 'drivers_by_area', 'driver_locations'),
        'optional': (),
    },
    'book': {
        'required': ('rides', 'rides_by_customer', 'rides_by_area_date'),
        'optional': ('promotions',),
    },
    'accept': {
        'required': ('rides', 'rides_by_customer', 'rides_by_area_date', 'rides_by_driver_month',
                     'drivers', 'drivers_by_area'),
        'optional': (),
    },
    'start': {
        'required': ('rides', 'rides_by_customer', 'rides_by_area_date', 'rides_by_driver_month',
                     'driver_locations'),
        'optional': (),
    },
    'complete': {
        'required': ('rides', 'rides_by_customer', 'rides_by_area_date', 'rides_by_driver_month',
                     'payments_by_city_date', 'drivers', 'drivers_by_area'),
        'optional': (),
    },
    'cancel': {
        'required': ('rides', 'rides_by_customer', 'rides_by_area_date'),
        'optional': ('rides_by_driver_month', 'drivers', 'drivers_by_area', 'promotions'),
    },
    'rate': {
        'required': ('rides', 'ratings_by_driver', 'drivers'),
        'optional': ('drivers_by_area',),
    },
}
