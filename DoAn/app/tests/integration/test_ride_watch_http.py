"""Đường dẫn hỏi trạng thái chuyến trên Cassandra thật (keyspace test): dấu phiên bản đổi khi tài xế nhận chuyến."""
import re

import pytest

from domain.tz import parse_vn
from tests.integration.conftest import login as http_login

pytestmark = [pytest.mark.business, pytest.mark.auth]

BOOK_AT = parse_vn("2026-10-04 10:05")
ACCEPT_AT = parse_vn("2026-10-04 10:07")  # khác giờ đặt, để status_history có hai mốc riêng


def _payload(ride_id):
    return {"ride_id": ride_id, "city": "HCM", "district": "Q1", "pickup_address": "456 Lê Duẩn, Q1",
            "destination_address": "Sân bay Tân Sơn Nhất, Tân Bình", "distance_km": "8.1",
            "payment_method": "MOMO", "promo_code": ""}


def _ride_id_from(html: str) -> str:
    m = re.search(r'name="ride_id"[^>]*value="([^"]+)"', html) or re.search(r'value="([^"]+)"[^>]*name="ride_id"', html)
    assert m
    return m.group(1)


def test_status_follows_booking_then_accept(client_factory, db):
    cust = client_factory(clock=lambda: BOOK_AT)
    assert http_login(cust, "cust001").status_code == 303
    rid = _ride_id_from(cust.get("/customer/book").text)
    assert cust.post("/customer/book", data=_payload(rid)).status_code == 303

    first = cust.get(f"/rides/{rid}/status")
    assert first.status_code == 200 and first.headers["cache-control"] == "no-store"
    body = first.json()
    assert body["status"] == "REQUESTED" and body["active"] is True
    page = cust.get(f"/rides/{rid}").text  # trang chi tiết mang cùng dấu và nhịp 5 giây
    assert f'data-stamp="{body["stamp"]}"' in page and 'data-every="5"' in page

    drv = client_factory(clock=lambda: ACCEPT_AT)
    assert http_login(drv, "drv551").status_code == 303
    assert drv.post(f"/rides/{rid}/accept").status_code == 303

    second = cust.get(f"/rides/{rid}/status").json()
    assert second["status"] == "ACCEPTED" and second["active"] is True
    assert second["stamp"] != body["stamp"]
    assert second["stamp"].startswith("ACCEPTED|") and second["stamp"].endswith("|DRV_551")

    # hỏi thêm lần nữa khi chưa có gì đổi: dấu giữ nguyên
    assert cust.get(f"/rides/{rid}/status").json()["stamp"] == second["stamp"]
    # tài xế của chuyến cũng hỏi được, khách khác thì không
    assert drv.get(f"/rides/{rid}/status").status_code == 200
    other = client_factory(clock=lambda: ACCEPT_AT)
    http_login(other, "cust002")
    assert other.get(f"/rides/{rid}/status").status_code == 403
    guest = client_factory(clock=lambda: ACCEPT_AT)
    assert guest.get(f"/rides/{rid}/status").status_code == 401
