"""Lịch sử, thu nhập tháng, doanh thu, thống kê khu vực, GPS, CSV và phân quyền các trang báo cáo (9.3, 9.4).

Con số kỳ vọng lấy từ dữ liệu seed thật (02_data.cql), múi giờ nghiệp vụ +07. Các test service chỉ đọc nên dùng
`db_readonly`; test HTTP đăng nhập (ghi last_login_at) hoặc ghi GPS dùng `db`/`client_factory`."""
from datetime import date, timedelta

import pytest

from domain.tz import VN, parse_vn
from services import reports
from tests.integration.conftest import login as http_login

pytestmark = pytest.mark.business

NOW = parse_vn("2026-10-04 10:10")


def _clock():
    return NOW


def _hm(dt):
    """Giờ:phút theo +07 (kiểm múi giờ: driver trả datetime naive UTC)."""
    return dt.astimezone(VN).strftime("%H:%M") if dt.tzinfo else None


def _client(client_factory, username):
    c = client_factory(clock=_clock)
    assert http_login(c, username).status_code == 303
    return c


# ------------------------------------------------------------------ lịch sử khách
def test_customer_history_newest_first_and_date_filter(db_readonly):
    rows = reports.customer_history(db_readonly, "CUST001")
    assert len(rows) == 4 and rows[0]["ride_id"] == "RIDE_1021"
    ranged = reports.customer_history(db_readonly, "CUST001", date(2026, 10, 1), date(2026, 10, 4))
    assert [r["ride_id"] for r in ranged] == ["RIDE_1021", "RIDE_1001", "RIDE_1013"]
    only_from = reports.customer_history(db_readonly, "CUST001", date_from=date(2026, 10, 4))
    assert [r["ride_id"] for r in only_from] == ["RIDE_1021"]
    only_to = reports.customer_history(db_readonly, "CUST001", date_to=date(2026, 9, 30))
    assert [r["ride_id"] for r in only_to] == ["RIDE_1007"]


def test_customer_history_of_unknown_customer_is_empty(db_readonly):
    assert reports.customer_history(db_readonly, "CUST_NOPE") == []


# ------------------------------------------------------------------ thu nhập tháng, đánh giá
def test_driver_month_income_matches_seed_a01(db_readonly):
    m = reports.driver_month(db_readonly, "DRV_551", 202610)
    assert m["income"]["so_chuyen"] == 2 and m["income"]["tong_cuoc"] == 159000.0
    assert m["rides"][0]["ride_id"] == "RIDE_1020"  # clustering requested_at DESC
    stamps = [r["requested_at"] for r in m["rides"]]
    assert stamps == sorted(stamps, reverse=True)


def test_driver_month_without_completed_rides_is_zero_not_none(db_readonly):
    m = reports.driver_month(db_readonly, "DRV_551", 202601)
    assert m["rides"] == []
    assert m["income"] == {"so_chuyen": 0, "tong_cuoc": 0.0, "cuoc_tb": 0.0, "cuoc_thap_nhat": 0.0,
                           "cuoc_cao_nhat": 0.0}


def test_driver_ratings_matches_seed(db_readonly):
    r = reports.driver_ratings(db_readonly, "DRV_551")
    assert r["count"] == 5 and r["avg"] == 4.8 and len(r["rows"]) == 5


# ------------------------------------------------------------------ doanh thu, khu vực
def test_revenue_day_matches_seed_a02(db_readonly):
    r = reports.revenue_day(db_readonly, "HCM", date(2026, 10, 3))
    assert r["by_method"]["CASH"] == {"count": 2, "amount": 158000.0, "discount": 0.0}
    assert r["by_method"]["MOMO"]["amount"] == 26000.0
    assert r["by_method"]["ZALOPAY"]["amount"] == 110000.0 and r["by_method"]["ZALOPAY"]["discount"] == 20000.0
    assert r["by_method"]["CARD"]["count"] == 0 and r["by_method"]["CARD"]["amount"] == 0.0
    assert r["total_count"] == 4 and r["total_amount"] == 294000.0
    assert set(r["by_method"]) == {"CASH", "MOMO", "ZALOPAY", "CARD"}


def test_revenue_day_without_payments_is_all_zero(db_readonly):
    r = reports.revenue_day(db_readonly, "HN", date(2026, 1, 1))
    assert r["total_count"] == 0 and r["total_amount"] == 0.0 and r["total_discount"] == 0.0


def test_revenue_7days_matches_seed_a03(db_readonly):
    r = reports.revenue_7days(db_readonly, "HCM", date(2026, 10, 4))
    assert (r["count"], r["amount"]) == (21, 1269000.0)
    assert r["days"] == [date(2026, 9, 28) + timedelta(days=i) for i in range(7)]  # 7 ngày kết thúc 04/10, tăng dần
    hn = reports.revenue_7days(db_readonly, "HN", date(2026, 10, 4))
    assert (hn["count"], hn["amount"]) == (6, 545000.0)


def test_area_day_stats_matches_seed_a04_in_plus07(db_readonly):
    s = reports.area_day_stats(db_readonly, "HCM", "Q1", date(2026, 10, 4))
    assert s["so_chuyen"] == 6 and s["tong_cuoc"] == 256000.0
    assert _hm(s["som_nhat"]) == "07:10" and s["som_nhat"].utcoffset().total_seconds() == 7 * 3600
    assert _hm(s["muon_nhat"]) == "09:30"


def test_area_day_stats_empty_day(db_readonly):
    s = reports.area_day_stats(db_readonly, "HCM", "Q1", date(2026, 1, 1))
    assert s["so_chuyen"] == 0 and s["tong_cuoc"] == 0.0 and s["som_nhat"] is None and s["muon_nhat"] is None


def test_area_drivers_multi_district_in(db_readonly):
    rows = reports.area_drivers(db_readonly, "HCM", ["Q1", "Q3", "BINH_THANH"])
    assert {r["driver_id"] for r in rows} == {"DRV_554", "DRV_553"}


def test_area_drivers_rejects_unknown_districts(db_readonly):
    assert reports.area_drivers(db_readonly, "HCM", ["XYZ"]) == []
    assert reports.area_drivers(db_readonly, "ZZ", ["Q1"]) == []


# ------------------------------------------------------------------ chi tiết chuyến + status_history
def test_ride_detail_history_in_time_order_plus07(db_readonly):
    d = reports.ride_detail(db_readonly, "RIDE_1007")
    assert [s for _, s in d["history"]] == ["REQUESTED", "ACCEPTED", "ONGOING", "COMPLETED"]
    times = [t for t, _ in d["history"]]
    assert times == sorted(times)
    assert times[0].strftime("%Y-%m-%d %H:%M %z") == "2026-09-29 17:45 +0700"
    assert reports.ride_detail(db_readonly, "RIDE_NOPE") is None


# ------------------------------------------------------------------ GPS
def test_driver_track_latest_and_route_of_day(db_readonly):
    t = reports.driver_track(db_readonly, "DRV_552", date(2026, 10, 4))
    assert t["latest"]["lat"] == 10.795 and _hm(t["latest"]["ts"]) == "09:48"
    assert len(t["track"]) == 6
    assert [p["ts"] for p in t["track"]] == sorted((p["ts"] for p in t["track"]), reverse=True)


def test_driver_track_empty_day(db_readonly):
    t = reports.driver_track(db_readonly, "DRV_552", date(2026, 1, 1))
    assert t["latest"] is None and t["track"] == []


def test_record_location_writes_point_in_plus07_day(db):
    r = reports.record_location(db, "DRV_552", 10.8, 106.7, 21.5, parse_vn("2026-10-05 00:30"))
    assert r.ok and r.code == "ok"
    t = reports.driver_track(db, "DRV_552", date(2026, 10, 5))  # 00:30 +07 vẫn là ngày 05, không phải 04 (UTC)
    assert t["latest"]["lat"] == 10.8 and t["latest"]["speed_kmh"] == 21.5 and len(t["track"]) == 1
    assert len(reports.driver_track(db, "DRV_552", date(2026, 10, 4))["track"]) == 6


@pytest.mark.parametrize("lat,lng,speed", [(91.0, 106.7, 0.0), (10.8, 181.0, 0.0), (None, 106.7, 0.0),
                                           (10.8, None, 0.0), (10.8, 106.7, -1.0), (10.8, 106.7, 400.0)])
def test_record_location_rejects_invalid_values_without_writing(db, lat, lng, speed):
    r = reports.record_location(db, "DRV_552", lat, lng, speed, NOW)
    assert not r.ok and r.code == "invalid_input"
    assert len(reports.driver_track(db, "DRV_552", date(2026, 10, 4))["track"]) == 6


# ------------------------------------------------------------------ CSV qua HTTP (ADMIN)
def test_admin_exports_history_csv(client_factory):
    c = _client(client_factory, "admin")
    r = c.get("/admin/export/history.csv?customer_id=CUST001")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers.get("content-disposition", "")
    lines = r.content.decode("utf-8-sig").splitlines()
    assert len(lines) == 5 and lines[0] == ",".join(reports.HISTORY_COLUMNS)
    assert lines[1].startswith("2026-10-04,RIDE_1021,")
    assert r.content[:3] == b"\xef\xbb\xbf"
    assert "password_hash" not in r.text and "pbkdf2" not in r.text and "8d969eef" not in r.text


def test_admin_exports_payments_csv(client_factory):
    c = _client(client_factory, "dieuphoi")  # OPERATOR gộp vào ADMIN
    r = c.get("/admin/export/payments.csv?city=HCM&day=2026-10-03")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.content.decode("utf-8-sig").splitlines()
    assert lines[0] == ",".join(reports.PAYMENT_COLUMNS) and len(lines) == 1 + 4
    assert "password_hash" not in r.text


@pytest.mark.parametrize("url", ["/admin/export/history.csv?customer_id=",
                                 "/admin/export/history.csv",
                                 "/admin/export/payments.csv?city=ZZ&day=2026-10-03",
                                 "/admin/export/payments.csv?city=HCM&day=khong-phai-ngay"])
def test_admin_export_bad_input_is_400(client_factory, url):
    assert _client(client_factory, "admin").get(url).status_code in (400, 422)


# ------------------------------------------------------------------ trang HTML
def test_customer_history_page_shows_only_own_rides(client_factory, db):
    c = _client(client_factory, "cust001")
    page = c.get("/customer/rides")
    assert page.status_code == 200
    for rid in ("RIDE_1021", "RIDE_1001", "RIDE_1013", "RIDE_1007"):
        assert rid in page.text
    assert page.text.index("RIDE_1021") < page.text.index("RIDE_1007")  # mới nhất trước
    assert "RIDE_1024" not in page.text and "RIDE_1022" not in page.text
    # khách không chọn được người khác bằng tham số
    spoof = c.get("/customer/rides?customer_id=CUST006")
    assert "RIDE_1024" not in spoof.text and "RIDE_1021" in spoof.text
    ranged = c.get("/customer/rides?from=2026-10-01&to=2026-10-04")
    assert "RIDE_1013" in ranged.text and "RIDE_1007" not in ranged.text
    assert c.get("/customer/rides?from=hôm-qua").status_code == 400


def test_customer_history_page_roles(client_factory):
    assert _client(client_factory, "drv551").get("/customer/rides").status_code == 403
    assert _client(client_factory, "admin").get("/customer/rides").status_code == 403
    g = client_factory(clock=_clock).get("/customer/rides")
    assert g.status_code == 303 and g.headers["location"].startswith("/login")


def test_driver_income_page_is_own_income_only(client_factory):
    c = _client(client_factory, "drv551")
    page = c.get("/driver/income")  # tháng mặc định theo đồng hồ +07: 202610
    assert page.status_code == 200 and "159.000" in page.text and "RIDE_1020" in page.text
    spoof = c.get("/driver/income?driver_id=DRV_552&yyyymm=202610")
    assert "RIDE_1020" in spoof.text  # vẫn là thu nhập của chính mình
    other = _client(client_factory, "drv552").get("/driver/income?yyyymm=202610")
    assert other.status_code == 200 and "RIDE_1020" not in other.text and "159.000" not in other.text
    assert c.get("/driver/income?yyyymm=abc").status_code == 400
    assert c.get("/driver/income?yyyymm=202613").status_code == 400


def test_driver_income_and_ratings_roles(client_factory):
    for path in ("/driver/income", "/driver/ratings"):
        assert _client(client_factory, "cust001").get(path).status_code == 403
        assert _client(client_factory, "admin").get(path).status_code == 403
        g = client_factory(clock=_clock).get(path)
        assert g.status_code == 303 and g.headers["location"].startswith("/login")


def test_driver_ratings_page_shows_own_average(client_factory):
    page = _client(client_factory, "drv551").get("/driver/ratings")
    assert page.status_code == 200 and "4.8" in page.text and "5" in page.text


def test_admin_reports_page_shows_seed_numbers(client_factory):
    c = _client(client_factory, "admin")
    page = c.get("/admin/reports?city=HCM&day=2026-10-03")
    assert page.status_code == 200
    assert "294.000" in page.text and "158.000" in page.text and "110.000" in page.text
    page = c.get("/admin/reports?city=HCM&district=Q1&day=2026-10-04")
    assert "256.000" in page.text and "07:10" in page.text and "09:30" in page.text
    assert "1.269.000" in page.text  # 7 ngày kết thúc ngày 04/10
    assert c.get("/admin/reports?city=ZZ").status_code == 400
    assert c.get("/admin/reports?day=sai").status_code == 400


def test_admin_reports_default_day_is_today_in_plus07(client_factory):
    page = _client(client_factory, "admin").get("/admin/reports")
    assert page.status_code == 200 and "2026-10-04" in page.text and "04/10/2026" in page.text


@pytest.mark.parametrize("path", ["/admin/reports", "/admin/areas", "/admin/export/history.csv?customer_id=CUST001",
                                  "/admin/export/payments.csv?city=HCM&day=2026-10-03",
                                  "/admin/drivers/DRV_552/track"])
def test_report_pages_only_admin_or_operator(client_factory, path):
    for who in ("cust001", "drv551"):
        assert _client(client_factory, who).get(path).status_code == 403, (who, path)
    g = client_factory(clock=_clock).get(path)
    assert g.status_code == 303 and g.headers["location"].startswith("/login")
    assert _client(client_factory, "dieuphoi").get(path).status_code == 200


def test_admin_areas_page_lists_drivers(client_factory):
    page = _client(client_factory, "admin").get("/admin/areas?city=HCM&districts=Q1&districts=Q3&districts=BINH_THANH")
    assert page.status_code == 200 and "DRV_554" in page.text and "DRV_553" in page.text
    assert _client(client_factory, "admin").get("/admin/areas?city=ZZ").status_code == 400


def test_admin_track_page_shows_latest_and_route(client_factory):
    page = _client(client_factory, "admin").get("/admin/drivers/DRV_552/track?day=2026-10-04")
    assert page.status_code == 200 and "10.795" in page.text and "09:48" in page.text and "09:38" in page.text
    assert _client(client_factory, "admin").get("/admin/drivers/DRV_552/track?day=sai").status_code == 400


def test_ride_detail_page_lists_status_history_in_order(client_factory):
    c = _client(client_factory, "cust001")
    page = c.get("/rides/RIDE_1007")
    assert page.status_code == 200
    body = page.text[page.text.index("Lịch sử trạng thái"):]
    order = [body.index(s) for s in ("Đang tìm tài xế", "Tài xế đang đến", "Đang trong chuyến", "Hoàn thành")]
    assert order == sorted(order) and "29/09/2026 17:45" in body


def test_driver_location_post_records_own_point_only(client_factory, db):
    c = _client(client_factory, "drv552")
    r = c.post("/driver/location", data={"lat": "10.8", "lng": "106.7", "speed": "30", "driver_id": "DRV_551"})
    assert r.status_code == 303
    mine = reports.driver_track(db, "DRV_552", date(2026, 10, 4))
    assert mine["latest"]["lat"] == 10.8 and len(mine["track"]) == 7  # 6 điểm seed + 1 điểm mới (10:10 +07)
    assert len(reports.driver_track(db, "DRV_551", date(2026, 10, 4))["track"]) == 6  # không ghi hộ người khác
    bad = c.post("/driver/location", data={"lat": "abc", "lng": "106.7"})
    assert bad.status_code in (303, 400) and len(reports.driver_track(db, "DRV_552", date(2026, 10, 4))["track"]) == 7


def test_driver_location_post_roles(client_factory, db):
    assert _client(client_factory, "cust001").post("/driver/location", data={"lat": "1", "lng": "1"}).status_code == 403
    g = client_factory(clock=_clock).post("/driver/location", data={"lat": "1", "lng": "1"})
    assert g.status_code == 303 and g.headers["location"].startswith("/login")
    assert len(reports.driver_track(db, "DRV_552", date(2026, 10, 4))["track"]) == 6
