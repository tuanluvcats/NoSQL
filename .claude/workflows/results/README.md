# Kết quả workflow `verify-prompt1-analysis` — task 3 và 4

Ngày chạy: 04/10/2026. Workflow gốc: [`../verify-prompt1-analysis.js`](../verify-prompt1-analysis.js).

## Tiến độ

| # | Checker (prefix) | Trạng thái | Kết quả |
|---|---|---|---|
| 1 | draft-text (T) | Chưa chạy | — |
| 2 | draft-screenshots (S) | Chưa chạy | — |
| 3 | cassandra-41 (C) | **Xong** | [`task3_cassandra-41.json`](task3_cassandra-41.json): 15 finding, 20 fact |
| 4 | python-driver (P) | **Xong** | [`task4_python-driver.json`](task4_python-driver.json): 5 finding, 9 fact |
| 5 | dbschema (D) | Chưa chạy | — |
| 6 | rubric-consistency (R) | Chưa chạy | — |
| 7 | design-review (M) | Chờ task 2 | Phần đầu vào từ task 3 (`facts_for_prompt2`) đã có |
| — | Critic (K), Skeptic | Chờ đủ 7 checker | — |

Hai file JSON theo đúng `FINDINGS_SCHEMA` của workflow. Khi chạy tiếp, nạp `facts_for_prompt2` của task 3 vào `pDesign` (thay cho `cass.facts_for_prompt2`). Nạp `findings` của cả hai task vào danh sách `findings` trước bước Critic.

## Khác biệt so với môi trường trong workflow

- `prompt1_answer.md` và thư mục `nosql_extract` nằm trên máy Windows, không có trong repo. Vì vậy các nhận định được kiểm tra là phần trích dẫn trong file workflow. Finding ghi `[theo workflow]` là diễn giải lại phạm vi kiểm tra, không phải nguyên văn Prompt 1. Khi có `prompt1_answer.md`, cần đối chiếu lại câu chữ.
- Không chỉ đọc tài liệu: mọi hành vi đều được chạy thật trên Cassandra 4.1.12 (image `cassandra:4.1`, cấu hình giống `docker-compose.yml`), trong container cloud tách biệt, không đụng tới máy Windows.
- Phía Windows được tái hiện bằng Python 3.12.7 bản Windows chính thức (gói NuGet) chạy qua Wine, cài từ đúng các wheel `win_amd64 cp312` trên PyPI. Wine không phải Windows thật, nhưng kết luận chính đã được xác nhận độc lập bằng nội dung wheel, bảng import PE và mã nguồn driver. Nên chạy lại `evidence/p4_probe.py` một lần trên máy thật để xác nhận.
- `cassandra.apache.org` bị chặn từ môi trường này (403). Tài liệu 4.1 được đọc từ mã nguồn AsciiDoc trên GitHub `apache/cassandra`, nhánh `cassandra-4.1`. Trang web chính thức được build từ chính mã nguồn này.

## Kết luận quan trọng nhất

1. **P1 (high): "Python 3.12 cần cassandra-driver ≥ 3.29" sai một phần.** Trên Windows + Python 3.12, mọi bản từ 3.29.0 đến 3.30.1 đều báo lỗi `DependencyException: Unable to load a default connection class` ngay khi import. Nguyên nhân: Python 3.12 đã bỏ `asyncore`, còn wheel Windows không kèm `ev-4.dll`. Cách sửa đã kiểm chứng: `pip install "cassandra-driver==3.30.1" pyasyncore`. Stack FastAPI + Jinja2 + Bootstrap khi đó chạy được (P3).
2. **C11 (high): còn thiếu phần cấu hình cho mục "quản trị người dùng".** Cassandra mặc định dùng `AllowAllAuthenticator`, nên `CREATE ROLE ... WITH PASSWORD` và `GRANT` đều báo lỗi. Muốn bật phải mount một `cassandra.yaml` đặt `PasswordAuthenticator` và `CassandraAuthorizer`; image Docker không có biến môi trường nào cho việc này. Datacenter của cấu hình hiện tại là `datacenter1`. Biến `CASSANDRA_DC` chỉ có tác dụng khi dùng `GossipingPropertyFileSnitch`.
3. **Thiết kế bảng (C8, C9, C10, partly_wrong):**
   - Không nên lưu doanh thu (tiền) bằng counter: counter không idempotent, không có TTL, không BATCH chung được với bảng thường.
   - `driver_locations ((driver_id), ts DESC)` làm partition phình mãi. Nên chia bucket theo ngày, đặt `default_time_to_live` và dùng TWCS.
   - `drivers_by_area` có `status`/`rating` trong khóa chính, nên không UPDATE được; mỗi lần đổi phải DELETE + INSERT.
4. **Các nhận định đúng:** MV, UDF và SASI tắt mặc định; SAI chỉ có từ 5.0; LWT, static, GROUP BY chạy đúng như mô tả, kèm các ràng buộc ghi trong JSON. Từ 4.1 có thể `GROUP BY floor(ts, 1d)`. Backup bằng `nodetool snapshot` rồi khôi phục bằng `nodetool import` (`refresh` đã deprecated). `COPY` làm mất TTL. 3 node cần khoảng 4–6 GB RAM.

## Bằng chứng và cách tái lập (`evidence/`)

| File | Nội dung |
|---|---|
| `t3_version.out` | Phiên bản image, cqlsh, Java, datacenter |
| `t3_probe.cql` → `t3_probe.out` | Kiểm tra MV, SAI/SASI, UDF, GROUP BY, PER PARTITION LIMIT, token, ALLOW FILTERING, LWT, static, UDT, TTL, counter, TWCS, đổi khóa, role khi chưa bật auth |
| `t3_index_gcgrace.out` | SAI/SASI, secondary index, `gc_grace_seconds`, tùy chọn TWCS |
| `t3_backup_restore.sh` → `.out` | snapshot → TRUNCATE → `nodetool import` |
| `t3_copy_ttl.sh` → `.out`, `t3_copy_counter_help.out` | COPY làm mất TTL; COPY bảng counter; HELP COPY |
| `t3_auth.cql`, `t3_auth_check.sh` → `.out` | Bật PasswordAuthenticator + MV bằng yaml mount; role và quyền; `CASSANDRA_DC` |
| `t3_memory.out` | RAM mỗi node với heap 1G |
| `t3_describe_keyspace_probe.cql` | Kết quả `DESCRIBE KEYSPACE` |
| `p4_windows_py312.out` | Nội dung wheel Windows, DLL phụ thuộc, lỗi import, cách sửa bằng pyasyncore, app FastAPI |
| `p4_probe.py`, `p4_probe_asyncio.py`, `p4_probe_lbp.py` → `.out`, `p4_fastapi_app/` | Script thử driver Python |
| `p4_node_driver.out` | Driver Node.js 4.10.0 kết nối 4.1.12 |

Chạy lại các script `t3_*` trên máy có Docker như sau:

1. `docker compose up -d cassandra`
2. `docker cp t3_probe.cql nosql-cassandra:/tmp/`
3. `docker exec nosql-cassandra cqlsh -f /tmp/t3_probe.cql`

Các script `t3_probe.cql`, `t3_backup_restore.sh`, `t3_copy_ttl.sh` chỉ dùng keyspace thử nghiệm `probe`. Xoá sau khi thử bằng lệnh `DROP KEYSPACE probe;`.

Riêng `t3_auth.cql` tạo keyspace `ride_booking` và một materialized view. Script này đã chạy trên container thử nghiệm riêng `c41-auth`, nên **không chạy trên container `nosql-cassandra` thật**.
