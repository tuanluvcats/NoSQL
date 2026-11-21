"""Trang NoSQL minh họa: catalog sinh tự động, ma trận ghi, collection, clustering DESC, truy vấn thiếu partition key."""
import html

import pytest
from cassandra import InvalidRequest

from db.catalog import STATEMENTS
from domain.write_matrix import WRITE_MATRIX
from services.system_info import collections_demo, missing_pk_demo
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.nosql

A10_CQL = "SELECT ride_id FROM rides WHERE customer_id = 'CUST001'"


def _real_cassandra_error(raw_session) -> str:
    """Thông điệp lỗi THẬT do Cassandra trả về, lấy trực tiếp từ server (không viết tay)."""
    with pytest.raises(InvalidRequest) as exc:
        raw_session.execute(A10_CQL)
    return str(exc.value)


def test_nosql_page_requires_login(client_factory):
    r = client_factory().get("/nosql")
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert client_factory().post("/nosql/missing-pk").status_code == 303


def test_nosql_page_lists_every_statement_code_and_write_matrix(client_factory):
    c = client_factory()
    http_login(c, "admin")
    r = c.get("/nosql")
    assert r.status_code == 200
    for stmt in STATEMENTS.values():
        assert stmt.code in r.text, stmt.code
    for event in WRITE_MATRIX:
        assert event in r.text
    assert "Q17" in r.text and "A10" in r.text


def test_any_logged_in_role_can_view_nosql_page(client_factory):
    c = client_factory()
    http_login(c, "cust001")
    assert c.get("/nosql").status_code == 200


def test_missing_pk_shows_real_cassandra_error_and_explanation(client_factory, raw):
    expected = _real_cassandra_error(raw)
    assert "ALLOW FILTERING" in expected
    c = client_factory()
    http_login(c, "admin")
    r = c.post("/nosql/missing-pk")
    assert r.status_code == 200
    page = html.unescape(r.text)
    assert expected in page  # đúng từng ký tự thông điệp thật của server 3.11.4
    assert "ALLOW FILTERING" in r.text
    assert "partition key" in page and "customer_id" in page  # kèm giải thích
    assert "rides_by_customer" in page  # chỉ đường sang bảng đúng truy vấn


def test_missing_pk_demo_returns_exact_message_and_does_not_write(db, raw):
    expected = _real_cassandra_error(raw)
    assert missing_pk_demo(db) == expected


def test_collections_demo_data(db):
    d = collections_demo(db)
    hist = d["B06"]["status_history"]
    assert [s for _, s in sorted(hist.items())] == ["REQUESTED", "ACCEPTED", "ONGOING", "COMPLETED"]
    assert d["A08_rating_tags"] and all(isinstance(r["tags"], (list, tuple)) for r in d["A08_rating_tags"])
    assert [t for r in d["A08_rating_ride_1007"] for t in r["tags"]] == ["Đường vòng"]  # list<text> của RIDE_1007
    cities = {r["promo_code"]: set(r["cities"]) for r in d["A08_promo_cities"]}
    assert cities["HANOI10"] == {"HN"} and cities["GIAM20"] == {"HCM", "HN"}
    months = [r["requested_at"] for r in d["B10"]]
    assert len(months) >= 2 and months == sorted(months, reverse=True)  # clustering DESC


def test_page_shows_collections_and_desc_ordering(client_factory):
    c = client_factory()
    http_login(c, "admin")
    page = html.unescape(c.get("/nosql").text)
    assert "HANOI10" in page and "Đường vòng" in page  # set cities + tag của RIDE_1007
    assert "REQUESTED" in page and "COMPLETED" in page  # map status_history
    assert "map<timestamp" in page
    assert "list<text>" in page and "set<text>" in page
    assert "CLUSTERING ORDER BY (requested_at DESC" in page
