import pytest

from domain.money import discount_of, fare_of, normalize_distance

pytestmark = pytest.mark.business


@pytest.mark.parametrize('d,expected', [
    (8.1, 81000.0), (1.8, 27000.0), (0.3, 15000.0),
    (1.0, 20000.0),  # 20.5 -> half-even 20, dung nhu gen_data
    (3.0, 38000.0), (5.0, 54000.0),
])
def test_fare_of(d, expected):
    assert fare_of(d) == expected


@pytest.mark.parametrize('fare,pct,cap,expected', [
    (81000, 20, 30000, 16000.0),
    (53000, 20, 30000, 11000.0),
    (70000, 15, 20000, 10000.0),
    (130000, 15, 20000, 20000.0),
    (200000, 20, 30000, 30000.0),
    (54000, 10, 10000, 5000.0),
])
def test_discount_of(fare, pct, cap, expected):
    assert discount_of(fare, pct, cap) == expected


def test_t08_example_pays_65000():
    assert fare_of(8.1) - discount_of(81000, 20, 30000) == 65000


def test_normalize_distance():
    assert normalize_distance(8.14) == 8.1
    for bad in (0, 0.04, 200.5):
        with pytest.raises(ValueError):
            normalize_distance(bad)
