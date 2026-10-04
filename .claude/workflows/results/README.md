# Kết quả workflow `verify-prompt1-analysis` — task 3 và 4

Ngày chạy: 04/10/2026. Workflow: [`../verify-prompt1-analysis.js`](../verify-prompt1-analysis.js).

Task 3 (`cassandra-41`) và task 4 (`python-driver`) đã chạy xong trên cloud. Workflow đã được sửa để máy local **không chạy lại hai task này**. Local chỉ làm nốt hai việc cần đến máy Windows (xem mục dưới).

## Tiến độ

| # | Checker (prefix) | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | draft-text (T) | Chạy trên local | Không đổi |
| 2 | draft-screenshots (S) | Chạy trên local | Không đổi |
| 3 | cassandra-41 (C) | **Xong trên cloud** | [`task3_cassandra-41.json`](task3_cassandra-41.json): 15 finding, 21 fact. Local chỉ đối chiếu claim |
| 4 | python-driver (P) | **Xong trên cloud** | [`task4_python-driver.json`](task4_python-driver.json): 5 finding, 11 fact. Local đối chiếu claim và chạy thử trên Windows thật |
| 5 | dbschema (D) | Chạy trên local | Không đổi |
| 6 | rubric-consistency (R) | Chạy trên local | Không đổi |
| 7 | design-review (M) | Chạy trên local | Không còn chờ task 3: dùng thẳng fact của task 3 và các finding C8–C10 |
| — | Critic (K), Skeptic | Chạy trên local | Nhận finding của task 3, 4 như bình thường |

## Khi chạy lại workflow trên máy local

Kết quả task 3 và 4 được chép vào workflow thành hai hằng `PRE3` và `PRE4` (khối `PRECOMPUTED RESULTS`). Thay cho hai checker cũ, workflow chạy hai agent kiểm tra nhẹ.

**`cassandra-41-localcheck`** (khoảng 12 lượt gọi tool):
- Không nghiên cứu lại và không bật Docker.
- Mở `prompt1_answer.md`, thay mỗi claim bằng câu nguyên văn của Prompt 1. Các claim gắn `[theo workflow]` hiện chỉ là diễn giải.
- Nếu câu chữ thật làm thay đổi đánh giá thì sửa verdict, và ghi lý do vào evidence với tiền tố `LOCAL CHECK:`.
- Bổ sung finding cho nhận định Cassandra nào của Prompt 1 mà C1–C15 chưa bao phủ.

**`python-driver-localcheck`** (khoảng 15 lượt gọi tool):
- Làm bước đối chiếu claim như trên.
- Tạo venv tạm ở `nosql_extract/venv_probe` bằng Python 3.12.7 của máy, rồi chạy `evidence/p4_probe.py` hai lần: trước và sau khi cài `pyasyncore`. Thêm một dòng kiểm tra `fastapi`/`uvicorn`/`jinja2`.
- Kết quả ghi vào evidence của P1/P3 với tiền tố `REAL WINDOWS:`. Xong thì xoá venv.

Nếu một agent kiểm tra không trả về kết quả hoặc bị lỗi, workflow dùng nguyên kết quả có sẵn và ghi log. Các bước sau vẫn chạy.

Trước khi chạy workflow thật, có thể tự kiểm tra offline (không gọi agent, không cần mạng):

```bash
node .claude/workflows/results/check_workflow.mjs
```

Script chạy workflow với `agent()` giả lập theo ba tình huống: agent trả `null`, agent trả kết quả, agent bị lỗi. Script kiểm tra:
- workflow phân tích cú pháp được;
- kết quả task 3, 4 trong workflow khớp với hai file JSON;
- design-review không phải chờ task 3.

Nếu sửa `task3_cassandra-41.json` hoặc `task4_python-driver.json`, chạy `python .claude/workflows/results/sync_precomputed.py` để chép lại vào workflow. `check_workflow.mjs` sẽ báo lỗi nếu quên bước này.

## Khác biệt so với môi trường trong workflow

- `prompt1_answer.md` và thư mục `nosql_extract` chỉ có trên máy Windows. Claim được lấy từ phần trích dẫn trong workflow; bước đối chiếu nguyên văn để lại cho local (xem trên).
- Mọi hành vi đều được chạy thật trên Cassandra 4.1.12 (image `cassandra:4.1`, cấu hình giống `docker-compose.yml`), trong container cloud tách biệt.
- Phía Windows được tái hiện bằng Python 3.12.7 bản Windows chính thức (gói NuGet) chạy qua Wine, cài từ đúng các wheel `win_amd64 cp312` trên PyPI.
  - Kết luận chính đã được xác nhận độc lập bằng nội dung wheel, bảng import PE và mã nguồn driver.
  - Lần chạy trên Windows thật do `python-driver-localcheck` đảm nhận.
- `cassandra.apache.org` bị chặn từ môi trường cloud (403). Tài liệu 4.1 được đọc từ mã nguồn AsciiDoc trên GitHub `apache/cassandra`, nhánh `cassandra-4.1`; trang web chính thức được build từ chính mã nguồn này.

## Kết luận quan trọng nhất

1. **P1 (high): "Python 3.12 cần cassandra-driver ≥ 3.29" sai một phần.**
   - Trên Windows + Python 3.12, mọi bản từ 3.29.0 đến 3.30.1 đều báo lỗi `DependencyException: Unable to load a default connection class` ngay khi import.
   - Nguyên nhân: Python 3.12 đã bỏ `asyncore`, còn wheel Windows không kèm `ev-4.dll`. Trên Linux không có lỗi này, vì wheel có libev.
   - Cách sửa đã kiểm chứng: `pip install "cassandra-driver==3.30.1" pyasyncore`. Khi đó stack FastAPI + Jinja2 + Bootstrap chạy được (P3).
2. **C11 (high): còn thiếu phần cấu hình cho mục "quản trị người dùng".**
   - Cassandra mặc định dùng `AllowAllAuthenticator`, nên `CREATE ROLE ... WITH PASSWORD` và `GRANT` đều báo lỗi.
   - Muốn bật phải mount một `cassandra.yaml` đặt `PasswordAuthenticator` và `CassandraAuthorizer`; image không có biến môi trường cho việc này.
   - Datacenter của cấu hình hiện tại là `datacenter1`. `CASSANDRA_DC` chỉ có tác dụng khi dùng `GossipingPropertyFileSnitch`.
3. **Thiết kế bảng (C8, C9, C10, partly_wrong):**
   - Không nên lưu doanh thu (tiền) bằng counter: counter không idempotent, không có TTL, không BATCH chung được với bảng thường.
   - `driver_locations ((driver_id), ts DESC)` làm partition phình mãi. Nên chia bucket theo ngày, đặt `default_time_to_live` và dùng TWCS.
   - `drivers_by_area` có `status`/`rating` trong khóa chính, nên không UPDATE được; mỗi lần đổi phải DELETE + INSERT.
4. **Backup/Restore (C12): cả 4 cách khôi phục đều chạy được trên 4.1.12.**
   - `nodetool snapshot` → `nodetool import` (khuyến nghị).
   - Incremental backup (`nodetool enablebackup`) → `nodetool import`.
   - `nodetool refresh`: vẫn chạy nhưng in cảnh báo deprecated.
   - `sstableloader`.
   - Dọn snapshot bằng `nodetool clearsnapshot`. Lệnh `COPY` làm mất TTL (C13).
5. **Các nhận định đúng:**
   - MV, UDF và SASI tắt mặc định; SAI chỉ có từ 5.0.
   - LWT, static, GROUP BY chạy đúng như mô tả, kèm các ràng buộc ghi trong JSON. Từ 4.1 có thể `GROUP BY floor(ts, 1d)`.
   - 3 node cần khoảng 4–6 GB RAM.

## Bằng chứng và cách tái lập (`evidence/`)

| File | Nội dung |
|---|---|
| `t3_version.out` | Phiên bản image, cqlsh, Java, datacenter |
| `t3_probe.cql` → `t3_probe.out` | Kiểm tra MV, SAI/SASI, UDF, GROUP BY, PER PARTITION LIMIT, token, ALLOW FILTERING, LWT, static, UDT, TTL, counter, TWCS, đổi khóa, role khi chưa bật auth |
| `t3_index_gcgrace.out` | SAI/SASI, secondary index, `gc_grace_seconds`, tùy chọn TWCS |
| `t3_backup_restore.sh` → `.out` | snapshot → TRUNCATE → `nodetool import`; COPY làm mất TTL |
| `t3_backup_restore2.sh` → `.out` | Incremental backup → import, `nodetool refresh`, `sstableloader`, `clearsnapshot` |
| `t3_copy_ttl.sh` → `.out`, `t3_copy_counter_help.out` | COPY làm mất TTL; COPY bảng counter; HELP COPY |
| `t3_auth.cql`, `t3_auth_check.sh` → `.out` | Bật PasswordAuthenticator + MV bằng yaml mount; role và quyền; `CASSANDRA_DC` |
| `t3_memory.out` | RAM mỗi node với heap 1G |
| `t3_describe_keyspace_probe.cql` | Kết quả `DESCRIBE KEYSPACE` |
| `p4_pypi.out` | Danh sách phiên bản PyPI, wheel cp312 từng bản |
| `p4_windows_py312.out` | Nội dung wheel Windows, DLL phụ thuộc, lỗi import, cách sửa bằng pyasyncore, app FastAPI |
| `p4_linux_py312.out` | Đối chứng Linux: driver tự dùng libev, không lỗi |
| `p4_probe.py`, `p4_probe_asyncio.py`, `p4_probe_lbp.py` → `.out`, `p4_fastapi_app/` | Script thử driver Python |
| `p4_node_driver.out` | Driver Node.js 4.10.0 kết nối 4.1.12 |

Chạy lại các script `t3_*` trên máy có Docker như sau:

1. `docker compose up -d cassandra`
2. `docker cp t3_probe.cql nosql-cassandra:/tmp/`
3. `docker exec nosql-cassandra cqlsh -f /tmp/t3_probe.cql`
4. `bash t3_backup_restore.sh`, `bash t3_backup_restore2.sh` (trong Git Bash, thêm `MSYS_NO_PATHCONV=1` trước lệnh)

Các script `t3_probe.cql`, `t3_backup_restore*.sh`, `t3_copy_ttl.sh` chỉ dùng keyspace thử nghiệm `probe`. Xoá sau khi thử bằng lệnh `DROP KEYSPACE probe;`.

Riêng `t3_auth.cql` tạo keyspace `ride_booking` và một materialized view. Script này đã chạy trên container thử nghiệm riêng `c41-auth`, nên **không chạy trên container `nosql-cassandra` thật**.
