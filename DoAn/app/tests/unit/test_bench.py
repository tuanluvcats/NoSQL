"""Công cụ đo hiệu năng: phần tính toán thuần (không cần Cassandra)."""
import pytest

from tools import bench

pytestmark = pytest.mark.nosql


def test_summarize_percentiles():
    r = bench.summarize([float(x) for x in range(1, 101)])
    assert r == {"n": 100, "p50": 50.5, "p95": 95.0, "max": 100.0}


def test_summarize_rejects_empty():
    with pytest.raises(ValueError):
        bench.summarize([])


def test_race_winners_counts_true():
    assert bench.race_winners([False, True, False]) == 1
    assert bench.race_winners([True, True]) == 2


def test_refuses_non_test_keyspace():
    from config import Settings
    with pytest.raises(Exception):
        bench.run(Settings.from_env({}), "ride_booking", 1, 1, 2)


def test_render_markdown_reports_bad_rounds():
    meta = {"version": "3.11.4", "host": "127.0.0.1", "keyspace": "k_test", "rows": 22, "threads": 8, "when": "x"}
    lat = {"Đọc": {"n": 3, "p50": 1.0, "p95": 2.0, "max": 3.0}}
    text = bench.render_markdown(meta, lat, {"naive": [1, 3, 2], "lwt": [1, 1, 1]})
    assert "| naive | 3 | 1 | 2 | 3 |" in text
    assert "| lwt | 3 | 3 | 0 | 1 |" in text
    assert "| Đọc | 3 | 1.0 | 2.0 | 3.0 |" in text
