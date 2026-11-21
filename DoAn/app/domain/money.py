"""Tính tiền; dùng đúng hàm round của Python (half-even) như gen_data.py."""
from __future__ import annotations


def fare_of(distance_km: float) -> float:
    return float(max(15000, round((12000 + 8500 * distance_km) / 1000) * 1000))


def discount_of(fare: float, percent: int, cap: float) -> float:
    return float(min(cap, round(fare * percent / 100 / 1000) * 1000))


def normalize_distance(d: float) -> float:
    d = round(float(d), 1)
    if not (0.1 <= d <= 200):
        raise ValueError('Quãng đường phải trong khoảng 0.1 đến 200 km')
    return d
