import pytest

from db import trace
from db.repo import CassandraDb, LwtResult
from db.trace import TraceEntry, TraceStore, tables_written

pytestmark = pytest.mark.nosql


class _Prepared:
    def __init__(self, cql):
        self.cql = cql
        self.consistency_level = None


class FakeSession:
    def __init__(self, results=None):
        self.prepare_calls: list[str] = []
        self.execute_calls: list[tuple] = []
        self._results = list(results or [])

    def prepare(self, cql):
        self.prepare_calls.append(cql)
        return _Prepared(cql)

    def execute(self, stmt, params=(), **kwargs):
        self.execute_calls.append((stmt, tuple(params)))
        return self._results.pop(0) if self._results else []


@pytest.fixture(autouse=True)
def _fresh_trace():
    trace.start_request()
    yield
    trace.start_request()


def test_rows_records_trace_entry():
    s = FakeSession([[{"username": "cust001", "role": "CUSTOMER"}]])
    db = CassandraDb(s, "ride_booking_test")
    out = db.rows("B01_account_get", ["cust001"])
    assert out == [{"username": "cust001", "role": "CUSTOMER"}]
    (e,) = trace.current()
    assert e.code == "B01"
    assert e.name == "B01_account_get"
    assert e.q == "Q1"
    assert e.table == "user_accounts"
    assert e.partition_key == {"username": "cust001"}
    assert e.consistency == "LOCAL_QUORUM"
    assert e.kind == "read"
    assert e.row_count == 1
    assert e.params == ["cust001"]
    assert e.applied is None and e.error is None
    assert e.elapsed_ms >= 0
    assert "FROM user_accounts" in e.cql


def test_one_returns_none_when_empty():
    db = CassandraDb(FakeSession([[]]), "ks")
    assert db.one("B01_account_get", ["nobody"]) is None
    assert trace.current()[0].row_count == 0


def test_lwt_rejected_returns_current():
    s = FakeSession([[{"[applied]": False, "status": "ACCEPTED"}]])
    db = CassandraDb(s, "ks")
    params = ["DRV_1", "A", "51A", "2026-10-01", {}, "RIDE_X"]
    r = db.lwt("T05_ride_accept", params)
    assert r == LwtResult(False, {"status": "ACCEPTED"})
    (e,) = trace.current()
    assert e.applied is False
    assert e.current == {"status": "ACCEPTED"}
    assert e.kind == "lwt"
    assert e.partition_key == {"ride_id": "RIDE_X"}


def test_lwt_applied():
    s = FakeSession([[{"[applied]": True}]])
    r = CassandraDb(s, "ks").lwt("T02_account_lock", ["u"])
    assert r.applied is True and r.current is None
    assert trace.current()[0].applied is True


def test_exec_records_write():
    s = FakeSession([[]])
    CassandraDb(s, "ks").exec("T02_login_touch", ["2026-10-01", "cust001"])
    (e,) = trace.current()
    assert e.kind == "write" and e.table == "user_accounts"
    assert e.partition_key == {"username": "cust001"}


def test_prepare_is_cached_per_name():
    s = FakeSession()
    db = CassandraDb(s, "ks")
    db.rows("B01_account_get", ["a"])
    db.rows("B01_account_get", ["b"])
    assert len(s.prepare_calls) == 1
    assert len(s.execute_calls) == 2
    assert len(trace.current()) == 2


def test_unknown_statement_name_raises():
    with pytest.raises(KeyError):
        CassandraDb(FakeSession(), "ks").rows("NOPE", [])


def test_error_is_traced_and_reraised():
    class Boom(FakeSession):
        def execute(self, stmt, params=(), **kwargs):
            raise RuntimeError("boom")

    db = CassandraDb(Boom(), "ks")
    with pytest.raises(RuntimeError):
        db.rows("B01_account_get", ["a"])
    (e,) = trace.current()
    assert "boom" in e.error


def test_raw_records_code_and_table():
    s = FakeSession([[]])
    db = CassandraDb(s, "ks")
    db.raw("BK", "rides", "TRUNCATE rides", kind="write")
    (e,) = trace.current()
    assert (e.code, e.table, e.kind, e.cql) == ("BK", "rides", "write", "TRUNCATE rides")
    assert s.execute_calls[0][1] == ()


def test_raw_with_params_prepares_once_per_cql():
    s = FakeSession([[], []])
    db = CassandraDb(s, "ks")
    db.raw("BK", "rides", "INSERT INTO rides JSON ?", ['{"ride_id": "a"}'], kind="write")
    db.raw("BK", "rides", "INSERT INTO rides JSON ?", ['{"ride_id": "b"}'], kind="write")
    assert s.prepare_calls == ["INSERT INTO rides JSON ?"]


def _e(table, kind, applied=None, name="x"):
    return TraceEntry(name=name, code="X", q="Q0", table=table, cql="", params=[], partition_key={},
                      consistency="LOCAL_QUORUM", kind=kind, applied=applied, current=None,
                      row_count=0, elapsed_ms=0.0, error=None)


def test_tables_written_order_and_filtering():
    entries = [
        _e("rides", "lwt", True),
        _e("rides_by_customer", "write"),
        _e("drivers", "read"),
        _e("drivers", "lwt", False),
        _e("rides", "write"),
    ]
    assert tables_written(entries) == ["rides", "rides_by_customer"]


def test_start_request_resets_and_returns_list():
    trace.record(_e("rides", "write"))
    lst = trace.start_request()
    assert lst == [] and trace.current() == []
    trace.record(_e("rides", "write"))
    assert len(trace.current()) == 1


def test_trace_store_lru():
    st = TraceStore(maxlen=2)
    t1 = st.put([_e("a", "read")])
    t2 = st.put([_e("b", "read")])
    t3 = st.put([_e("c", "read")])
    assert st.get(t1) is None
    assert st.get(t2)[0].table == "b"
    assert st.get(t3)[0].table == "c"
    assert len({t1, t2, t3}) == 3
