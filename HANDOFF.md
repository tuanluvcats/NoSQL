# HANDOFF: đồ án NoSQL (DbSchema và Apache Cassandra)

Cập nhật: 2026-11-24. Nhánh chính: `main`.

Ghi chú bàn giao cho người tiếp tục dự án: trạng thái hiện tại, cách chạy, quy tắc làm việc và việc còn mở. Chỉ cần đọc file, chạy lệnh trong PowerShell, sửa file và dùng git.
Đọc hết mục 1 đến 4 trước khi sửa gì.

## 1. Dự án là gì

- Đề tài: thiết kế CSDL Cassandra cho hệ thống đặt xe công nghệ, mô hình hóa bằng DbSchema, kèm ứng dụng web.
- Barem chấm điểm: `DoAn/DANH SACH DE TAI CUOI KY VA THANG DIEM_NOSQL (14DH).pdf`. Yêu cầu chung: `DoAn/YEUCAUDOAN.txt`.
- Thiết kế CSDL, câu truy vấn, sao lưu và kết quả kiểm chứng: `DoAn/CASSANDRA.MD`.
- Script CQL theo thứ tự chạy: `DoAn/cassandra/01_schema.cql` (13 bảng và 1 materialized view), `02_data.cql` (dữ liệu mẫu), `03_queries_basic.cql`, `04_queries_advanced.cql`, `05_transactions.cql` (LWT), `06_app_migration.cql` (cột `rides.rated_at` cho ứng dụng), `99_reset_data.cql`.
- Báo cáo Word: `DoAn/Báo cáo NoSQL DbSchema và Apache Cassandra.docx` (bản nộp). Mục 3.7 mô tả ứng dụng; ảnh minh họa lấy từ `DoAn/app/docs/hinh_bao_cao/`.
- Ứng dụng web: `DoAn/app/` (FastAPI, Jinja2, Bootstrap 5, cassandra-driver 3.30). Hướng dẫn đầy đủ: `DoAn/app/README.md`.

## 2. Quy tắc bắt buộc

1. **Không ghi vào keyspace `ride_booking`.** Đó là dữ liệu dùng cho ảnh chụp và kết quả trong báo cáo. Ứng dụng chạy trên `ride_booking_demo`; test chỉ chạy trên keyspace có đuôi `_test` (code tự từ chối keyspace khác).
2. **Không xóa dữ liệu, không `git reset --hard`, không `push --force`** nếu chủ repo chưa đồng ý rõ ràng.
3. **Chỉ nói "xong" khi test đã chạy thật và pass.** Ghi lại dòng tóm tắt của pytest.
4. **Sửa file Word tại chỗ và giữ một bản sao lưu ngoài repo trước khi sửa.** Giữ nguyên style có sẵn của tài liệu.
5. **Văn phong báo cáo:** viết ở mức phương pháp, không đưa tên file, tên hàm, đường dẫn mã nguồn vào phần trình bày. Mọi con số phải đo thật; số liệu đo một lần thì ghi rõ là một lần.
6. **Giao diện cho người dùng cuối:** không hiện tên bảng, mã câu truy vấn, LWT, keyspace hay mã trạng thái tiếng Anh. Ghi chú kỹ thuật chỉ đặt trong khối `{% if tech %}...{% endif %}` với class `tech-note`. Mã trạng thái, vai trò, thanh toán, khu vực hiển thị qua filter nhãn tiếng Việt (`DoAn/app/domain/labels.py`).
7. **Commit:** mỗi bước một commit, message tiếng Việt có tiền tố `feat`/`fix`/`docs`/`test`/`chore`. Tác giả là chủ repo; không thêm dòng `Co-Authored-By`.

## 3. Môi trường

- Windows 11, PowerShell, Python 3.12.
- Cassandra 3.11.4 cài trực tiếp ở `C:\apache-cassandra-3.11.4`, khởi động bằng `khoi_dong_cassandra.bat` (chạy ẩn, mất 1 đến 2 phút). Kiểm cổng: `Test-NetConnection 127.0.0.1 -Port 9042`.
- Máy không cài Cassandra thì dùng Docker: `docker compose up -d cassandra-doan` ở gốc repo (Cassandra 3.11, cổng 9042).
- Console Windows dùng cp1252: script Python in tiếng Việt thì đặt `$env:PYTHONIOENCODING = "utf-8"`.

```powershell
cd DoAn\app
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

.venv\Scripts\python -m tools.check_env                                              # kiểm máy và kết nối
.venv\Scripts\python -m tools.setup_db --keyspace ride_booking_demo --seed --yes     # dựng CSDL ứng dụng (TRUNCATE 13 bảng của keyspace đó)

$env:CASSANDRA_KEYSPACE = "ride_booking_demo"
.venv\Scripts\python -m uvicorn main:app --port 8000                                 # mở http://127.0.0.1:8000
```

Tài khoản thử (mật khẩu `123456`): `admin`, `dieuphoi`, `cust001` đến `cust010`, `drv551` đến `drv560`.
Nút "Bật chế độ kỹ thuật" ở chân trang (hoặc biến môi trường `APP_TECH_MODE=1`) hiện lại lệnh CQL đã chạy và các ghi chú kỹ thuật; dùng khi demo cho giảng viên.

## 4. Kiểm thử

```powershell
.venv\Scripts\python -m pytest tests/unit -q -p no:cacheprovider     # vài giây, không cần Cassandra
.venv\Scripts\python -m pytest tests -q -p no:cacheprovider          # toàn bộ, khoảng 6 phút, cần Cassandra ở 127.0.0.1:9042
.venv\Scripts\python -m pytest tests -q -p no:cacheprovider --cov=.
.venv\Scripts\python -m coverage report --omit="tests/*,.venv/*"     # độ bao phủ không tính thư mục test
```

Kết quả gần nhất (2026-11-24, Cassandra 3.11.4): 748 test pass trong 403 giây; độ bao phủ 91,1 % trên 3.297 lệnh (không tính thư mục `tests`).
Marker theo barem: `pytest -m auth|crud|business|backup|nosql`.
Đo hiệu năng: `.venv\Scripts\python -m tools.bench --keyspace ride_booking_bench_test`, kết quả ở `DoAn/app/docs/ket_qua_do_hieu_nang.md`. Đồng hồ Windows làm tròn khoảng 15,6 ms nên công cụ đo bằng query trace phía máy chủ.

## 5. Ứng dụng được tổ chức thế nào

- `main.py`: tạo app, middleware phiên đăng nhập và chế độ bảo trì.
- `config.py`: đọc biến môi trường; danh sách khu vực, phương thức thanh toán, 13 bảng.
- `db/catalog.py`: toàn bộ câu CQL dạng prepared statement, mỗi câu một mã (B: đọc cơ bản, A: tổng hợp, T: ghi có điều kiện, Q: truy vấn báo cáo, APP: riêng của ứng dụng). `db/repo.py` chạy câu theo mã và ghi trace. `db/capabilities.py` ghi kết quả thăm dò Cassandra.
- `domain/`: logic thuần không đụng CSDL (tiền, múi giờ +07, máy trạng thái chuyến, mật khẩu, khuyến mãi, ma trận ghi của từng sự kiện, nhãn tiếng Việt).
- `services/`: nghiệp vụ (đặt xe, nhận chuyến, đánh giá, báo cáo, sao lưu, kiểm tra nhất quán).
- `routes/`: HTTP. Mọi trang render qua `routes/deps.py::render`, hàm này gắn trace CQL, người dùng, thông báo và cờ `tech`.
- `templates/`: Jinja2, mọi trang kế thừa `base.html`.
- `tools/`: CLI dựng CSDL, nạp dữ liệu mẫu, migrate, kiểm môi trường, đo hiệu năng.
- `tests/unit` dùng CSDL giả (`tests/fakes.py`); `tests/integration` chạy trên Cassandra thật, keyspace `ride_booking_test`.

Thêm một câu truy vấn: khai báo trong `db/catalog.py` (kèm bảng và partition key), gọi qua `db.rows`/`db.one`/`db.exec` ở service, nếu là ghi thì cập nhật ma trận ghi trong `domain/write_matrix.py`, rồi viết test unit và integration.

Ghi nhiều bảng: bảng `rides` là nguồn đúng, ghi trước bằng LWT; chỉ khi `[applied]` là True mới ghi các bảng phụ. Lỗi giữa chừng trả kết quả `partial` và được sửa bằng công cụ ở `/admin/consistency`.

## 6. Kết quả thăm dò Cassandra (`capabilities`)

`DoAn/app/db/capabilities.py`, ghi bởi `tests/integration/test_cassandra_probe.py`, `PROBED_ON = "3.11.4 cài trực tiếp Windows, 2026-11-21"`:

| Hằng số | Giá trị | Hệ quả |
|---|---|---|
| `TRUNCATE_CLEARS_MV` | `True` | `TRUNCATE` bảng `vehicles` làm rỗng cả view `vehicles_by_plate`; khôi phục chỉ ghi lại `vehicles`, Cassandra tự dựng lại view |
| `LWT_IF_IN_SUPPORTED` | `True` | `IF status IN (...)` chạy được; ứng dụng vẫn dùng `IF status = <giá trị đã đọc>` |
| `LWT_ON_MV_BASE_OK` | `True` | LWT trên bảng gốc có view chạy được, view cập nhật đúng |
| `JSON_ROUNDTRIP_OK` | `True` | `SELECT JSON` rồi `INSERT ... JSON` khôi phục đúng mọi cột; nền tảng của sao lưu trong ứng dụng |

Chưa chạy lại thăm dò trên Cassandra 3.11.19 (Docker).

## 7. Đã xong

- CSDL: 13 bảng thiết kế theo truy vấn, 1 materialized view, dữ liệu mẫu, truy vấn cơ bản và nâng cao, LWT, sao lưu bằng snapshot và CSV (`DoAn/cassandra/scripts/`).
- Ứng dụng theo barem: đăng nhập, đăng ký, phân quyền, khóa tài khoản (9.1); quản lý khách, tài xế, xe, khuyến mãi, sao lưu và khôi phục JSON (9.2); đặt xe, nhận chuyến bằng LWT hai tầng, bắt đầu, hoàn thành, thanh toán, hủy, đánh giá một lần (9.3); lịch sử, thu nhập tháng, doanh thu ngày và 7 ngày, thống kê khu vực, GPS, xuất CSV (9.4); trang Kết nối và trang NoSQL cho quản trị.
- Đồng thời: điểm trung bình tài xế ghi kèm `USING TIMESTAMP` nên hai lượt đánh giá cùng lúc không ghi đè nhau.
- Giao diện đã rà theo nhận xét giảng viên: không nút trùng chức năng, hỏi lại khi xóa hoặc khóa, giao diện mặc định không có ghi chú kỹ thuật.
- Trải nghiệm đã sửa sau một lượt rà soát giao diện theo các nguyên tắc dễ dùng (nhìn trạng thái hệ thống, phòng lỗi, nhất quán):
  - đặt xe hiện giá ngay trên nút đặt, máy chủ từ chối đặt nếu giá đã đổi;
  - chi tiết chuyến kiểu biên nhận, có biển số chữ to và chấm sao;
  - chuyến chờ dạng thẻ, tự làm mới;
  - trang trạng thái tài xế theo 3 trạng thái;
  - lịch sử và thu nhập dạng thẻ;
  - nút cao 44px trên màn cảm ứng;
  - trang chi tiết chuyến đang chạy tự hỏi `GET /rides/{ride_id}/status` mỗi 5/10/15 giây (có lệch ngẫu nhiên, giãn khi lỗi, dừng khi tab ẩn hoặc chuyến kết thúc), mỗi lần đọc 1 dòng `rides` theo `ride_id`; chế độ kỹ thuật chỉ hiện thanh "Tải lại" để giữ panel CQL (cơ chế riêng của web, không ghi vào báo cáo Word);
  - trên màn hình rộng, trang thao tác (đặt xe, chuyến, tài xế, trang chủ, biểu mẫu quản trị, báo cáo, nhất quán, backup) nằm trong một cột giữa rộng 40rem, đăng nhập và đăng ký 28rem. Trang con chọn bằng `{% set page_width = "narrow" %}` hoặc `"compact"`; trang bảng quản trị, trang Kết nối, NoSQL và panel CQL vẫn dùng hết bề ngang.

  Ảnh màn hình ở `DoAn/app/docs/giao_dien/`.
- Tài liệu: `DoAn/app/docs/kich_ban_demo.md` (kịch bản demo), `DoAn/app/docs/hoi_dap_bao_ve.md` (câu hỏi khi bảo vệ: Jinja2, FastAPI, LWT, phi chuẩn hóa).
- Báo cáo Word có mục 3.7 về ứng dụng và mục "BẢNG PHÂN CÔNG CÔNG VIỆC", 50 trang, mục lục đã cập nhật. Năm hình của mục 3.7 (Hình 3.9–3.13) đã chụp lại theo giao diện mới; số liệu kiểm thử trong báo cáo là 748 test, độ bao phủ 91,1%.

## 8. Việc còn mở

1. Kiểm trên máy từng thành viên: `tools.check_env`, dựng keyspace riêng, chạy toàn bộ test, chạy lại thăm dò `pytest tests/integration/test_cassandra_probe.py -q`.
2. Gộp cột `rated_at` thẳng vào `01_schema.cql`: đang để riêng ở `06_app_migration.cql` để hình DbSchema trong báo cáo không lệch.
3. Keyspace `ride_booking` chưa được kiểm sức khỏe. Kiểm bằng trang `/admin/consistency` và bảng số dòng ở `/admin/backup` khi chạy ứng dụng trên keyspace đó (chỉ đọc).
4. Test tạo snapshot khi `TRUNCATE`; dọn bằng `nodetool clearsnapshot -- ride_booking_test`.

## 9. Giới hạn đã biết

Danh sách đầy đủ ở mục "Giới hạn đã biết" của `DoAn/app/README.md`. Tóm tắt:

- Ghi nhiều bảng không nguyên tử; có công cụ đồng bộ lại nhưng chưa ghi lại bảng đánh giá và điểm tài xế.
- Tài xế có thể kẹt trạng thái bận nếu LWT nhận chuyến gặp `WriteTimeout`; có công cụ giải phóng ở `/admin/consistency`.
- Biển số duy nhất chỉ kiểm bằng đọc view, không có ràng buộc duy nhất thật.
- Đổi tên khách hoặc tài xế không cập nhật tên đã sao chép vào các chuyến cũ.
- Cờ bảo trì nằm trong bộ nhớ một tiến trình.
- File sao lưu chứa mật khẩu đã băm, không phải ảnh chụp nhất quán giữa các bảng.
- Không có CSRF token (cookie `SameSite=lax`); phải đặt `APP_SECRET_KEY` khi chạy thật.
- Mật khẩu dữ liệu mẫu là SHA-256 không salt của `123456`; tài khoản mới dùng PBKDF2.
