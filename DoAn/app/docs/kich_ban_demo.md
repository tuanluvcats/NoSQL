# Kịch bản demo 5–7 phút: ứng dụng đặt xe công nghệ trên Cassandra

Dùng cho buổi báo cáo trực tiếp hoặc quay video. Thứ tự đi theo thang điểm: mục 8 (kết nối), rồi bốn ý của mục 9 (9.1 quản trị người dùng, 9.2 thao tác
CSDL, 9.3 nghiệp vụ, 9.4 chức năng hỗ trợ), rồi phần đặc trưng NoSQL và hạn chế. Mỗi thao tác trên ứng dụng đều **mở DbSchema song song** để thấy
dữ liệu trong Cassandra thay đổi thật. Cột "Thấy ở đâu" ghi chỗ cần chỉ: panel **CQL đã chạy** ở cuối trang (mã B/A/T/Q, bảng, partition key,
consistency, kết quả `[applied]`) và bảng trong DbSchema.

Số liệu dùng trong kịch bản (81.000đ, giảm 16.000đ, trả 65.000đ; `[applied]`; thông báo lỗi) lấy từ lần chạy thật trên Cassandra 3.11.4. Các tên menu của
DbSchema (mở dữ liệu bảng, làm mới) có thể khác chút giữa các phiên bản; bản đã dùng cho báo cáo là DbSchema 10.5.2.

## 0. Chuẩn bị (trước khi bấm quay)

| Bước | Việc | Lệnh / màn hình |
|---|---|---|
| 0.1 | Bật Cassandra 3.11.4 và kiểm tra máy | `cd DoAn\app` rồi `.venv\Scripts\python -m tools.check_env` (phải thấy `connected: True`, `release_version: 3.11.4`) |
| 0.2 | Dựng CSDL demo sạch ngay trước buổi quay | `.venv\Scripts\python -m tools.setup_db --keyspace ride_booking_demo --seed --yes`. Lệnh này `TRUNCATE` 13 bảng của keyspace đó, nên dùng keyspace riêng, không phải `ride_booking` của báo cáo. Nạp lại seed để dữ liệu và trạng thái tài xế đúng như kịch bản |
| 0.3 | Chạy ứng dụng trên keyspace demo | `$env:CASSANDRA_KEYSPACE = "ride_booking_demo"` rồi `.venv\Scripts\python -m uvicorn main:app --port 8000` |
| 0.4 | Hai trình duyệt **khác nhau** | Trình duyệt A (Chrome thường) và B (Chrome ẩn danh, hoặc Edge). Hai **tab của cùng một trình duyệt dùng chung cookie phiên**, nên đăng nhập hai người khác nhau ở hai tab sẽ đè lên nhau. Phiên A: `admin`, sau đó `drv555`. Phiên B: `cust016`, `cust001`, sau đó `drv554` |
| 0.5 | DbSchema song song | Kết nối `localhost:9042` (Method Standard, DataCenter để trống hoặc `datacenter1`), keyspace `ride_booking_demo`. Mở sẵn dữ liệu các bảng `user_accounts`, `customers`, `promotions`, `rides`, `drivers`, `drivers_by_area`, `payments_by_city_date`. Sau mỗi thao tác bấm làm mới (Refresh) bảng liên quan |
| 0.6 | Cửa sổ khác | Thư mục `DoAn\app\backups` (để thấy file backup JSON xuất hiện), một slide bìa, slide sơ đồ 13 bảng + MV |
| 0.7 | Kiểm tra trạng thái ban đầu | `drv555` đang OFFLINE, `drv554` AVAILABLE ở HCM / Q3, mã `GIAM20` có `used_count = 5` (xem bảng `promotions`) |

Mật khẩu của mọi tài khoản seed là `123456`. Biển số của `drv555` là `51K-567.89`.

## 1. Giới thiệu và kết nối CSDL, mục 8 (0:00–0:45)

| Thời lượng | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|
| 0:00–0:15 | Slide bìa | Tên đề tài, thành viên, môn Dữ liệu NoSQL 14DH | – |
| 0:15–0:45 | Trình duyệt A, chưa đăng nhập: `/connection`. Chuyển sang DbSchema, mở cây keyspace `ride_booking_demo` | Ứng dụng nối Cassandra bằng driver Python qua giao thức CQL native v4. Thông tin đọc từ `system.local` và `system_schema` của chính máy chủ: host `127.0.0.1`, port 9042, datacenter `datacenter1`, `protocol_version` 4, `release_version` 3.11.4, keyspace, **13 bảng và 1 materialized view** `vehicles_by_plate`, cột `rides.rated_at` đã có. Consistency LOCAL_QUORUM, LWT dùng LOCAL_SERIAL | Trang `/connection`. DbSchema: cùng keyspace, cùng 13 bảng và 1 view. Hai công cụ cùng nhìn một CSDL |

## 2. Bốn nhóm chức năng của mục 9 (0:45–4:50)

### 9.1 Quản trị người dùng (0:45–1:25)

| Thời lượng | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|
| 0:45–1:05 | Phiên B: `/register`, đăng ký `cust016` (mật khẩu `123456`, họ tên "Khách Thử Mười Sáu", điện thoại `0901000016`, email `cust016@example.com`). Bấm đăng ký **lần thứ hai** với cùng tên | Đăng ký ghi `user_accounts` bằng LWT `IF NOT EXISTS` trước, rồi mới ghi `customers`. Lần hai bị từ chối vì tên đã có: đây là `[applied] = False` thật, kèm dòng hiện có (không lộ mật khẩu) | Panel: mã `T01` trên `user_accounts` (LWT), lần một `[applied] True`, lần hai `[applied] False` kèm bảng giá trị hiện tại. DbSchema: dòng `cust016` trong `user_accounts` và `customers` |
| 1:05–1:25 | Phiên A: đăng nhập `admin`, vào `/admin/accounts`, bấm **Khóa** `cust016`. Phiên B: đăng nhập lại `cust016`. Quay lại A, bấm **Mở khóa** | Phân quyền ADMIN/CUSTOMER/DRIVER. Khóa là LWT `IF is_active = true`; kiểm tài khoản bị khóa ở **mỗi** request. Đăng nhập khi bị khóa trả 403 "Tài khoản đã bị khóa." Không khóa được admin cuối cùng | Panel: mã `T02` trên `user_accounts`, `[applied] True`. DbSchema: `user_accounts.is_active` đổi `false`, rồi `true` |

### 9.2 Thao tác trên CSDL: thêm, xóa, sửa, backup (1:25–2:10)

| Thời lượng | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|
| 1:25–1:45 | Phiên A: `/admin/customers`, **Thêm khách** `CUST099` (họ tên bất kỳ, điện thoại `0900000099`), rồi **Sửa** đổi tên. Thử **Xóa** `CUST001` | Thêm dùng `IF NOT EXISTS`, sửa dùng `IF EXISTS`, vì `INSERT`/`UPDATE` của Cassandra là upsert và sẽ tạo dòng ma. Khách đã có chuyến thì không xóa được (dùng khóa tài khoản) | Panel: mã `B18` (thêm) và `B19` (sửa) trên `customers`, cột `[applied]`. Thông báo "Khách đã có chuyến đi, không được xóa." DbSchema: dòng `CUST099` trong `customers` |
| 1:45–2:10 | `/admin/vehicles`: tra biển số `51K-567.89`. `/admin/promotions`: thêm rồi bỏ thành phố `DN` cho `GIAM20` | Tra biển số đi qua **materialized view** `vehicles_by_plate` (partition key là biển số, B05). Thêm/bớt phần tử của collection **set** `cities` bằng `cities + {'DN'}` / `cities - {'DN'}` | Panel: mã `B05` đọc bảng `vehicles_by_plate` (là view), lệnh `UPDATE promotions SET cities = ...` hiện trong cột CQL. DbSchema: cột `cities` của `promotions` có `DN` rồi mất |

Backup và restore nằm ở **bước 3.5** (cuối buổi) để dữ liệu demo không bị lùi giữa chừng.

### 9.3 Nghiệp vụ theo bài toán (2:10–4:10)

Dùng đúng kịch bản T01 đến T12 của `CASSANDRA.MD` §8 (T05 là cú nhận chuyến tranh chấp).

| Thời lượng | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|
| 2:10–2:25 | Phiên A: đăng xuất, đăng nhập `drv555`, `/driver`. Bật nhận chuyến: HCM, Q1, biển số `51K-567.89`, vĩ độ `10.7815`, kinh độ `106.6985` | T03. Tài xế phải nhập đúng biển số của mình, ứng dụng kiểm qua MV. Chuyển OFFLINE sang AVAILABLE bằng LWT `IF status = 'OFFLINE'`; mỗi tài xế chỉ nằm ở **một** khu vực | Panel: mã `APP20` trên `drivers` `[applied] True`, mã `T03` ghi `drivers_by_area` và `driver_locations`; dòng "So với WRITE_MATRIX[driver_online]" báo **đủ** (`drivers`, `drivers_by_area`, `driver_locations`). DbSchema: `drivers.status = AVAILABLE`, dòng DRV_555 trong `drivers_by_area` |
| 2:25–2:50 | Phiên B: đăng nhập `cust001`, `/customer/book`. Quận HCM / Q1, đón "456 Lê Duẩn, Q1", đến "Sân bay Tân Sơn Nhất, Tân Bình", `8.1` km, thanh toán MOMO, mã `GIAM20`. Bấm **Xem báo giá**, rồi **Đặt xe** | T04. Giá 81.000đ (công thức `max(15000, round((12000 + 8500*d)/1000)*1000)`), giảm 16.000đ, khách trả **65.000đ**. Lượt mã được **giữ lúc đặt xe** bằng LWT `IF used_count = n`, rồi chuyến được ghi bằng `IF NOT EXISTS`. Ghi nhiều bảng phi chuẩn hóa | Panel: mã `T07` trên `promotions` `[applied] True` (`used_count` 5 sang 6), mã `T04` trên `rides` `[applied] True`, rồi `T04` ghi `rides_by_customer` và `rides_by_area_date`. Dòng ma trận `book` báo đủ `rides`, `rides_by_customer`, `rides_by_area_date`, thêm `promotions`. DbSchema: dòng mới trong `rides`, `rides_by_customer`, `rides_by_area_date`; `promotions.used_count = 6` |
| 2:50–3:30 | **Tranh nhận chuyến (T05), hai trình duyệt.** Phiên B: đăng xuất `cust001`, đăng nhập `drv554` (đang AVAILABLE ở HCM / Q3). Cả hai phiên A (`drv555`) và B (`drv554`) mở `/driver/waiting?city=HCM&district=Q1`: đều thấy chuyến vừa đặt với nút **Nhận chuyến**. Bấm ở A, **ngay sau đó** bấm ở B (trang B vẫn là bản cũ) | Nhận chuyến chạy **hai tầng**: LWT trên `drivers` (`IF status = 'AVAILABLE'` sang BUSY) trước, rồi LWT trên `rides` (`IF status = 'REQUESTED'`). Chỉ một tài xế thắng. Bên thua không bị kẹt BUSY (nếu thua ở `rides` thì được trả về AVAILABLE) | **A thắng:** panel "CQL của thao tác vừa rồi" có mã `APP07` trên `drivers` `[applied] True`, mã `T05` trên `rides` `[applied] True`, rồi `T05` ghi `rides_by_customer`, `rides_by_area_date`, `rides_by_driver_month` và 11 lệnh xóa ở `drivers_by_area` (xóa tài xế khỏi mọi khu vực); ma trận `accept` báo đủ. **B thua:** thông báo "Chuyến đã được nhận hoặc không còn ở trạng thái chờ.", `drv554` vẫn AVAILABLE. DbSchema: `rides.status = ACCEPTED`, `driver_id = DRV_555`; DRV_555 `BUSY` và biến mất khỏi `drivers_by_area` |
| 3:30–3:55 | Phiên A (`drv555`): trang chi tiết chuyến, **Bắt đầu chuyến** (vĩ độ `10.7995`, kinh độ `106.6790`), rồi **Hoàn thành và thanh toán** (quận trả khách `TAN_BINH`, `10.8185` / `106.6588`) | T06 và T08. Mỗi bước là LWT `IF status = ... AND driver_id = ?`, nên tài xế khác không thể bắt đầu hay hoàn thành chuyến này (thử sẽ nhận 403). Hoàn thành ghi thanh toán, trả tài xế về AVAILABLE và đưa vào `drivers_by_area` tại Tân Bình | Panel: mã `T06` và `T08` trên `rides` `[applied] True`, mã `T08` ghi `payments_by_city_date`; ma trận `complete` đủ. Bảng `status_history` (map) của chuyến có đủ REQUESTED, ACCEPTED, ONGOING, COMPLETED. DbSchema: `payments_by_city_date` có dòng 65.000 |
| 3:55–4:10 | Phiên B: đăng xuất `drv554`, đăng nhập `cust001`, mở chuyến vừa đi, **Gửi đánh giá** 5 sao và hai tag. Thử gửi **lần hai** | T09. Đánh giá chỉ một lần mỗi chuyến nhờ LWT `IF rated_at = null` trên cột `rated_at` thêm bởi `06_app_migration.cql`. Điểm trung bình của DRV_555 sau đánh giá là **4,67**, cập nhật cả `drivers.rating` và `drivers_by_area.rating`. Lần hai bị từ chối | Panel: mã `APP14` trên `rides` `[applied] True`, mã `T09` ghi `ratings_by_driver`, `drivers` và `drivers_by_area`. Lần hai: "Chuyến này đã được đánh giá." DbSchema: `drivers.rating = 4.67` |

**Lưu ý khi nói về T05.** Hai lần bấm tay cách nhau vài giây nên bên thua bị chặn ngay ở bước đọc trạng thái chuyến, trước khi chạy LWT; vì vậy cú bấm của B không tạo dòng `[applied] False` ở T05. Dòng `[applied] False` hiện được ngay trong demo ở đăng ký trùng tên (9.1). Trường hợp hai LWT chạm nhau trong vài mili-giây (kết quả `lwt_lost`, tài xế thua được trả về AVAILABLE) được chứng minh bằng test `test_two_drivers_race_exactly_one_wins` trong `tests/integration/test_accept.py`; có thể chạy riêng bằng `.venv\Scripts\python -m pytest tests/integration/test_accept.py -q` nếu hội đồng muốn xem.

Nếu còn thời gian: khách hủy một chuyến khi còn REQUESTED (nút **Hủy chuyến**), thấy lượt mã `GIAM20` được trả lại bằng LWT; tài xế xem thu nhập tại
`/driver/income?yyyymm=202610`; khách xem lịch sử ở `/customer/rides`.

### 9.4 Chức năng hỗ trợ khác (4:10–4:50)

| Thời lượng | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|
| 4:10–4:30 | Phiên A: đăng nhập lại `admin`, `/admin/reports?city=HCM&day=2026-10-04`, rồi `/admin/areas` | Doanh thu ngày, 7 ngày và thống kê chuyến theo khu vực-ngày. Mỗi bảng được thiết kế riêng cho một truy vấn (`payments_by_city_date`, `rides_by_area_date`). Dữ liệu mẫu nằm ở ngày 04/10/2026 nên cần chọn đúng ngày | Panel: `SUM`/`COUNT` đọc trong **một partition** (city + ngày). DbSchema: bảng `payments_by_city_date` |
| 4:30–4:50 | `/admin/consistency`: kiểm tra mã chuyến vừa tạo. Ghi chú thêm: xuất CSV `/admin/export/payments.csv?city=HCM&day=2026-10-04` và GPS `/admin/drivers/DRV_551/track?day=2026-10-04` | Vì Cassandra không có transaction đa bảng, công cụ này so `rides` (nguồn đúng) với các bảng phụ và có nút Reconcile ghi lại từ `rides`. Cũng tìm tài xế kẹt BUSY | Kết quả "không lệch" cho chuyến vừa chạy xong; panel liệt kê các lệnh đọc từng bảng phụ |

## 3. Đặc trưng NoSQL của Cassandra (4:50–6:10)

| Thời lượng | Bước | Màn hình / thao tác | Nói gì | Thấy ở đâu |
|---|---|---|---|---|
| 4:50–5:00 | 3.1 | Quay lại các panel đã mở, chỉ vào một dòng LWT và dòng ma trận | Mỗi trang cho thấy câu CQL, bảng, **partition key**, consistency và `[applied]`; sau mỗi sự kiện, danh sách bảng bị ghi được so với ma trận ghi §3.7 | Panel "CQL đã chạy" |
| 5:00–5:20 | 3.2 | Phiên A: `/nosql`, mục **Truy vấn thiếu partition key**, bấm "Chạy câu truy vấn thiếu partition key" | Câu `SELECT ride_id FROM rides WHERE customer_id = 'CUST001'` lọc theo cột không phải khóa nên **bị Cassandra từ chối**; không dùng `ALLOW FILTERING` vì sẽ quét mọi partition. Cách đúng của thiết kế theo truy vấn là bảng phi chuẩn hóa `rides_by_customer` (B07) | Khung lỗi nguyên văn từ server 3.11.4: `Error from server: code=2200 [Invalid query] message="Cannot execute this query as it might involve data filtering and thus may have unpredictable performance. If you want to execute this query despite the performance unpredictability, use ALLOW FILTERING"`. Panel: dòng mã `A10` trên `rides` có nền đỏ |
| 5:20–5:35 | 3.3 | Cùng trang `/nosql`, cuộn xuống Collection và Clustering DESC | **map**: `status_history` của chuyến RIDE_1007; **list**: `tags` đánh giá (giữ thứ tự); **set**: `cities` của mã khuyến mãi (không trùng, tự sắp xếp). `rides_by_driver_month` khai báo `CLUSTERING ORDER BY (requested_at DESC, ...)` nên chuyến mới nhất nằm đầu mà không cần `ORDER BY` | Các bảng nhỏ ở mục Collection và Clustering DESC; DbSchema: kiểu cột `map`, `set`, `list` |
| 5:35–5:45 | 3.4 | Mục Catalog của `/nosql`; nhắc lại tra biển số ở 9.2 | Mọi câu CQL của ứng dụng đều là prepared statement có mã B/A/T/Q, mỗi câu ứng với một truy vấn đã thiết kế. Materialized view là một bảng khác do Cassandra tự đồng bộ khi ghi `vehicles` | Bảng catalog sinh tự động |
| 5:45–6:10 | 3.5 | Phiên A: `/admin/backup`. (1) **Tạo backup** nhãn `truocdemo`; xem file JSON mới trong `DoAn\app\backups`. (2) `/admin/customers`: **Xóa** `CUST099`; quay lại trang backup thấy số dòng `customers` giảm 1. (3) Chọn file `truocdemo`, bấm **Khôi phục** và xác nhận | Backup là JSON logical (`SELECT JSON` từng bảng thật), không cần `nodetool`. Khôi phục: kiểm toàn bộ file **trước** khi xóa gì, bật chế độ bảo trì chặn ghi, ghi bản an toàn `*_prerestore.json`, `TRUNCATE` 13 bảng rồi `INSERT ... JSON` lại. View `vehicles_by_plate` không bị ghi trực tiếp: `TRUNCATE vehicles` làm rỗng view (đã kiểm trên 3.11.4) và view tự dựng lại | Trang backup: bảng "Số dòng hiện tại" (kể cả dòng `vehicles_by_plate`) trở về như lúc backup, `customers` lại có `CUST099`. Thư mục backup có thêm file `..._prerestore.json`. DbSchema: Refresh `customers` |

## 4. Hạn chế và hướng phát triển (6:10–7:00)

| Thời lượng | Nội dung | Màn hình | Ghi chú |
|---|---|---|---|
| 6:10–6:40 | Hạn chế: ghi nhiều bảng **không nguyên tử** (có Reconcile); tài xế có thể kẹt BUSY nếu LWT nhận chuyến gặp `WriteTimeout` (có công cụ giải phóng); biển số duy nhất chỉ kiểm bằng đọc MV; tên phi chuẩn hóa trong bảng chuyến cũ là bản chụp lịch sử; một số trang quét toàn bảng; cờ bảo trì nằm trong bộ nhớ một tiến trình; file backup chứa `password_hash` và không phải ảnh chụp nhất quán giữa các bảng; không có CSRF token; trang lỗi 500 còn in thông điệp lỗi | Slide hạn chế | Danh sách đầy đủ ở mục "Giới hạn đã biết" của `README.md` |
| 6:40–7:00 | Hướng phát triển: chạy nhiều node và nhiều datacenter, thêm index/bảng cho các truy vấn quét, bản đồ và định vị thật, thanh toán thật, chuyển CSRF và kiểm soát lỗi 500 | Slide hướng phát triển | – |

## Sau khi quay

- Nếu cần chạy lại từ đầu, chạy lại bước 0.2 để nạp lại seed (cũng đưa `GIAM20` về `used_count = 5` và `drv555` về OFFLINE).
- Dọn snapshot sinh ra khi `TRUNCATE`: `nodetool clearsnapshot -- ride_booking_demo` (xem `README.md`, mục "Chạy test tự động").
- Mã khuyến mãi seed hết hạn lúc 23:59:59 ngày 31/12/2026: nếu quay sau ngày đó, sửa hạn ở `/admin/promotions` trước.
- **Chưa kiểm:** việc chạy đúng kịch bản này trên máy của từng thành viên; các tên nút DbSchema ở bước 0.5.
