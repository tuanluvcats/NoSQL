"""Đo hiệu năng và so sánh với cách làm "ngây thơ" (baseline) trên Cassandra thật.

Chạy trên keyspace riêng (tên phải kết thúc bằng `_test`), tạo lại schema + seed, rồi đo:
  1. Đọc theo partition key so với truy vấn thiếu partition key (ALLOW FILTERING).
  2. Ghi thường so với ghi có điều kiện (LWT).
  3. Tranh nhận chuyến: nhiều luồng cùng nhận một chuyến, cách "đọc rồi UPDATE" (baseline) so với LWT.
Kết quả in ra dạng Markdown (và ghi file nếu có --out).

    python -m tools.bench --keyspace ride_booking_bench_test --out docs/ket_qua_do_hieu_nang.md
"""
from __future__ import annotations

import argparse
import statistics
import threading
import time
from pathlib import Path

from config import Settings, assert_test_keyspace, ensure_utf8_stdout
from db.session import connect

SCHEMA = Path(__file__).resolve().parents[2] / "cassandra" / "01_schema.cql"


def summarize(samples_ms: list[float]) -> dict:
    """p50, p95, max (ms) của một dãy mẫu, làm tròn 2 chữ số."""
    if not samples_ms:
        raise ValueError("không có mẫu")
    s = sorted(samples_ms)
    p95 = s[min(len(s) - 1, max(0, round(0.95 * len(s)) - 1))]
    return {"n": len(s), "p50": round(statistics.median(s), 2), "p95": round(p95, 2), "max": round(s[-1], 2)}


def race_winners(attempts: list[bool]) -> int:
    """Số luồng tin rằng mình đã nhận được chuyến. Đúng phải luôn là 1."""
    return sum(1 for ok in attempts if ok)


def render_markdown(meta: dict, latency: dict[str, dict], race: dict[str, list[int]]) -> str:
    lines = ["# Kết quả đo hiệu năng và so sánh baseline", "",
             f"Môi trường: Cassandra {meta['version']}, một node, {meta['host']}; keyspace `{meta['keyspace']}` "
             f"(schema và dữ liệu mẫu giống `ride_booking`, {meta['rows']} chuyến). Thời điểm đo: {meta['when']}.", "",
             "## 1. Thời gian Cassandra xử lý (ms, lấy từ query trace phía server)", "",
             "| Thao tác | Số lần | p50 | p95 | max |", "|---|---:|---:|---:|---:|"]
    for name, r in latency.items():
        lines.append(f"| {name} | {r['n']} | {r['p50']} | {r['p95']} | {r['max']} |")
    lines += ["", "## 2. Tranh nhận cùng một chuyến", "",
              f"Mỗi vòng: tạo một chuyến REQUESTED, {meta['threads']} luồng (tài xế) cùng nhận. Đúng nghiệp vụ: mỗi vòng đúng 1 người thắng.", "",
              "| Cách làm | Số vòng | Vòng có đúng 1 người thắng | Vòng có từ 2 người thắng trở lên | Số người thắng nhiều nhất trong một vòng |",
              "|---|---:|---:|---:|---:|"]
    for name, winners in race.items():
        ok = sum(1 for w in winners if w == 1)
        bad = sum(1 for w in winners if w > 1)
        lines.append(f"| {name} | {len(winners)} | {ok} | {bad} | {max(winners)} |")
    lines += ["", "Ghi chú: một node nên không có độ trễ giữa các bản sao; trên cụm nhiều node, LWT (Paxos, 4 vòng mạng) còn chậm hơn ghi "
              "thường rõ hơn. Đọc theo partition key gần như không đổi khi bảng lớn lên, còn ALLOW FILTERING phải quét cả bảng nên chậm "
              "dần theo số dòng. Các chuyến giả (mã BENCH_F...) chỉ nằm trong keyspace đo, không đụng `ride_booking`.", ""]
    return "\n".join(lines)


def _timed(fn, n: int) -> list[float]:
    """Thời gian Cassandra xử lý (ms) lấy từ query trace phía server. Không đo bằng đồng hồ phía client vì trên Windows
    vòng sự kiện của driver làm tròn mọi lệnh về khoảng 15,6 ms."""
    out = []
    for i in range(n):
        rs = fn(i)
        out.append(rs.get_query_trace(max_wait_sec=10).duration.total_seconds() * 1000)
    return out


def _race(session, mode: str, rounds: int, threads: int) -> list[int]:
    ins = session.prepare("INSERT INTO rides (ride_id, status) VALUES (?, 'REQUESTED')")
    read = session.prepare("SELECT status FROM rides WHERE ride_id = ?")
    naive = session.prepare("UPDATE rides SET status = 'ACCEPTED', driver_id = ? WHERE ride_id = ?")
    lwt = session.prepare("UPDATE rides SET status = 'ACCEPTED', driver_id = ? WHERE ride_id = ? IF status = 'REQUESTED'")
    result = []
    for r in range(rounds):
        rid = f"BENCH_RACE_{mode}_{r}"
        session.execute(ins, [rid])
        barrier = threading.Barrier(threads)
        attempts = [False] * threads

        def worker(k):
            barrier.wait()
            if mode == "lwt":
                attempts[k] = bool(session.execute(lwt, [f"DRV_B{k}", rid]).one()["[applied]"])
            else:
                row = session.execute(read, [rid]).one()
                if row and row["status"] == "REQUESTED":
                    session.execute(naive, [f"DRV_B{k}", rid])
                    attempts[k] = True

        ts = [threading.Thread(target=worker, args=(k,)) for k in range(threads)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        result.append(race_winners(attempts))
        session.execute("DELETE FROM rides WHERE ride_id = %s", [rid])
    return result


def run(settings: Settings, keyspace: str, n: int, rounds: int, threads: int, extra: int = 0) -> str:
    assert_test_keyspace(keyspace)
    from tools.setup_db import setup_db

    cluster, session = connect(settings, keyspace=None)
    try:
        setup_db(session, keyspace, seed=True, schema_path=SCHEMA)
        session.set_keyspace(keyspace)
        version = session.execute("SELECT release_version FROM system.local").one()["release_version"]
        ids = [r["ride_id"] for r in session.execute("SELECT ride_id FROM rides")]
        session.execute("INSERT INTO rides (ride_id, status) VALUES ('BENCH_W', 'REQUESTED')")

        by_pk = session.prepare("SELECT ride_id, status, fare FROM rides WHERE ride_id = ?")
        scan = session.prepare("SELECT ride_id, fare FROM rides WHERE status = 'COMPLETED' ALLOW FILTERING")
        w_plain = session.prepare("UPDATE rides SET cancel_reason = ? WHERE ride_id = 'BENCH_W'")
        w_lwt = session.prepare("UPDATE rides SET cancel_reason = ? WHERE ride_id = 'BENCH_W' IF status = 'REQUESTED'")
        for _ in range(20):  # làm nóng kết nối và cache
            session.execute(by_pk, [ids[0]])

        def ex(stmt, params=None):
            return lambda i: session.execute(stmt, params(i) if params else None, trace=True)

        def reads(label):
            return {
                f"Đọc theo partition key, {label}": summarize(_timed(ex(by_pk, lambda i: [ids[i % len(ids)]]), n)),
                f"Thiếu partition key (`ALLOW FILTERING`), {label}": summarize(_timed(ex(scan), max(10, n // 10))),
            }

        latency = reads(f"{len(ids)} chuyến")
        latency["Ghi thường (`UPDATE`)"] = summarize(_timed(ex(w_plain, lambda i: [f"b{i}"]), n))
        latency["Ghi có điều kiện (LWT `IF status = ...`)"] = summarize(_timed(ex(w_lwt, lambda i: [f"l{i}"]), n))
        if extra:
            from cassandra.concurrent import execute_concurrent_with_args
            filler = session.prepare("INSERT INTO rides (ride_id, status, fare) VALUES (?, ?, 50000)")
            execute_concurrent_with_args(session, filler, [(f"BENCH_F{k}", "COMPLETED" if k % 2 else "CANCELLED")
                                                          for k in range(extra)], concurrency=64)
            latency.update(reads(f"{len(ids) + extra} chuyến"))
        session.execute("DELETE FROM rides WHERE ride_id = 'BENCH_W'")
        race = {"Baseline: đọc trạng thái rồi UPDATE thường": _race(session, "naive", rounds, threads),
                "Ứng dụng: LWT `IF status = 'REQUESTED'`": _race(session, "lwt", rounds, threads)}
        meta = {"version": version, "host": ",".join(settings.hosts),
                "keyspace": keyspace, "rows": len(ids), "threads": threads,
                "when": time.strftime("%Y-%m-%d %H:%M")}
        return render_markdown(meta, latency, race)
    finally:
        cluster.shutdown()


def main(argv=None) -> int:
    ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Đo độ trễ và so sánh baseline trên keyspace *_test")
    ap.add_argument("--keyspace", default="ride_booking_bench_test")
    ap.add_argument("--n", type=int, default=200, help="số lần đo mỗi thao tác")
    ap.add_argument("--rounds", type=int, default=30, help="số vòng tranh nhận chuyến")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--extra", type=int, default=20000, help="số chuyến giả thêm vào để thấy ALLOW FILTERING chậm dần")
    ap.add_argument("--out", help="ghi kết quả Markdown ra file")
    a = ap.parse_args(argv)
    text = run(Settings.from_env(), a.keyspace, a.n, a.rounds, a.threads, a.extra)
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
