"""Trang tài xế: chuyến chờ dạng thẻ, người thua tranh chuyến về lại danh sách chuyến chờ, trang trạng thái nhận chuyến."""
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from config import Settings
from db.repo import LwtResult
from main import create_app
from domain.tz import parse_vn
from tests.fakes import FakeDb

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")
RIDE = {"ride_id": "RIDE_A", "customer_id": "C1", "city": "HCM", "district": "TAN_PHU", "status": "REQUESTED",
        "driver_id": None, "ride_date": date(2026, 10, 4), "requested_at": parse_vn("2026-10-04 10:00"),
        "pickup_address": "140 Lê Trọng Tấn", "destination_address": "Aeon Mall", "distance_km": 1.8, "fare": 27000.0}
AREA = {"city": "HCM", "district": "TAN_PHU", "driver_id": "DRV_1", "full_name": "Tài", "vehicle_plate": "51K-567.89"}
WAITING = "/driver/waiting?city=HCM&district=TAN_PHU&day=2026-10-04"
ROWS = [dict(RIDE, payment_method="CASH"),
        dict(RIDE, ride_id="RIDE_B", requested_at=parse_vn("2026-10-04 10:05"), pickup_address="12 Âu Cơ",
             fare=35000.0, payment_method="MOMO")]
URL = "/driver/waiting?city=HCM&district=TAN_PHU"
DRIVER = {"driver_id": "DRV_1", "full_name": "Tài", "status": "OFFLINE", "rating": 5.0}


def _client(role=None, ref_id=None, extra=None, tech=False, cookies=None):
    responses = {}
    if role:
        responses["B01_account_get"] = [{"username": "u1", "role": role, "ref_id": ref_id, "full_name": "Người Dùng",
                                         "is_active": True, "password_hash": "x"}] * 20
    responses.update(extra or {})
    db = FakeDb(responses)
    app = create_app(Settings.from_env({}), db=db, clock=lambda: NOW)

    @app.post("/_login")
    def fake_login(request: Request):
        request.session["username"] = "u1"
        return {"ok": True}

    c = TestClient(app, raise_server_exceptions=False, follow_redirects=False)
    if role:
        c.post("/_login")
    for k, v in (cookies or {}).items():
        c.cookies.set(k, v)
    if tech:
        c.cookies.set("tech_mode", "1")
    return c, db


def _driver(extra=None, **kw):
    return _client("DRIVER", "DRV_1", extra, **kw)


# ------------------------------------------------------------------ P2.2 thua tranh chuyến
def test_driver_who_loses_the_race_goes_back_to_same_waiting_list():
    c, db = _driver({"B06_ride_get": [RIDE], "A06_area_find_driver": [[AREA]],
                     "T05_ride_accept": [LwtResult(False, {"status": "ACCEPTED"})]})
    r = c.post("/rides/RIDE_A/accept")
    assert r.status_code == 303 and r.headers["location"] == WAITING


def test_ride_already_taken_also_returns_to_waiting_list():
    c, db = _driver({"B06_ride_get": [dict(RIDE, status="ACCEPTED", driver_id="DRV_9")]})
    r = c.post("/rides/RIDE_A/accept")
    assert r.status_code == 303 and r.headers["location"] == WAITING


def test_driver_not_online_still_goes_to_driver_home():
    c, db = _driver({"B06_ride_get": [RIDE]})
    r = c.post("/rides/RIDE_A/accept")
    assert r.status_code == 303 and r.headers["location"] == "/driver"


# ------------------------------------------------------------------ P2.3 danh sách chuyến chờ
def test_waiting_list_is_cards_with_unique_accept_names():
    c, db = _driver({"APP15_area_waiting": [ROWS]})
    html = c.get(URL).text
    assert "<table" not in html
    assert html.count('<li class="ride-card">') == 2
    assert 'aria-label="Nhận chuyến số 1, đón tại 140 Lê Trọng Tấn"' in html
    assert 'aria-label="Nhận chuyến số 2, đón tại 12 Âu Cơ"' in html
    for want in ("27.000đ", "10 phút trước", "5 phút trước", "Chuyến chờ ở Tân Phú"):
        assert want in html
    assert html.count("chip-cash") == 1
    assert "Về trang tài xế" not in html
    assert "<code>RIDE_A</code>" not in html


def test_waiting_auto_refresh_has_pause_control_and_starts_paused_in_tech_mode():
    c, _ = _driver({"APP15_area_waiting": [ROWS]})
    html = c.get(URL).text
    assert 'data-autorefresh="20"' in html and "Tạm dừng tự làm mới" in html
    assert "data-start-paused" not in html
    c, _ = _driver({"APP15_area_waiting": [ROWS]}, tech=True)
    assert "data-start-paused" in c.get(URL).text


def test_empty_waiting_list_explains_and_opens_filter():
    c, _ = _driver()
    html = c.get(URL).text
    assert "Chưa có chuyến nào đang chờ ở Tân Phú." in html
    assert '<details class="disclosure filter" open>' in html


def test_waiting_day_accepts_vietnamese_date():
    c, db = _driver({"APP15_area_waiting": [ROWS]})
    r = c.get(URL + "&day=03/10/2026")
    assert r.status_code == 200
    assert [p for n, p in db.calls if n == "APP15_area_waiting"] == [("HCM", "TAN_PHU", date(2026, 10, 3))]
    assert "ngày 03/10/2026" in r.text and "Đặt lúc" in r.text
    assert 'type="text" id="w_day" name="day" value="03/10/2026"' in r.text  # ô ngày hiện theo ngày/tháng/năm


# ------------------------------------------------------------------ P2.4 trang trạng thái nhận chuyến
def test_offline_driver_sees_one_clear_next_step():
    c, _ = _driver({"B03_driver_get": [DRIVER]})
    html = c.get("/driver").text
    for want in ("Bạn đang nghỉ", 'action="/driver/online"', "Bật nhận chuyến", '<details class="disclosure gps-fields">'):
        assert want in html
    assert 'action="/driver/offline"' not in html
    assert "DRV_1" not in html


def test_online_driver_sees_area_plate_and_waiting_link():
    c, _ = _driver({"B03_driver_get": [dict(DRIVER, status="AVAILABLE")], "A06_area_find_driver": [[AREA], []]})
    html = c.get("/driver").text
    for want in ("Đang nhận chuyến ở Tân Phú", 'href="/driver/waiting?city=HCM&amp;district=TAN_PHU"',
                 'class="plate plate-sm"', "Tắt nhận chuyến", "Chuyển sang khu vực này", 'value="51K-567.89"'):
        assert want in html


def test_busy_driver_sees_current_ride_without_extra_reads():
    c, db = _driver({"B03_driver_get": [dict(DRIVER, status="BUSY")],
                     "B10_driver_month": [[{"ride_id": "RIDE_X", "status": "ACCEPTED"}]],
                     "B06_ride_get": [{"ride_id": "RIDE_X", "driver_id": "DRV_1", "status": "ACCEPTED",
                                       "pickup_address": "A", "destination_address": "B"}]})
    html = c.get("/driver").text
    for want in ("Bạn đang có chuyến", "Đến điểm đón khách", 'href="/rides/RIDE_X"', "Mở chuyến đang chạy"):
        assert want in html
    assert db.names().count("B06_ride_get") == 1
    assert 'action="/driver/offline"' not in html


def test_offline_form_is_prefilled_from_own_cookie_only():
    c, _ = _driver({"B03_driver_get": [DRIVER]}, cookies={"driver_last_area": "DRV_1|HCM|TAN_PHU|51K-567.89"})
    html = c.get("/driver").text
    assert 'value="51K-567.89"' in html
    assert re.search(r'value="TAN_PHU" data-city="HCM"\s+selected', html)
    for cookie in ("DRV_9|HCM|TAN_PHU|51K-567.89", "DRV_1|XX|Q1|51K"):
        c, _ = _driver({"B03_driver_get": [DRIVER]}, cookies={"driver_last_area": cookie})
        assert 'value="51K' not in c.get("/driver").text


def test_going_online_remembers_area():
    c, _ = _driver({"B03_driver_get": [DRIVER],
                    "B05_vehicle_by_plate": [[{"driver_id": "DRV_1", "plate": "51K-567.89"}]]})
    r = c.post("/driver/online", data={"city": "HCM", "district": "TAN_PHU", "plate": "51K-567.89"})
    assert r.status_code == 303
    assert "driver_last_area=DRV_1|HCM|TAN_PHU|51K-567.89" in r.headers["set-cookie"]
