import re

import pytest

from config import BASE_TABLES
from db.catalog import RIDE_COLS, STATEMENTS, Stmt

pytestmark = pytest.mark.nosql

EXPECTED_NAMES = (
    "B01_account_get",
    "T01_account_insert",
    "T02_login_touch",
    "T02_account_lock",
    "T02_account_unlock",
    "APP01_accounts_scan",
    "B02_customer_get",
    "B18_customer_insert",
    "B19_customer_update",
    "B20_customer_delete",
    "APP02_customers_scan",
    "B03_driver_get",
    "APP03_drivers_scan",
    "APP04_driver_insert",
    "APP05_driver_update",
    "APP06_driver_delete",
    "APP20_driver_online",
    "APP07_driver_claim",
    "APP08_driver_release",
    "APP09_driver_offline",
    "T09_driver_rating",
    "B04_vehicle_get",
    "B05_vehicle_by_plate",
    "APP10_vehicles_scan",
    "APP11_vehicle_insert",
    "APP12_vehicle_update",
    "APP13_vehicle_delete",
    "B12_area_drivers",
    "A06_area_multi",
    "A06_area_find_driver",
    "T03_area_insert",
    "T05_area_delete",
    "T09_area_rating",
    "T03_location_insert",
    "B13_location_latest",
    "Q14_location_track",
    "B06_ride_get",
    "T04_ride_insert",
    "T04_rbc_insert",
    "T04_rad_insert",
    "T05_ride_accept",
    "T05_rbc_accept",
    "T05_rad_accept",
    "T05_rdm_insert",
    "T06_ride_start",
    "T06_rbc_status",
    "T06_rad_status",
    "T06_rdm_status",
    "T08_ride_complete",
    "T08_payment_insert",
    "T10_ride_cancel",
    "APP14_ride_rate",
    "APP21_ride_backfill_rated",
    "B07_customer_history",
    "B08_customer_history_range",
    "B09_customer_has_rides",
    "APP23_rbc_get",
    "B10_driver_month",
    "APP22_driver_has_rides",
    "APP25_rdm_get",
    "A01_driver_income",
    "B11_area_day",
    "APP15_area_waiting",
    "APP24_rad_get",
    "A04_area_stats",
    "B14_ratings",
    "A08_rating_tags",
    "T09_rating_insert",
    "A05_rating_avg",
    "B15_payments_day",
    "APP26_payment_get",
    "A02_revenue_method",
    "A03_revenue_days",
    "B16_promo_get",
    "A08_promo_cities",
    "APP16_promos_scan",
    "APP17_promo_insert",
    "APP18_promo_update",
    "APP19_promo_delete",
    "T07_promo_use",
    "T11_promo_city_add",
    "T11_promo_city_remove",
    "SYS_local",
    "SYS_tables",
    "SYS_views",
    "SYS_columns",
)

SYSTEM_TABLES = {"system.local", "system_schema.tables", "system_schema.views", "system_schema.columns"}
ALLOWED_TABLES = set(BASE_TABLES) | {"vehicles_by_plate"} | SYSTEM_TABLES

SCHEMA_PARTITION_KEYS = {
    "customers": ("customer_id",),
    "drivers": ("driver_id",),
    "vehicles": ("vehicle_id",),
    "vehicles_by_plate": ("license_plate",),
    "rides_by_customer": ("customer_id",),
    "user_accounts": ("username",),
    "rides": ("ride_id",),
    "rides_by_driver_month": ("driver_id", "yyyymm"),
    "rides_by_area_date": ("city", "district", "ride_date"),
    "drivers_by_area": ("city", "district"),
    "driver_locations": ("driver_id", "day"),
    "ratings_by_driver": ("driver_id",),
    "payments_by_city_date": ("city", "pay_date"),
    "promotions": ("promo_code",),
}


def test_all_expected_names_present():
    assert len(EXPECTED_NAMES) == len(set(EXPECTED_NAMES))
    assert set(EXPECTED_NAMES) <= set(STATEMENTS)
    assert set(STATEMENTS) == set(EXPECTED_NAMES)


def test_keys_match_names_and_type():
    for name, s in STATEMENTS.items():
        assert isinstance(s, Stmt)
        assert s.name == name


def test_tables_are_known():
    for s in STATEMENTS.values():
        assert s.table in ALLOWED_TABLES, s.name


def test_kind_matches_cql():
    for s in STATEMENTS.values():
        assert s.kind in ("read", "scan", "write", "lwt"), s.name
        if s.name == "APP12_vehicle_update":
            continue  # theo db.capabilities
        assert (s.kind == "lwt") == (" IF " in s.cql), s.name


def test_app12_kind_follows_capabilities():
    s = STATEMENTS["APP12_vehicle_update"]
    assert s.kind == ("lwt" if " IF EXISTS" in s.cql else "write")
    assert s.cql.startswith("UPDATE vehicles SET")


def test_reads_start_with_select_and_writes_do_not():
    for s in STATEMENTS.values():
        is_select = s.cql.startswith("SELECT ")
        assert is_select == (s.kind in ("read", "scan")), s.name


def test_no_forbidden_cql():
    for s in STATEMENTS.values():
        up = s.cql.upper()
        assert "SELECT *" not in up, s.name
        assert "BATCH" not in up, s.name
        assert "USING TTL" not in up and " TTL(" not in up, s.name
        assert "COUNTER" not in up, s.name


def test_name_prefix_is_code():
    for name, s in STATEMENTS.items():
        expected = "B13" if name == "Q14_location_track" else name.split("_")[0]
        assert s.code == expected, name


def test_q_label():
    for s in STATEMENTS.values():
        assert re.fullmatch(r"Q\d+|SYS", s.q), s.name
        if s.table.startswith("system"):
            assert s.q == "SYS" and s.code == "SYS"


def test_pk_indexes_within_param_count():
    for s in STATEMENTS.values():
        n = s.cql.count("?")
        for col, idx in s.pk:
            assert 0 <= idx < n, (s.name, col, idx, n)


def test_pk_columns_are_partition_keys_and_complete():
    for s in STATEMENTS.values():
        if s.table in SYSTEM_TABLES or s.kind == "scan":
            assert s.pk == (), s.name
            continue
        cols = tuple(c for c, _ in s.pk)
        # IN ? hoặc = ?: phải đủ mọi cột khóa partition, theo đúng thứ tự trong khóa
        assert set(cols) == set(SCHEMA_PARTITION_KEYS[s.table]), (s.name, cols)


def test_pk_positions_known_examples():
    assert STATEMENTS["B01_account_get"].pk == (("username", 0),)
    assert STATEMENTS["T02_login_touch"].pk == (("username", 1),)
    assert STATEMENTS["T09_driver_rating"].pk == (("driver_id", 2),)  # USING TIMESTAMP ? đứng trước SET
    assert STATEMENTS["T07_promo_use"].pk == (("promo_code", 1),)
    assert STATEMENTS["T05_ride_accept"].pk == (("ride_id", 5),)
    assert STATEMENTS["T04_ride_insert"].pk == (("ride_id", 0),)
    assert STATEMENTS["B10_driver_month"].pk == (("driver_id", 0), ("yyyymm", 1))
    assert STATEMENTS["T05_rad_accept"].pk == (
        ("city", 1), ("district", 2), ("ride_date", 3))
    assert STATEMENTS["A06_area_multi"].pk == (("city", 0), ("district", 1))
    assert STATEMENTS["T08_payment_insert"].pk == (("city", 0), ("pay_date", 1))


def test_param_counts_of_key_statements():
    n = {k: STATEMENTS[k].cql.count("?") for k in STATEMENTS}
    assert n["B01_account_get"] == 1
    assert n["T01_account_insert"] == 6
    assert n["T04_ride_insert"] == 16
    assert n["T05_ride_accept"] == 6
    assert n["T06_ride_start"] == 4
    assert n["T08_ride_complete"] == 4
    assert n["T10_ride_cancel"] == 4
    assert n["T04_rad_insert"] == 12
    assert n["T08_payment_insert"] == 10
    assert n["SYS_local"] == 0 and n["SYS_columns"] == 1


def test_every_base_table_has_a_write_or_lwt():
    written = {s.table for s in STATEMENTS.values() if s.kind in ("write", "lwt")}
    assert set(BASE_TABLES) <= written


def test_mv_only_read():
    for s in STATEMENTS.values():
        if s.table == "vehicles_by_plate":
            assert s.kind == "read"


def test_select_columns_are_listed_and_ride_cols():
    assert "rated_at" in RIDE_COLS
    assert len(RIDE_COLS) == 25
    assert len(set(RIDE_COLS)) == 25
    sel = STATEMENTS["B06_ride_get"].cql
    assert sel == "SELECT " + ", ".join(RIDE_COLS) + " FROM rides WHERE ride_id = ?"


def test_unbounded_scans_have_no_where():
    for s in STATEMENTS.values():
        if s.kind == "scan":
            assert " WHERE " not in s.cql, s.name


def test_scan_only_for_app_lists():
    scans = {n for n, s in STATEMENTS.items() if s.kind == "scan"}
    assert scans == {n for n in STATEMENTS if n.endswith("_scan")}


def test_allow_filtering_only_inside_one_partition():
    for s in STATEMENTS.values():
        if "ALLOW FILTERING" in s.cql:
            assert s.pk, s.name  # luôn cố định partition


def test_tz_dependent_statements_use_expected_filters():
    assert "status = 'COMPLETED'" in STATEMENTS["A01_driver_income"].cql
    assert "status = 'REQUESTED'" in STATEMENTS["APP15_area_waiting"].cql
    assert "IF status = 'REQUESTED'" in STATEMENTS["T05_ride_accept"].cql
    assert "IF status = 'ACCEPTED' AND driver_id = ?" in STATEMENTS["T06_ride_start"].cql
    assert "IF status = 'ONGOING' AND driver_id = ?" in STATEMENTS["T08_ride_complete"].cql
    assert "IF status = ?" in STATEMENTS["T10_ride_cancel"].cql


# ---- Đối chiếu tên cột với 01_schema.cql (không cần Cassandra) ----
def _schema_columns() -> dict[str, set[str]]:
    from config import CASSANDRA_DIR

    text = (CASSANDRA_DIR / "01_schema.cql").read_text(encoding="utf-8")
    text = re.sub(r"--[^\n]*", "", text)
    cols: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\)", text, re.S):
        names = set()
        for line in m.group(2).split("\n"):
            line = line.strip()
            if not line or line.startswith("PRIMARY KEY"):
                continue
            names.add(line.split()[0])
        cols[m.group(1)] = names
    mv = re.search(r"CREATE MATERIALIZED VIEW IF NOT EXISTS (\w+) AS\s+SELECT (.*?)\s+FROM", text, re.S)
    cols[mv.group(1)] = {c.strip() for c in mv.group(2).split(",")}
    cols["rides"].add("rated_at")  # 06_app_migration.cql
    return cols


SCHEMA = _schema_columns()
_KEYWORDS = {"true", "false", "null"}


def _referenced_columns(cql: str) -> set[str]:
    refs: set[str] = set()
    m = re.match(r"^INSERT INTO \w+ \(([^)]*)\)", cql)
    if m:
        refs |= {c.strip() for c in m.group(1).split(",")}
    m = re.match(r"^SELECT (.*?) FROM ", cql)
    if m:
        for item in m.group(1).split(", "):
            item = re.sub(r" AS \w+$", "", item.strip())
            inner = re.match(r"^\w+\((.*)\)$", item)
            item = inner.group(1) if inner else item
            if item != "*":
                refs.add(item)
    m = re.search(r" SET (.*?)(?: WHERE | IF |$)", cql)
    if m and cql.startswith("UPDATE"):
        for part in re.split(r", (?=\w+ = )", m.group(1)):
            refs.add(part.split(" = ")[0].strip())
    for cond in re.findall(r"(?:WHERE|AND|IF) (\w+) (?:=|IN|>=|<=) ", cql):
        refs.add(cond)
    return refs - _KEYWORDS


def test_schema_parser_sanity():
    assert len(SCHEMA) == 14
    assert "status_history" in SCHEMA["rides"] and "tags" in SCHEMA["ratings_by_driver"]
    assert SCHEMA["vehicles_by_plate"] == {"license_plate", "vehicle_id", "driver_id", "model", "color"}


def test_all_referenced_columns_exist_in_schema():
    for s in STATEMENTS.values():
        if s.table in SYSTEM_TABLES:
            continue
        refs = _referenced_columns(s.cql)
        assert refs, s.name
        unknown = refs - SCHEMA[s.table]
        assert not unknown, (s.name, sorted(unknown))
        # FROM/INTO/UPDATE đúng bảng khai báo
        assert re.search(rf"(?:FROM|INTO|UPDATE) {s.table}\b", s.cql), s.name


def test_referenced_columns_detects_typos():
    assert _referenced_columns("SELECT a, b FROM t WHERE c = ? AND d IN ?") == {"a", "b", "c", "d"}
    assert _referenced_columns("UPDATE t SET x = ?, y = y + ? WHERE k = ? IF z = null") == {"x", "y", "k", "z"}
