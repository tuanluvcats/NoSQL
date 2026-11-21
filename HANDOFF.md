# HANDOFF: ứng dụng minh họa đặt xe công nghệ (Cassandra 3.11)

Cập nhật: 2026-11-21. Nhánh `feat/ride-booking-app`. Người đọc: bất kỳ ai tiếp quản (thành viên nhóm, hoặc phiên làm việc sau).

Thiết kế: `docs/superpowers/specs/2026-11-21-ride-booking-app-design.md`. Kế hoạch (Task 0 đến 13): `docs/superpowers/plans/2026-11-21-ride-booking-app.md`.
Mã nguồn: `DoAn/app/`. Cách chạy, tài khoản thử, đối chiếu barem, giới hạn đã biết: `DoAn/app/README.md`. Kịch bản demo: `DoAn/app/docs/kich_ban_demo.md`.

## 1. Đã xong

Toàn bộ Task 0 đến 14 của kế hoạch đã làm xong và commit (Task 14 là vòng chỉnh cuối, xem dòng cuối bảng).

| Task | Nội dung | Commit |
|---|---|---|
| (thiết kế) | Spec và kế hoạch | `6bc6c26` |
| 0 | Scaffold, cấu hình, guard `_test`, loader CQL, seed, `06_app_migration.cql`, fixture integration, `setup_db`, `check_env` | `9abcb23` |
| 2 | Domain thuần: tiền, múi giờ +07, mã chuyến, máy trạng thái, mật khẩu, khuyến mãi | `8caaa0b` |
| 3 | Catalog prepared statement B/A/T/Q, `CassandraDb`, trace, khung app và panel "CQL đã chạy" | `c5cc4af` |
| (sửa) | CLI in được tiếng Việt trên console cp1252 | `bf62000` |
| 1 | Thăm dò hành vi Cassandra 3.11 (probe) | `ed96f25` |
| 4 | Đăng nhập, đăng ký, phân quyền, khóa/mở tài khoản (9.1) | `79c7db9` |
| 5 | CRUD khách, tài xế, xe (+MV), khuyến mãi (+set `cities`) (9.2) | `a40a1cc` |
| 6 | Đặt xe, giữ/trả lượt khuyến mãi | `8a62ef7` |
| 7 | Tài xế bật/tắt nhận chuyến, chuyến chờ, nhận chuyến LWT hai tầng | `b7198fd` |
| 8 | Bắt đầu, hoàn thành + thanh toán, hủy | `75d03c8` |
| 9 | Đánh giá (LWT `rated_at`), backfill, kiểm tra nhất quán + reconcile | `7bb7ff2` |
| (test) | Tăng tốc fixture integration | `5b04d08` |
| 10 | Lịch sử, chi tiết + `status_history`, thu nhập tháng, báo cáo, GPS, CSV (9.3, 9.4) | `09f2220` |
| 11 | Backup/restore JSON logical, chế độ bảo trì (9.2) | `13e9e01` |
| (sửa) | Trang lỗi 404/403/500 đúng người dùng đã đăng nhập, không lộ lỗi DB khi tra cứu người dùng | `e5b230f` |
| 12 | Trang Kết nối (mục 8), trang NoSQL minh họa, kịch bản T01 đến T12 end-to-end | `9989227` |
| 13 | README, kịch bản demo, HANDOFF, `tests/unit/test_docs.py` | `245fdbf` |
| 14 | Vòng chỉnh cuối: trang chủ theo keyspace thật và vai trò, trang 500 ẩn lỗi (log + `APP_DEBUG=1`), menu trang 503 đúng người dùng, `tools.check_env --help` | `b78ecd0` |
| 15 | Đánh giá đồng thời: `UPDATE ... USING TIMESTAMP ?` cho `drivers.rating` và `drivers_by_area.rating` (lần đọc AVG sau thắng) | `26c6888` |
| 16 | Rà UX: menu gom nhóm theo mục 9.1-9.4 và tô trang đang mở, trang chủ không lặp nút của menu, nhãn tài xế "Trạng thái"/"Chuyến chờ", xác nhận khi xóa/khóa, tài xế BUSY có link tới chuyến đang chạy; `tests/unit/test_ux_rules.py` | `a17eee9` |
| 17 | `app/docs/hoi_dap_bao_ve.md`: hỏi đáp khi bảo vệ (Jinja2, FastAPI, LWT, phi chuẩn hóa, last-write-wins) kèm nguồn tham khảo | commit docs kế tiếp |

Kết quả test ở HEAD `9989227` (trước Task 13): 545 test xanh trên Cassandra 3.11.4 (cài trực tiếp, Windows 11, Python 3.12.7), cả chế độ reset thường và đầy đủ.
Task 13 thêm `tests/unit/test_docs.py` (13 test), tổng 558 test (325 unit, 233 integration). Task 14 thêm test cho trang chủ, trang 500/503, `APP_DEBUG` và `check_env`
(số test cuối xem dòng tóm tắt pytest khi chạy lại). Sau Task 16: 611 test xanh (chạy đủ unit và integration, 2026-11-22).

## 2. Đang dở

Không có task nào dở dang. Chỉ còn các việc mở ở mục 4.

## 3. Kết quả probe (`capabilities`)

`DoAn/app/db/capabilities.py`, ghi bởi `tests/integration/test_cassandra_probe.py`, `PROBED_ON = "3.11.4 cài trực tiếp Windows, 2026-11-21"`:

| Hằng số | Giá trị | Hệ quả |
|---|---|---|
| `TRUNCATE_CLEARS_MV` | `True` | `TRUNCATE` bảng gốc `vehicles` làm rỗng cả MV `vehicles_by_plate`. Restore chỉ ghi lại `vehicles` (nhánh A), không ghi trực tiếp vào MV. Nhánh B (DROP/CREATE MV) chưa cài và chỉ cần nếu một phiên bản Cassandra khác cho giá trị `False` |
| `LWT_IF_IN_SUPPORTED` | `True` | `IF status IN (...)` chạy được trên 3.11.4. Ứng dụng vẫn dùng `IF status = <đã đọc>` (quyết định D3) |
| `LWT_ON_MV_BASE_OK` | `True` | LWT trên bảng gốc có MV chạy được, MV cập nhật đúng |
| `JSON_ROUNDTRIP_OK` | `True` | `SELECT JSON` rồi `INSERT ... JSON` khôi phục đúng mọi cột; nền tảng của backup/restore |

Hai điểm "chưa chắc" của spec (TRUNCATE và MV; `IF col IN`) đã có câu trả lời trên 3.11.4. Chưa chạy lại probe trên Cassandra 3.11.19 (Docker) hay trên máy từng thành viên.

## 4. Còn lại, việc còn mở

1. **Kiểm 3.11.4 trên máy từng thành viên (chưa kiểm).** Ứng dụng mới chạy thật trên một máy (3.11.4 cài trực tiếp). Mỗi người cần làm theo README: `python -m tools.check_env`, dựng keyspace riêng, chạy test, và có thể chạy lại probe
   (`.venv\Scripts\python -m pytest tests/integration/test_cassandra_probe.py -q`). Docker 3.11.19 cũng chưa chạy lại với ứng dụng.
2. **Các file của người dùng còn thay đổi, chưa commit (không thuộc commit ứng dụng, cố ý để người dùng tự commit):**
   - `DoAn/cassandra/02_data.cql`: đã dọn đuôi thử nghiệm (còn 321 dòng, chỉ phần seed; trước đó đoạn đuôi chạy T01/T05/T07/T08 dở, có `DELETE RIDE_1001` và `TRUNCATE payments_by_city_date`). Bộ nạp seed của ứng dụng vẫn tự cắt ở hết khối `driver_locations`.
   - `DoAn/CASSANDRA.MD`: đã sửa **§11** (Kết nối từ ứng dụng) cho khớp ứng dụng thật: đường dẫn `DoAn/app`, `tools.setup_db`, `tools.check_env`, backup bằng JSON qua driver, bỏ gợi ý `docker exec ... backup_snapshot.sh` làm cách chính. File này vẫn còn các thay đổi chưa commit khác của người dùng; chỉ §11 do Task 13 sửa.
   - Cùng khoảng 33 thay đổi chưa commit khác không liên quan (báo cáo Word, bài tập các chương, `DoAn/DoAn.dbs`, ...) vẫn nguyên. Mọi `git add` của ứng dụng đều chỉ thêm đúng file của task.
3. **Hoãn có chủ đích:** gộp `rated_at` thẳng vào `01_schema.cql` (và sửa T05 trong `05_transactions.cql`). Hiện vẫn giữ `06_app_migration.cql` riêng để hình trong Word của cả nhóm không lệch. Hệ quả: sau khi chạy migration, DbSchema/`DESCRIBE` của keyspace đó có thêm cột `rated_at`, nên chạy ứng dụng trên keyspace riêng (ví dụ `ride_booking_demo`).
4. **Keyspace `ride_booking` thật của người dùng chưa được đụng tới và chưa kiểm sức khỏe.** Đoạn đuôi thử nghiệm cũ của `02_data.cql` có thể đã làm hỏng dữ liệu (RIDE_1001 bị xóa, `payments_by_city_date` bị truncate) nếu từng chạy cả file. Cách kiểm: trang `/admin/consistency` và bảng "Số dòng hiện tại" ở `/admin/backup`, hoặc chạy `setup_db` lên keyspace riêng.
5. **Snapshot do `TRUNCATE`/`DROP` của test** tốn đĩa: dọn bằng `nodetool clearsnapshot -- ride_booking_test` (lệnh chuẩn, xem README; chưa chạy trên máy từng thành viên).
6. Báo cáo Word chưa được cập nhật phần ứng dụng; nằm ngoài phạm vi các task.

## 5. Lỗi đã biết và giới hạn

Danh sách đầy đủ, có giải thích, ở mục "Giới hạn đã biết" của `DoAn/app/README.md`. Tóm tắt:

- Ghi nhiều bảng không nguyên tử (kết quả `partial`, có Reconcile); Reconcile không ghi lại `ratings_by_driver`/điểm tài xế.
- Tài xế có thể kẹt BUSY nếu LWT nhận chuyến gặp `WriteTimeout` (có công cụ giải phóng ở `/admin/consistency`, còn một cửa sổ chạy đua hẹp).
- Hai admin khóa chéo nhau cùng lúc có thể qua phép kiểm "admin cuối".
- Biển số duy nhất chỉ kiểm bằng đọc MV (không có unique thật).
- Đổi tên khách/tài xế không cập nhật tên phi chuẩn hóa trong bảng chuyến cũ.
- Đánh giá: lỗi ghi sau LWT `rated_at` có thể mất dòng đánh giá; chưa có công cụ chèn lại.
- Quét toàn bảng ở trang admin và trang Nhất quán; `first_month` cố định 202609 cho phép kiểm "đã có chuyến".
- Cờ bảo trì nằm trong bộ nhớ một tiến trình; request chạy dở trước `begin()` có thể ghi chen.
- File backup chứa `password_hash`, không phải ảnh chụp nhất quán giữa các bảng; restore không rollback tự động (có file `*_prerestore.json`).
- Không có CSRF token (cookie `SameSite=lax`); khóa phiên mặc định `dev-secret-change-me` nếu không đặt `APP_SECRET_KEY`.
- Mã khuyến mãi seed hết hạn 2026-12-31; mật khẩu seed là SHA-256 không salt của `123456` (chỉ demo), tài khoản mới dùng PBKDF2.
- Trong demo, thao tác nhận chuyến lần hai bằng tay bị chặn ở bước kiểm trạng thái trước khi tới LWT, nên không hiện `[applied] False` của T05; nhánh đó được chứng minh bằng
  `tests/integration/test_accept.py::test_two_drivers_race_exactly_one_wins`. Dòng `[applied] False` hiện được ngay trong demo ở đăng ký trùng tên (T01).

## 6. Lệnh chạy lại

Mọi lệnh chạy ở `D:\Documents\Homework\NoSQL\DoAn\app` (PowerShell). Chi tiết trong `DoAn/app/README.md`.

```powershell
cd D:\Documents\Homework\NoSQL\DoAn\app
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

.venv\Scripts\python -m tools.check_env                                              # kiểm máy
.venv\Scripts\python -m tools.setup_db --keyspace ride_booking_demo --seed --yes     # dựng CSDL demo (TRUNCATE 13 bảng của keyspace đó)
.venv\Scripts\python -m tools.migrate --keyspace ride_booking                        # chỉ khi CSDL đã dựng từ Word: thêm rated_at, không xóa dữ liệu

$env:CASSANDRA_KEYSPACE = "ride_booking_demo"
.venv\Scripts\python -m uvicorn main:app --port 8000                                 # mở http://127.0.0.1:8000

.venv\Scripts\python -m pytest tests -q -p no:cacheprovider                          # toàn bộ (khoảng 3 phút khi có Cassandra)
.venv\Scripts\python -m pytest -m auth -q                                            # tương tự: crud, business, backup, nosql
```

Tài khoản thử (mật khẩu `123456`): `admin`, `dieuphoi`, `cust001` đến `cust010`, `drv551` đến `drv560`. Không có mật khẩu thật nào trong repo.

## 7. Danh sách commit của nhánh (cũ đến mới, so với `main`)

```text
6bc6c26 docs: thiết kế và kế hoạch triển khai ứng dụng minh họa đặt xe (Cassandra)
9abcb23 feat(app): scaffold cấu hình, guard keyspace _test, seed loader, setup_db, check_env và 06_app_migration
8caaa0b feat(app): domain thuần (tiền, múi giờ +07, mã chuyến, máy trạng thái, mật khẩu, khuyến mãi)
c5cc4af feat(app): catalog prepared statement B/A/T/Q, CassandraDb, trace và panel CQL đã chạy
bf62000 fix(app): CLI in được tiếng Việt trên console cp1252
ed96f25 test(app): probe hành vi Cassandra 3.11 (TRUNCATE MV, IF IN, LWT+MV, JSON)
79c7db9 feat(app): đăng nhập/đăng ký LWT, phân quyền, khóa tài khoản kiểm mỗi request
a40a1cc feat(app): CRUD khách, tài xế, xe (tra MV), khuyến mãi (set cities) chống upsert
8a62ef7 feat(app): đặt xe IF NOT EXISTS, giữ lượt khuyến mãi bằng LWT optimistic
b7198fd feat(app): tài xế online/offline một khu vực, nhận chuyến LWT hai tầng có bồi hoàn
75d03c8 feat(app): bắt đầu/hoàn thành/hủy chuyến bằng LWT IF status, thanh toán và trả lượt mã
7bb7ff2 feat(app): đánh giá một lần bằng LWT rated_at, backfill, kiểm tra nhất quán và reconcile
5b04d08 test(app): tăng tốc fixture integration (reset chỉ các bảng bẩn, TRUNCATE song song, rated_at nạp sẵn, raw_readonly)
09f2220 feat(app): lịch sử, thu nhập tháng, doanh thu ngày/7 ngày, thống kê khu vực, GPS, xuất CSV
13e9e01 feat(app): backup/restore JSON logical, kiểm file trước TRUNCATE, chế độ bảo trì
e5b230f fix(app): trang lỗi 404/403/500 hiển thị đúng người dùng đã đăng nhập, không lộ lỗi DB khi tra cứu người dùng
9989227 feat(app): trang Kết nối, trang NoSQL minh họa và kịch bản T01–T12 end-to-end
245fdbf docs(app): README, kịch bản demo, HANDOFF
b78ecd0 fix(app): vòng chỉnh cuối (trang chủ theo vai trò, trang 500 ẩn lỗi, menu 503, check_env --help)
26c6888 fix(app): cập nhật điểm tài xế bằng USING TIMESTAMP để hai lượt đánh giá đồng thời không ghi đè điểm cũ
a17eee9 fix(app): rà UX (menu gom nhóm, bỏ nút trùng, xác nhận xóa/khóa, link chuyến đang chạy cho tài xế)
```
