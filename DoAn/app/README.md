# Ứng dụng minh họa đặt xe công nghệ trên Cassandra 3.11

Ứng dụng web (FastAPI, Jinja2, Bootstrap, render phía server) cho đề tài "Tìm hiểu công cụ DbSchema để quản trị và khai thác CSDL Cassandra
*Quản lý dữ liệu đặt xe công nghệ* và xây dựng ứng dụng minh họa" (môn Dữ liệu NoSQL, HUIT 14DH). Ứng dụng chạy trên keyspace
`ride_booking` đã thiết kế trong `DoAn/cassandra/` (13 bảng và 1 materialized view `vehicles_by_plate`) và dùng thẳng các câu truy vấn B/A/T/Q
của `DoAn/CASSANDRA.MD`.

Điểm cần thấy khi trình bày: ở cuối mỗi trang có panel **CQL đã chạy** (câu CQL, bảng, partition key, consistency, kết quả LWT `[applied]`,
danh sách bảng bị ghi so với ma trận ghi §3.7). Các bảng phi chuẩn hóa luôn khớp với `rides` nhờ quy tắc "ghi `rides` bằng LWT trước, chỉ khi
`[applied] = True` mới ghi các bảng phụ", và có công cụ Kiểm tra nhất quán để đối chiếu hoặc ghi lại (reconcile).

Tài liệu đi kèm: [`docs/kich_ban_demo.md`](docs/kich_ban_demo.md) (kịch bản demo 5 đến 7 phút), `HANDOFF.md` ở gốc repo (trạng thái công việc,
việc còn mở), thiết kế và kế hoạch ở `docs/superpowers/specs/` và `docs/superpowers/plans/` (gốc repo).

## Tính năng theo vai trò

| Vai trò | Màn hình chính |
|---|---|
| Chưa đăng nhập | `/login`, `/register` (đăng ký khách bằng LWT), `/connection` (thông tin kết nối, mục 8), `/health` |
| Khách (`CUSTOMER`) | `/customer/book` (đặt xe, báo giá, mã khuyến mãi), `/customer/rides` (lịch sử, lọc ngày), `/rides/{ride_id}` (chi tiết, `status_history`, hủy, đánh giá) |
| Tài xế (`DRIVER`) | `/driver` (bật/tắt nhận chuyến theo khu vực, ghi GPS), `/driver/waiting` (chuyến chờ theo khu vực và ngày, nhận chuyến), `/driver/income` (thu nhập tháng), `/driver/ratings` |
| Quản trị (`ADMIN`, và `OPERATOR` được gộp vào ADMIN) | `/admin/accounts` (khóa/mở khóa), `/admin/customers`, `/admin/drivers`, `/admin/vehicles` (tra biển số qua MV), `/admin/promotions` (thêm/bớt phần tử set `cities`), `/admin/reports` (doanh thu ngày, 7 ngày, thống kê khu vực-ngày), `/admin/areas`, `/admin/consistency`, `/admin/backup` |
| Mọi người dùng đã đăng nhập | `/nosql` (collection, clustering DESC, ma trận ghi, catalog câu CQL, truy vấn thiếu partition key) |

Xuất CSV (chỉ quản trị): `/admin/export/history.csv?customer_id=CUST001`, `/admin/export/payments.csv?city=HCM&day=2026-10-04`.
Vị trí GPS của một tài xế: `/admin/drivers/DRV_551/track`.

## Cài đặt

Ứng dụng viết cho Python 3.12 và Cassandra 3.11. Đã chạy thật trên Windows 11 với Python 3.12.7 và Cassandra 3.11.4. Các phiên bản Python khác
**chưa kiểm** (driver `cassandra-driver` cần gói `pyasyncore` trên Python 3.12, xem `DoAn/CASSANDRA.MD` §11).

### 1. Cassandra 3.11.4 cài trực tiếp trên Windows (cách chính, cho cả nhóm)

Cài theo tài liệu thực hành (trang 37 đến 42), tóm tắt trong `DoAn/CASSANDRA.MD` §1.5: JDK 8 (`jdk-8u231-windows-x64`), giải nén
`apache-cassandra-3.11.4-bin` vào `c:\apache-cassandra-3.11.4`, mở Command Prompt, `cd c:\apache-cassandra-3.11.4\bin` rồi chạy `cassandra`.
Khi log có dòng `Node localhost/127.0.0.1 state jump to NORMAL` là sẵn sàng (cổng 9042).

- Python 2.7 trong tài liệu thực hành chỉ để chạy `cqlsh`. **Ứng dụng này không cần `cqlsh` và không cần Python 2.7**: mọi công cụ (dựng CSDL, nạp
  seed, migrate, backup, test) dùng driver Python. Python 3.12 là bản riêng cho ứng dụng.
- Cassandra phải chạy trước khi mở ứng dụng. Nếu chưa chạy, ứng dụng vẫn lên và hiện banner đỏ "Không kết nối được Cassandra".

### 2. Môi trường Python (PowerShell, tại thư mục `DoAn\app`)

```powershell
cd D:\Documents\Homework\NoSQL\DoAn\app
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Dùng `py -3.12` (không dùng `py` trần, vì máy có thể đặt Python 3.14 làm mặc định). Các lệnh dưới đây gọi thẳng `.venv\Scripts\python`
nên không cần `Activate.ps1`. Mọi lệnh `python -m tools.…` và `uvicorn` chạy với thư mục hiện hành là `DoAn\app`.

### 3. Biến môi trường (PowerShell, đặt trước khi chạy tool hoặc app)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `CASSANDRA_HOSTS` | `127.0.0.1` | Danh sách contact point, ngăn cách bằng dấu phẩy |
| `CASSANDRA_PORT` | `9042` | Cổng CQL |
| `CASSANDRA_KEYSPACE` | `ride_booking` | Keyspace ứng dụng làm việc |
| `CASSANDRA_LOCAL_DC` | `datacenter1` | Datacenter cục bộ cho chính sách cân bằng tải |
| `APP_SECRET_KEY` | `dev-secret-change-me` | Khóa ký cookie phiên; nên đặt khi chạy ngoài máy cá nhân |
| `APP_DEBUG` | (tắt) | Đặt `1` (hoặc `true`, `yes`, `on`) để trang lỗi 500 hiện loại lỗi và thông điệp; mặc định ẩn, lỗi chỉ ghi vào log máy chủ |
| `APP_BACKUP_DIR` | `DoAn\app\backups` | Thư mục lưu file backup JSON (đã nằm trong `.gitignore`) |
| `CASSANDRA_TEST_KEYSPACE` | `ride_booking_test` | Keyspace của integration test (phải kết thúc bằng `_test`) |

```powershell
$env:CASSANDRA_HOSTS = "127.0.0.1"
$env:CASSANDRA_PORT = "9042"
$env:CASSANDRA_KEYSPACE = "ride_booking_demo"
$env:CASSANDRA_LOCAL_DC = "datacenter1"
```

Biến chỉ có hiệu lực trong cửa sổ PowerShell đó. Ứng dụng đọc keyspace **một lần lúc khởi động**; đổi biến thì phải chạy lại `uvicorn`.

### 4. Kiểm tra máy

```powershell
.venv\Scripts\python -m tools.check_env
.venv\Scripts\python -m tools.check_env --help        # trợ giúp; tùy chọn --keyspace <tên> kiểm keyspace khác biến môi trường
```

Lệnh in máy chủ, keyspace và các trường `connected`, `release_version`, `keyspace_exists`, `tables`, `has_rated_at`, `error`. Mã thoát 0 khi kết nối được và
keyspace đã có. Trên máy tác giả (keyspace `ride_booking_test`) kết quả là `connected: True`, `release_version: 3.11.4`, `tables: 13`,
`has_rated_at: True`. Keyspace chưa dựng thì in `keyspace_exists: False` và thoát mã 1: làm bước "Chuẩn bị CSDL" bên dưới.

### Docker (cách phụ, môi trường của một người)

Chỉ dùng khi máy không cài Cassandra trực tiếp. Hai service Cassandra trong `docker-compose.yml` cùng dùng cổng 9042, mỗi lúc chỉ chạy một:

```powershell
cd D:\Documents\Homework\NoSQL
docker compose stop cassandra
docker compose up -d cassandra-doan
```

Sau đó làm các bước như trên (ứng dụng vẫn chỉ nói chuyện qua cổng 9042 bằng driver). Cách Docker chưa được chạy lại với ứng dụng này; bản Cassandra
đã kiểm thật là 3.11.4 cài trực tiếp.

## Chuẩn bị CSDL

**Cảnh báo trước khi chạy:** `--seed` sẽ `TRUNCATE` 13 bảng của keyspace được chỉ định rồi nạp lại dữ liệu mẫu. Nếu keyspace `ride_booking` đang chứa
dữ liệu bạn đã dùng làm báo cáo (ảnh chụp DbSchema, kết quả chạy `03`, `04`, `05`), **đừng** chạy lệnh này lên nó. Hãy dựng một keyspace riêng cho
ứng dụng, ví dụ `ride_booking_demo`. Tool chỉ dùng `CREATE ... IF NOT EXISTS`, không bao giờ `DROP`.

### Trường hợp 1: dựng CSDL mới bằng ứng dụng (không cần cqlsh)

```powershell
.venv\Scripts\python -m tools.setup_db --keyspace ride_booking --seed --yes
```

Lệnh làm ba việc: tạo keyspace, 13 bảng và MV từ `DoAn/cassandra/01_schema.cql`; thêm cột `rides.rated_at` (xem phần 06 bên dưới); `TRUNCATE` rồi
nạp seed từ `DoAn/cassandra/02_data.cql`. Thiếu `--yes` thì tool từ chối (mã thoát 2). Muốn keyspace riêng, đổi tên: `--keyspace ride_booking_demo`.
Khi đó đặt `$env:CASSANDRA_KEYSPACE = "ride_booking_demo"` trước khi chạy ứng dụng. Kết quả mong đợi: số dòng seed mỗi bảng khớp bảng
`EXPECTED_SEED_COUNTS` trong `tools/seed.py` (10 khách, 10 tài xế, 10 xe, 22 tài khoản, 36 chuyến, 3 mã khuyến mãi, ...). Nếu bạn sửa `02_data.cql`
làm số dòng đổi thì tool báo "Số dòng seed không khớp" và dừng **trước** khi `TRUNCATE`.

`02_data.cql` hiện chỉ còn phần seed (321 dòng, đã dọn đoạn chạy thử T01/T05/T07/T08 ở đuôi). Dù vậy tool vẫn chỉ nạp các lệnh `INSERT` cho đến hết khối
`driver_locations`, nên một đoạn đuôi nào được thêm lại sau này cũng không bị chạy.

Chỉ nạp lại seed lên keyspace đã có schema: `python -m tools.seed --keyspace <tên> --yes`.

### Trường hợp 2: CSDL đã dựng từ Word (chạy `01_schema.cql`, `02_data.cql` bằng cqlsh/DbSchema)

```powershell
.venv\Scripts\python -m tools.migrate --keyspace ride_booking
```

Lệnh chỉ thêm cột `rides.rated_at` nếu chưa có (chạy lại nhiều lần được) rồi đánh dấu các chuyến seed đã có đánh giá (backfill). **Không xóa dữ liệu.**
Hệ quả: `DESCRIBE`/DbSchema của keyspace đó sẽ có thêm cột `rated_at`, không còn khớp hình trong Word. Vì vậy nên để keyspace `ride_booking` của báo cáo nguyên
vẹn và chạy ứng dụng trên keyspace riêng ở Trường hợp 1.

### Chạy ứng dụng

```powershell
.venv\Scripts\python -m uvicorn main:app --port 8000
```

Mở <http://127.0.0.1:8000>. Trang chủ `/` hiện keyspace đang dùng, phiên bản Cassandra (`release_version` đọc một dòng từ `system.local`) và các lối vào nhanh theo vai trò
của người đã đăng nhập (quản trị: tài khoản, danh mục, báo cáo, khu vực, nhất quán, backup; khách: đặt xe, lịch sử; tài xế: nhận chuyến, thu nhập, đánh giá; chưa đăng nhập: đăng nhập, đăng ký, kết nối). Trang `/connection` cho biết ứng dụng đang nối tới đâu (host, protocol 4, `release_version` lấy từ `system.local`, keyspace,
danh sách bảng, `rides.rated_at` đã có hay chưa). `/health` trả `{"status": "ok"}` kể cả khi chưa nối được Cassandra.

## Tài khoản đăng nhập thử

Mật khẩu của **mọi** tài khoản seed là `123456` (chỉ dùng cho demo, xem phần Giới hạn).

| Tên đăng nhập | Vai trò | Ghi chú |
|---|---|---|
| `admin` | ADMIN | Quản trị hệ thống |
| `dieuphoi` | OPERATOR (tính là ADMIN) | Nhân viên điều phối, cùng quyền với `admin` |
| `cust001` ... `cust010` | CUSTOMER | `cust001` là CUST001 Nguyễn Văn An; `cust006` là CUST006 Võ Ngọc Hân |
| `drv551` ... `drv560` | DRIVER | `drv551` là DRV_551, ..., `drv560` là DRV_560 (bảng dưới) |

Tài khoản đăng ký mới ở `/register` luôn là khách (CUSTOMER) và dùng mật khẩu băm PBKDF2.

Biển số và trạng thái ban đầu của từng tài xế (lấy từ `02_data.cql`). Tài xế bật nhận chuyến phải nhập **đúng biển số xe của mình**, ứng dụng kiểm qua MV
`vehicles_by_plate`:

| Tài khoản | Mã | Biển số | Xe | Trạng thái seed | Khu vực seed |
|---|---|---|---|---|---|
| `drv551` | DRV_551 | `51F-123.45` | Toyota Vios | AVAILABLE | HCM / TAN_PHU |
| `drv552` | DRV_552 | `51G-234.56` | Kia Morning | BUSY | (đang chạy chuyến) |
| `drv553` | DRV_553 | `59X1-345.67` | Honda Vision | AVAILABLE | HCM / BINH_THANH |
| `drv554` | DRV_554 | `51H-456.78` | Hyundai Grand i10 | AVAILABLE | HCM / Q3 |
| `drv555` | DRV_555 | `51K-567.89` | Toyota Innova | OFFLINE | không có (bật nhận chuyến để vào khu vực) |
| `drv556` | DRV_556 | `59T2-678.90` | Yamaha Sirius | BUSY | (đang chạy chuyến) |
| `drv557` | DRV_557 | `30H-111.22` | Toyota Vios | AVAILABLE | HN / CAU_GIAY |
| `drv558` | DRV_558 | `29B1-222.33` | Honda Wave Alpha | AVAILABLE | HN / HOAN_KIEM |
| `drv559` | DRV_559 | `30K-333.44` | Mazda 2 | BUSY | (đang chạy chuyến) |
| `drv560` | DRV_560 | `30G-444.55` | VinFast VF 5 | AVAILABLE | HN / CAU_GIAY |

Trạng thái trên chỉ đúng ngay sau khi nạp seed; sau khi bạn thao tác (hoặc chạy kịch bản demo) chúng thay đổi.

Mã khuyến mãi seed: `GIAM20` (20%, tối đa 30.000đ, đơn từ 50.000đ, HCM và HN), `HCMXANH` (15%, tối đa 20.000đ, HCM), `HANOI10` (10%, tối đa 15.000đ, HN).
Cả ba hết hạn lúc 23:59:59 ngày 31/12/2026 (+07:00). Dữ liệu chuyến mẫu nằm ở ngày 04/10/2026 và tháng 202610: ở các trang báo cáo, chọn đúng ngày/tháng
đó để thấy số liệu (trang có dòng nhắc "Dữ liệu mẫu: 04/10/2026").

## Chạy test tự động

Mọi lệnh chạy ở `DoAn\app`. Unit test không cần Cassandra; integration test cần Cassandra đang chạy ở địa chỉ trong biến môi trường.

```powershell
.venv\Scripts\python -m pytest tests -q -p no:cacheprovider      # toàn bộ (unit + integration), khoảng 3 phút khi có Cassandra
.venv\Scripts\python -m pytest tests/unit -q                     # chỉ unit, vài giây, không cần Cassandra
.venv\Scripts\python -m pytest tests/integration -q              # chỉ integration (cần Cassandra)
```

Chạy theo nhóm barem (marker khai báo trong `pytest.ini`):

```powershell
.venv\Scripts\python -m pytest -m auth -q        # 9.1 đăng nhập, phân quyền, khóa tài khoản, IDOR
.venv\Scripts\python -m pytest -m crud -q        # 9.2 CRUD danh mục
.venv\Scripts\python -m pytest -m business -q    # 9.3 và 9.4 nghiệp vụ, báo cáo, kịch bản T01-T12
.venv\Scripts\python -m pytest -m backup -q      # 9.2 backup/restore
.venv\Scripts\python -m pytest -m nosql -q       # đặc trưng NoSQL: LWT, MV, collection, guard, probe
```

Lần chạy gần nhất khi viết tài liệu này: toàn bộ test xanh trên Cassandra 3.11.4 (cài trực tiếp, Windows 11, Python 3.12.7), cả chế độ reset thường và đầy đủ.
Số lượng test sẽ thay đổi khi bổ sung; xem dòng cuối của pytest.

### Keyspace test và các chốt an toàn

- Integration test **không bao giờ** chạy trên keyspace của bạn. Chúng dùng keyspace riêng `ride_booking_test` (đổi bằng `CASSANDRA_TEST_KEYSPACE`),
  mỗi phiên chạy sẽ `DROP KEYSPACE IF EXISTS` rồi dựng lại từ `01_schema.cql` cộng cột `rated_at`, nạp seed, và chỉ reset những bảng bị test làm bẩn.
- **Guard `_test`:** nếu tên keyspace test không kết thúc bằng `_test`, bộ test dừng ngay (`UnsafeKeyspaceError`, mã thoát 4) trước khi ghi bất cứ thứ gì.
  Hàm dựng keyspace test cũng tự kiểm lại điều kiện này.
- **Tự skip:** không kết nối được Cassandra thì integration test được đánh dấu SKIPPED (unit vẫn chạy), không báo lỗi.
- **Dọn snapshot:** vì `auto_snapshot = true`, mỗi `TRUNCATE`/`DROP` của test để lại snapshot trên đĩa. Dọn bằng `nodetool` của Cassandra
  (cài trực tiếp: mở Command Prompt ở `c:\apache-cassandra-3.11.4\bin`):

```powershell
nodetool clearsnapshot -- ride_booking_test
# Docker: thêm "docker exec nosql-cassandra-doan" phía trước
docker exec nosql-cassandra-doan nodetool clearsnapshot -- ride_booking_test
```

## Đối chiếu barem chấm điểm

Thang điểm: mục 8 (0,5đ) và bốn ý của mục 9 (mỗi ý 0,5đ). Cột "Test" là file test chính, chạy bằng marker ở cột cuối.

| Mục | Nội dung barem | Hiện thực trong ứng dụng | Test chính | Marker |
|---|---|---|---|---|
| 8 | Kết nối CSDL với phần mềm ứng dụng | `config.py` (`Settings.from_env`), `db/session.py` (Cluster, protocol v4, LOCAL_QUORUM/LOCAL_SERIAL), trang `/connection` | `tests/integration/test_connection_page.py`, `tests/integration/test_repo_live.py` | `nosql` |
| 9.1 | Quản trị người dùng | Đăng nhập/đăng xuất (Q1), đăng ký khách bằng LWT `IF NOT EXISTS`, khóa/mở khóa bằng LWT, phân quyền ADMIN/CUSTOMER/DRIVER, kiểm tài khoản bị khóa ở **mỗi** request, không khóa admin cuối, chống IDOR | `tests/integration/test_auth_flow.py`, `tests/integration/test_booking_http.py`, `tests/integration/test_ride_authz_http.py` | `auth` |
| 9.2 | Thao tác CSDL: thêm, xóa, sửa, backup | CRUD `customers`, `drivers`, `vehicles` (tra qua MV), `promotions` (thêm/bớt phần tử set `cities`); backup/restore JSON ở `/admin/backup` | `tests/integration/test_crud.py`, `tests/integration/test_backup_restore.py` | `crud`, `backup` |
| 9.3 | Quản lý theo chức năng bài toán | Đặt xe + mã khuyến mãi, bật/tắt nhận chuyến, chuyến chờ theo khu vực, nhận chuyến (LWT hai tầng), bắt đầu, hoàn thành + thanh toán, hủy, đánh giá, lịch sử, chi tiết + `status_history`, thu nhập tháng | `tests/integration/test_booking.py`, `test_driver_presence.py`, `test_accept.py`, `test_ride_transitions.py`, `test_rating.py`, `test_scenario_t01_t12.py` | `business` |
| 9.4 | Chức năng hỗ trợ khác | Doanh thu ngày và 7 ngày, thống kê chuyến theo khu vực-ngày, GPS tài xế, xuất CSV, Kiểm tra nhất quán + reconcile + giải phóng tài xế kẹt BUSY | `tests/integration/test_reports.py`, `tests/integration/test_consistency.py` | `business` |
| (đặc trưng NoSQL) | Panel CQL, `[applied]`, ma trận ghi, collection, clustering DESC, thiếu partition key | `db/trace.py`, `db/catalog.py`, trang `/nosql`, `domain/write_matrix.py` | `tests/unit/test_repo_trace.py`, `tests/integration/test_cassandra_probe.py`, `tests/integration/test_nosql_page.py` | `nosql` |

Kịch bản T01 đến T12 của `CASSANDRA.MD` §8 được chạy end-to-end qua HTTP và service trong
`tests/integration/test_scenario_t01_t12.py`, kết quả cuối khớp §8 (điểm tài xế 4,67; khách trả 65.000đ cho chuyến 81.000đ giảm 16.000đ). Các ca khó
(tranh nhận một chuyến, tranh lượt mã khuyến mãi, hủy chạy đua với nhận chuyến, gửi lại form đặt xe, restore bằng file hỏng, truy cập chuyến của người khác)
đều có test riêng.

## Khác biệt so với 05_transactions.cql

`05_transactions.cql` minh họa từng câu CQL; ứng dụng phải chạy nhiều người cùng lúc nên có một số điểm khác (ký hiệu D1 đến D14 là các quyết định trong
kế hoạch triển khai). Kết quả cuối của kịch bản vẫn khớp `CASSANDRA.MD` §8.

- **T01 đảo thứ tự (đăng ký).** 05 ghi `customers` trước. Ứng dụng ghi `user_accounts` bằng LWT `IF NOT EXISTS` **trước** (tên đăng nhập là khóa duy nhất),
  chỉ khi `[applied] = True` mới ghi `customers` (cũng `IF NOT EXISTS`). Tên bị trùng thì không để lại hồ sơ khách mồ côi.
- **T03 (tài xế bật nhận chuyến).** 05 dùng `UPDATE drivers` thường. Ứng dụng dùng LWT `IF status = 'OFFLINE'` (D4), kiểm biển số qua MV (D5) và chỉ để tài xế
  ở **một** `(city, district)`: xóa dòng ở mọi khu vực trong cấu hình trước khi ghi khu vực mới. Tài xế BUSY không bật lại được và không tắt được khi đang BUSY.
- **T04 (đặt xe) và T07 (mã khuyến mãi) – D2.** 05 trừ lượt mã sau khi chuyến chạy. Ứng dụng **giữ lượt lúc đặt xe** bằng vòng LWT `IF used_count = n`
  (dừng khi `>= usage_limit`) **trước** `INSERT rides ... IF NOT EXISTS`; nếu chuyến không applied (gửi trùng) thì trả lượt. Crash giữa hai bước chỉ làm thất
  thoát một lượt, không bao giờ vượt giới hạn. Hủy chuyến cũng trả lượt. `ride_id` dạng `RIDE_<yyyyMMddHHmmss>_<rand>` được sinh lúc mở form, nên F5 hoặc bấm đúp
  không tạo chuyến thứ hai.
- **T05 (nhận chuyến) hai tầng – D2/D4.** 05 chỉ có LWT trên `rides` rồi `UPDATE drivers SET status = 'BUSY'` thường. Ứng dụng chạy LWT `drivers`
  (`IF status = 'AVAILABLE'` sang `BUSY`) **trước**, rồi LWT `rides` (`IF status = 'REQUESTED'`); thua ở `rides` thì trả tài xế về `AVAILABLE` (`IF status = 'BUSY'`).
  Nhận xong, xóa tài xế khỏi `drivers_by_area` ở mọi khu vực.
- **T06 (bắt đầu).** Như 05: `IF status = 'ACCEPTED' AND driver_id = ?`.
- **T08 (hoàn thành) thêm `AND driver_id`.** 05 chỉ `IF status = 'ONGOING'`. Ứng dụng dùng `IF status = 'ONGOING' AND driver_id = ?` để tài xế khác không hoàn thành
  chuyến của người khác. Sau đó ghi thanh toán, trả tài xế `AVAILABLE` và đưa lại vào `drivers_by_area` tại quận trả khách.
- **T09 (đánh giá) bổ sung.** 05 chỉ chèn `ratings_by_driver` rồi `UPDATE drivers SET rating`. Ứng dụng thêm (a) LWT `IF rated_at = null` trên `rides` để
  mỗi chuyến chỉ đánh giá một lần (cần cột `rated_at`, xem phần 06) và (b) cập nhật cả `drivers_by_area.rating`, nhưng **chỉ khi** tài xế đang có dòng ở khu vực nào
  đó (không tạo "dòng ma" cho tài xế offline). Chỉ khách của chuyến, chuyến COMPLETED mới đánh giá được; điểm trung bình làm tròn 2 chữ số.
- **T10 (hủy) – D3.** 05 dùng `IF status IN ('REQUESTED', 'ACCEPTED')`. Ứng dụng dùng `IF status = <trạng thái vừa đọc>` (tối đa 2 vòng đọc lại), vì khi chuyến vừa
  đổi REQUESTED sang ACCEPTED giữa lúc đọc và lúc ghi thì cần biết để trả tài xế về AVAILABLE. Lệnh `IF ... IN` vẫn chạy được trên 3.11.4 (xem phần probe).
- **T11 (set `cities`) và CRUD – D13.** Thêm/bớt phần tử set dùng `... IF EXISTS`; CRUD dùng `IF NOT EXISTS` khi tạo, `IF EXISTS` khi sửa, vì `INSERT`/`UPDATE` của
  Cassandra là upsert và sẽ tạo dòng ma cho khóa không tồn tại.
- **Thời gian – D1, D11.** Thời điểm nghiệp vụ lấy từ `now_vn()` (+07:00, cắt xuống mili-giây để khóa clustering `requested_at` đọc lại khớp chính xác); khóa của
  bảng phụ luôn lấy từ dòng `rides` vừa đọc. Múi giờ cố định `UTC+7`, không dùng `zoneinfo` vì Windows không có sẵn tzdata.
- **Truy vấn – D12, D14.** Mọi `SELECT` liệt kê cột (không `SELECT *`) vì protocol v4 giữ metadata cũ của prepared statement sau `ALTER TABLE ... ADD`. Sau mỗi
  POST ứng dụng redirect (PRG); CQL của thao tác vừa rồi được giữ trong bộ nhớ (100 thao tác gần nhất) và hiện ở trang kế tiếp.
- **Lỗi ghi bảng phụ – D10.** Nếu một lệnh ghi bảng phụ lỗi sau khi LWT đã applied, ứng dụng không rollback; kết quả `partial` kèm gợi ý dùng
  Kiểm tra nhất quán, mục Reconcile.

## Thay đổi schema: 06_app_migration.cql

Ứng dụng thay đổi schema **đúng một chỗ**, theo quy tắc chỉ `ALTER TABLE ... ADD` và đặt trong file riêng `DoAn/cassandra/06_app_migration.cql`:

```sql
ALTER TABLE rides ADD rated_at timestamp;
```

- **Lý do:** chặn đánh giá trùng. Hai lần bấm "Gửi đánh giá" cùng lúc phải chỉ có một lần thắng, nên cần một cột để LWT kiểm:
  `UPDATE rides SET rated_at = ? WHERE ride_id = ? IF rated_at = null AND status = 'COMPLETED' AND customer_id = ?`.
- **Không sửa `01_schema.cql`** để file Word và các hình đã chụp của cả nhóm không bị lệch. (Phương án gộp `rated_at` thẳng vào `01_schema.cql` được hoãn.)
- **Cách chạy:** `python -m tools.setup_db ...` đã tự chạy bước này; với CSDL có sẵn thì `python -m tools.migrate --keyspace <tên>` (chạy lại được). Dùng
  `cqlsh -f 06_app_migration.cql` cũng được nhưng chạy lần hai sẽ báo lỗi "conflicts with an existing column".
- **Backfill:** sau khi thêm cột, các chuyến seed đã có dòng đánh giá nhưng `rated_at` còn `null` sẽ cho phép đánh giá lại. Vì vậy `tools.migrate`, fixture test và nút
  "Chạy backfill" ở `/admin/consistency` đều chạy hàm `backfill_rated_at` (LWT `IF rated_at = null AND status = 'COMPLETED'`, đặt `rated_at` bằng thời điểm đánh giá).
- **DbSchema và Word không có cột này.** Sau khi chạy migration lên một keyspace, `DESCRIBE`/DbSchema (Refresh) của keyspace đó sẽ hiện thêm `rated_at`. Hãy chạy
  trên keyspace dành cho ứng dụng demo, không chạy lên CSDL đã dùng để chụp hình báo cáo.

## Kết quả thăm dò Cassandra (probe)

Hai điểm spec chưa chắc và hai điểm bổ sung được thăm dò bằng `tests/integration/test_cassandra_probe.py`; kết quả ghi trong `db/capabilities.py` và
`PROBED_ON = "3.11.4 cài trực tiếp Windows, 2026-11-21"`:

| Hằng số | Giá trị | Ý nghĩa và cách ứng dụng xử lý |
|---|---|---|
| `TRUNCATE_CLEARS_MV` | `True` | `TRUNCATE vehicles` làm rỗng luôn MV `vehicles_by_plate`; restore chỉ ghi lại `vehicles`, không ghi trực tiếp vào MV |
| `LWT_IF_IN_SUPPORTED` | `True` | `IF status IN (...)` chạy được trên 3.11.4; ứng dụng vẫn dùng `IF status = ...` (D3) |
| `LWT_ON_MV_BASE_OK` | `True` | LWT trên bảng gốc có MV chạy được và MV được cập nhật đúng |
| `JSON_ROUNDTRIP_OK` | `True` | `SELECT JSON` rồi `INSERT ... JSON` khôi phục đúng mọi cột (timestamp, date, map, set, list, null); nền tảng của backup/restore |

Cả nhóm có thể tự kiểm trên máy mình bằng `.venv\Scripts\python -m pytest tests/integration/test_cassandra_probe.py -q`.

## Cấu trúc thư mục

```text
config.py            Cấu hình, hằng số nghiệp vụ, guard keyspace _test
main.py              create_app: middleware (trace, bảo trì), xử lý lỗi, include router
db/                  session (Cluster), catalog (prepared statement mã B/A/T/Q), repo (CassandraDb), trace, migrate, capabilities
domain/              Logic thuần không gọi DB: tiền, múi giờ, mã chuyến, máy trạng thái, mật khẩu, khuyến mãi, ma trận ghi
services/            Luồng ghi nhiều bảng (đặt xe, nhận chuyến, hoàn thành, đánh giá, backup, nhất quán, báo cáo)
routes/              FastAPI router (khai báo bằng def vì driver chạy đồng bộ)
templates/ static/   Jinja2 và Bootstrap 5 (đã chép sẵn vào static/, không cần mạng)
tools/               check_env, setup_db, migrate, seed (CLI chỉ dùng driver, không cần cqlsh)
tests/               unit (domain, service với FakeDb) và integration (Cassandra thật, keyspace _test)
docs/                kich_ban_demo.md
```

## Giới hạn đã biết

Đây là những điểm đã được ghi nhận trong lúc xây dựng và chưa xử lý hoặc chỉ giảm nhẹ. Báo cáo nên nói thẳng chúng.

**Tính nhất quán dữ liệu**

- **Ghi nhiều bảng không nguyên tử.** Cassandra không có transaction đa bảng và ứng dụng không dùng BATCH. LWT trên `rides` chạy trước, các bảng phi chuẩn hóa ghi sau;
  nếu một lệnh sau lỗi thì dữ liệu lệch tạm thời (kết quả `partial`). Công cụ `/admin/consistency` so từng chuyến với các bảng phụ và `reconcile` ghi lại từ `rides`.
- **Tài xế có thể kẹt BUSY.** Nhận chuyến chạy LWT `drivers` (sang BUSY) trước rồi LWT `rides`. Nếu LWT gặp `WriteTimeout` (kết quả không rõ) hoặc tiến trình dừng giữa hai
  bước, tài xế có thể ở BUSY mà không có chuyến nào. Mục "Tài xế kẹt BUSY" ở `/admin/consistency` tìm và giải phóng (chỉ sau khi xác minh không có chuyến ACCEPTED/ONGOING).
  Vẫn còn một cửa sổ chạy đua hẹp giữa lúc giải phóng và lúc có người nhận chuyến; ứng dụng kiểm lại sau khi giải phóng và giữ BUSY nếu thấy chuyến mới.
- **Hai admin khóa chéo nhau cùng lúc** có thể cùng vượt qua phép kiểm "không khóa admin cuối cùng", vì phép kiểm là đọc rồi ghi, không phải một LWT duy nhất.
- **Biển số duy nhất chỉ kiểm bằng đọc MV.** Cassandra không có ràng buộc unique ngoài khóa chính, `vehicles_by_plate` là MV và LWT không tạo được điều kiện trên nó;
  hai người thêm cùng biển số gần như cùng lúc có thể cùng qua.
- **Tên phi chuẩn hóa là bản chụp lịch sử.** Bảng chuyến lưu sẵn tên và số điện thoại khách/tài xế lúc xảy ra. Đổi tên khách hoặc tài xế **không** cập nhật các bảng chuyến cũ.
- **Đánh giá có thể mất dòng khi lỗi ghi.** Thứ tự là: LWT `rated_at` trên `rides`, rồi chèn `ratings_by_driver`, rồi cập nhật điểm. Nếu lỗi ghi sau khi LWT `rated_at` đã
  applied, chuyến bị đánh dấu "đã đánh giá" nhưng có thể thiếu dòng trong `ratings_by_driver`; hiện **chưa có** công cụ chèn lại dòng đó. `reconcile` chỉ ghi lại các bảng chuyến và thanh toán (`rides_by_customer`, `rides_by_area_date`, `rides_by_driver_month`, `payments_by_city_date`), không đụng tới `ratings_by_driver` hay điểm của tài xế.
- **`first_month` cố định.** Phép kiểm "tài xế đã có chuyến" quét `rides_by_driver_month` từ tháng 202609 đến tháng hiện tại; dữ liệu cũ hơn không bị phát hiện.

**Hiệu năng và vận hành**

- **Một số trang phải quét toàn bảng.** Danh sách tài khoản/khách/tài xế/khuyến mãi ở trang admin và các kiểm tra ở trang Nhất quán đọc cả bảng. Chấp nhận được ở quy mô dữ liệu mẫu,
  sẽ chậm khi dữ liệu lớn.
- **Cờ bảo trì nằm trong bộ nhớ của một tiến trình.** Khi restore, middleware chặn mọi thao tác ghi khác. Nếu chạy nhiều worker, mỗi worker có một cờ riêng; request đang chạy dở
  trước lúc bật cờ vẫn có thể ghi chen vào giữa lúc restore.
- **Backup/restore.** File backup JSON chứa `password_hash` nên phải giữ kín. Backup đọc từng bảng riêng nên **không phải ảnh chụp nhất quán giữa các bảng**
  (nên tạo khi ít người ghi). Restore **không tự rollback**: trước khi `TRUNCATE`, ứng dụng ghi bản an toàn `*_prerestore.json` của dữ liệu hiện tại, nếu restore lỗi giữa chừng thì
  khôi phục tay từ file đó. File được kiểm toàn bộ (định dạng, đủ 13 bảng, cột và kiểu khớp schema) trước khi xóa bất kỳ thứ gì.

**Bảo mật**

- **Trang lỗi 500 không in loại lỗi và thông điệp** (tránh lộ chuỗi lỗi CSDL, đường dẫn): người dùng chỉ thấy thông báo chung, lỗi đầy đủ kèm traceback được ghi vào log của máy chủ
  (logger `ride_booking`, hiện ở cửa sổ chạy `uvicorn`). Đặt `APP_DEBUG=1` thì trang 500 mới hiện `TênLỗi: nội dung` (chỉ để gỡ lỗi trên máy cá nhân, không bật trên mạng thật).
- **Không có CSRF token.** Chỉ dựa vào cookie phiên `SameSite=lax`. Khóa ký phiên mặc định là `dev-secret-change-me` trừ khi đặt `APP_SECRET_KEY`.
- **Mật khẩu seed là SHA-256 không salt của `123456`** (cho khớp dữ liệu mẫu trong Word, chỉ dùng demo). Tài khoản đăng ký mới dùng PBKDF2-SHA256 có salt (100.000 vòng, thư viện chuẩn).
  `verify_password` nhận được cả hai kiểu.

**Dữ liệu mẫu và môi trường**

- **Mã khuyến mãi seed hết hạn 2026-12-31** (`valid_to` của `GIAM20`, `HCMXANH`, `HANOI10`). Sau ngày đó đặt xe kèm mã sẽ bị từ chối; cần sửa hạn ở `/admin/promotions`.
- **Phiên bản Cassandra.** Test đã chạy thật trên Cassandra 3.11.4 (`release_version` = 3.11.4, ghi trong `PROBED_ON`). Việc chạy ứng dụng trên **máy của từng thành viên**
  (cài riêng) **chưa kiểm**: mỗi người tự kiểm bằng `python -m tools.check_env` và bằng test probe ở trên. Bản 3.11.19 của Docker chưa chạy lại với ứng dụng này.
- **Bootstrap có sẵn trong `static/`.** Bản 5.3.3 (chỉ file CSS) đã chép vào `static/bootstrap.min.css`, ứng dụng không tải gì từ CDN nên chạy được khi không có mạng.
