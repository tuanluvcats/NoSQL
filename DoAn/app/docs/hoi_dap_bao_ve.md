# Hỏi đáp chuẩn bị bảo vệ đồ án (phần ứng dụng)

Tài liệu này để người trình bày trả lời câu hỏi của giảng viên về ứng dụng minh họa. Mỗi câu có câu trả lời ngắn (nói được trong 30 giây),
sau đó là chi tiết nếu bị hỏi tiếp. Thang điểm liên quan: mục 8 (kết nối CSDL với phần mềm), mục 9 (demo chức năng), mục 10 (trả lời câu hỏi).

## 1. Công nghệ của ứng dụng

### Jinja2 là gì?

**Trả lời ngắn:** Jinja2 là thư viện *template* của Python: một file HTML có chỗ trống, server điền dữ liệu vào rồi gửi trang HTML hoàn chỉnh cho trình duyệt.
Ứng dụng không cần viết JavaScript/React để hiển thị dữ liệu.

**Chi tiết:** Trong file `templates/*.html` có ba loại cú pháp:

- `{{ bien }}`: in giá trị. Ví dụ `{{ ride.fare }}` in giá chuyến. Jinja tự *escape* ký tự HTML (`<`, `>`), nên dữ liệu người dùng nhập không chèn được mã
  độc vào trang (chống XSS).
- `{% ... %}`: lệnh điều khiển. `{% if user.role == 'DRIVER' %}`, `{% for r in rides %}...{% endfor %}`.
- `{% extends "base.html" %}` và `{% block content %}`: kế thừa giao diện. `base.html` chứa thanh menu và panel "CQL đã chạy"; mỗi trang con chỉ viết phần
  nội dung riêng. `{% macro %}` là hàm nhỏ tái dùng (ví dụ macro `nav` vẽ một nút menu và tô sáng trang đang mở).

Luồng một request: trình duyệt gọi `GET /customer/rides` -> FastAPI chạy hàm trong `routes/customer.py` -> hàm gọi `services/...` -> `db/repo.py` chạy câu CQL
trên Cassandra -> kết quả (danh sách dict) đưa vào `render(request, "customer/history.html", {...})` -> Jinja2 tạo HTML -> trả về trình duyệt.

### FastAPI là gì, sao không dùng Flask/Django/React?

**Trả lời ngắn:** FastAPI là web framework Python, khai báo route bằng hàm có kiểu dữ liệu, tự kiểm tra form. Chọn vì một tiến trình, ít code, test dễ bằng
`TestClient`, và driver Cassandra chính thức là thư viện Python.

**Chi tiết:** Django có ORM cho SQL, không hợp Cassandra. React/SPA phải làm thêm một backend API và một frontend, nhiều việc hơn mà không thêm điểm NoSQL.
Route khai báo bằng `def` (không `async def`) vì `cassandra-driver` chạy đồng bộ; FastAPI tự chạy các hàm này trong thread pool.

### Ứng dụng kết nối Cassandra thế nào? (mục 8)

`db/session.py` tạo `Cluster` của `cassandra-driver` 3.30.1 với các biến môi trường `CASSANDRA_HOSTS`, `CASSANDRA_PORT`, `CASSANDRA_KEYSPACE`,
`CASSANDRA_LOCAL_DC`. Protocol v4 (Cassandra 3.11 không hỗ trợ v5), chính sách cân bằng tải `TokenAwarePolicy(DCAwareRoundRobinPolicy)` (gửi thẳng tới node giữ partition), consistency mặc định `LOCAL_QUORUM`,
LWT dùng `LOCAL_SERIAL`. Mọi câu CQL được *prepare* một lần (`db/catalog.py`, gắn mã B/A/T/Q giống báo cáo Word) rồi chạy lại với tham số, nên không bị
CQL injection. Trang **Kết nối** đọc `system.local` để hiện phiên bản thật.

## 2. Câu hỏi về NoSQL/Cassandra

### Vì sao một chuyến đi được ghi vào nhiều bảng?

Cassandra không có JOIN và chỉ truy vấn hiệu quả theo partition key. Vì vậy thiết kế *query-first*: mỗi câu hỏi nghiệp vụ có một bảng riêng, khóa theo đúng
điều kiện tìm. Ví dụ "lịch sử chuyến của khách" đọc `rides_by_customer` (khóa `customer_id`), "chuyến chờ ở quận" đọc `rides_by_area_date`
(khóa `city, district, ride_date`). Đổi lại, một sự kiện phải ghi nhiều bảng. Danh sách bảng phải ghi cho mỗi sự kiện nằm trong ma trận ghi
(`CASSANDRA.MD` §3.7, `domain/write_matrix.py`), và panel cuối mỗi trang đối chiếu những bảng thực sự đã ghi với ma trận này.

### Ghi nhiều bảng mà lỗi giữa chừng thì sao?

`rides` là nguồn đúng: luôn ghi `rides` trước (bằng LWT), chỉ khi `[applied] = True` mới ghi bảng phụ. Nếu bảng phụ lỗi, ứng dụng báo "partial" và trang
**Nhất quán** so từng bảng phụ với `rides` rồi ghi lại (reconcile). Không dùng BATCH vì báo cáo Word đã bỏ phần này và BATCH nhiều partition tốn kém.

### LWT là gì, dùng ở đâu?

Lightweight transaction là lệnh ghi có điều kiện (`IF NOT EXISTS`, `IF status = ...`) chạy bằng giao thức Paxos, đảm bảo chỉ một bên thắng khi nhiều người
cùng sửa một partition. Kết quả có cột `[applied]`; khi thua Cassandra trả kèm giá trị hiện tại, ứng dụng hiện ra cho người xem. Dùng ở:

- Đăng ký: `INSERT INTO user_accounts ... IF NOT EXISTS` (không trùng tên đăng nhập).
- Nhận chuyến: `drivers IF status = 'AVAILABLE'` rồi `rides IF status = 'REQUESTED'`. Hai tài xế bấm cùng lúc thì đúng một người nhận được; người thua ở
  `rides` được trả về `AVAILABLE`.
- Chuyển trạng thái chuyến: `IF status = 'ACCEPTED' AND driver_id = ?`, ... nên không thể nhảy sai thứ tự.
- Mã khuyến mãi: đọc `used_count = n` rồi `UPDATE ... SET used_count = n+1 IF used_count = n`, thử lại khi thua, dừng khi đạt `usage_limit`.
  Không dùng kiểu `counter` vì counter không có điều kiện, không chặn được vượt lượt.
- Đánh giá: `UPDATE rides SET rated_at = ? IF rated_at = null AND status = 'COMPLETED'` nên mỗi chuyến chỉ đánh giá một lần.

LWT tốn khoảng 4 vòng mạng nên chỉ dùng ở chỗ có tranh chấp; vị trí GPS, thanh toán dùng ghi thường.

### Last-write-wins là gì, ứng dụng xử lý thế nào?

Mỗi ô dữ liệu trong Cassandra có timestamp; hai lệnh ghi cùng ô thì lệnh có timestamp lớn hơn thắng, không phụ thuộc lệnh nào tới trước. Ứng dụng dùng điều
này khi cập nhật điểm tài xế: `UPDATE drivers USING TIMESTAMP ? SET rating = ?`, mốc lấy ngay trước lệnh đọc `AVG(stars)`. Hai khách đánh giá cùng lúc thì
lần đọc sau (thấy đủ hai đánh giá) luôn thắng, nên điểm không bị ghi đè bằng số cũ.

### Materialized view dùng ở đâu?

`vehicles_by_plate` là MV của bảng `vehicles`, khóa theo biển số, để tra xe bằng biển số khi tài xế bật nhận chuyến và trong trang quản trị xe. Ứng dụng
không bao giờ ghi trực tiếp vào MV; Cassandra tự cập nhật từ bảng gốc.

### Kiểu dữ liệu tập hợp (map/set/list) thể hiện ở đâu?

`promotions.cities` là `set<text>` (thêm/bớt thành phố bằng `cities + {...}` và `cities - {...}`), `rides.status_history` là `map<timestamp, text>` (lịch sử
trạng thái hiện ở trang chi tiết chuyến), `ratings_by_driver.tags` là `list<text>`.

### Truy vấn thiếu partition key thì sao?

Trang **NoSQL** có nút chạy thử một câu như vậy; Cassandra từ chối và đòi `ALLOW FILTERING`. Ứng dụng không dùng `ALLOW FILTERING` vì nó quét mọi node.
Các trang quản trị cần liệt kê toàn bộ (tài khoản, khách) chấp nhận quét bảng nhỏ ở quy mô dữ liệu mẫu và ghi rõ giới hạn này trong README.

### Backup/restore làm thế nào? (mục 9.2, mục 6)

Trang **Backup** xuất toàn bộ keyspace ra file JSON (SELECT từng bảng). Khôi phục: bật chế độ bảo trì chặn mọi thao tác ghi, `TRUNCATE` từng bảng gốc rồi
`INSERT` lại, không ghi vào MV (đã thử: TRUNCATE bảng gốc làm rỗng MV và MV tự dựng lại). Ngoài ra thư mục `cassandra/scripts` có `nodetool snapshot`
và `COPY TO/FROM` CSV cho phần làm trên công cụ.

## 3. Câu hỏi về logic và giao diện

- **Gửi form đặt xe hai lần có tạo hai chuyến không?** Không. Mã chuyến sinh lúc mở form và `INSERT ... IF NOT EXISTS`; lần hai không applied.
- **Tài xế đang chở khách có tắt nhận chuyến được không?** Không; nút tắt ẩn khi BUSY, server cũng từ chối. Trang tài xế hiện link tới chuyến đang chạy.
- **Khóa tài khoản có tác dụng ngay không?** Có, trạng thái tài khoản được kiểm ở mỗi request. Không khóa được admin cuối cùng. Khóa tài xế thì xóa họ khỏi
  `drivers_by_area`.
- **Xóa khách đã có chuyến?** Bị chặn (lịch sử chuyến sẽ mồ côi); dùng khóa tài khoản. Mọi nút xóa/khóa hỏi xác nhận trước.
- **Sao mỗi trang có panel CQL?** Để người xem thấy câu CQL thật, bảng, partition key, consistency level, `[applied]`. Đây là phần "thể hiện NoSQL".
- **Giao diện có kiểm tra trùng chức năng không?** Có test tự động (`tests/unit/test_ux_rules.py`): trang chủ không có link lặp, một nhãn không dẫn tới hai
  nơi, các nút trên một trang có tên khác nhau, nút xóa/khóa phải hỏi lại. Menu gom theo nhóm (Người dùng, Dữ liệu, Nghiệp vụ, Hệ thống) đúng các mục 9.1-9.4.

## 4. Kiểm thử

Khoảng 600 test pytest: unit test dùng `FakeDb` (không cần Cassandra) kiểm thứ tự ghi bảng và nhánh LWT thua; integration test chạy trên keyspace
`ride_booking_test` (từ chối chạy nếu tên không kết thúc bằng `_test`) gồm kịch bản T01-T12 cho đúng kết quả `CASSANDRA.MD` §8 (khách trả 65000,
điểm tài xế 4.67), hai luồng tranh nhận cùng chuyến, hai luồng tranh mã khuyến mãi, backup rồi restore.

### Có số liệu chứng minh không, so với cách làm nào?

Có (`docs/ket_qua_do_hieu_nang.md`, đo bằng query trace phía server). Baseline là cách làm thông thường "đọc trạng thái rồi UPDATE": 8 tài xế cùng nhận
một chuyến, 30 vòng, cả 30 vòng đều có từ 2 người "nhận được"; dùng LWT thì cả 30 vòng đúng 1 người. Cái giá: LWT khoảng 9,8 ms so với 0,8 ms của ghi
thường. Đọc theo partition key giữ khoảng 1 ms khi bảng tăng lên 20.036 chuyến, còn `ALLOW FILTERING` tăng từ 3,6 ms lên khoảng 100 ms: đó là lý do thiết
kế theo truy vấn. Độ bao phủ mã của bộ test là 89 %.

## 5. Tài liệu tham khảo đã đối chiếu

- DataStax, *How do I accomplish lightweight transactions with linearizable consistency?* (Cassandra 3.0): LWT giới hạn trong một partition, 4 vòng mạng,
  không trộn ghi LWT và ghi thường trên cùng ô. https://docs.datastax.com/en/cassandra/3.0/cassandra/dml/dmlLtwtTransactions.html
- Apache Cassandra, *Data modeling: defining database schema* (thiết kế theo truy vấn). https://cassandra.apache.org/doc/4.0/data_modeling/data_modeling_schema.html
- Planet Cassandra, trường hợp Lyft dùng Cassandra lưu yêu cầu chuyến, phân công tài xế, hoàn thành chuyến. https://planetcassandra.org/usecases/lyft/181
- Uber Engineering, *How Uber optimized Cassandra operations at scale* (tải LWT nặng làm tăng lỗi, lý do chỉ dùng LWT ở chỗ cần).
  https://www.uber.com/en-US/blog/how-uber-optimized-cassandra-operations-at-scale/
- Pythian, *Lightweight transactions in Cassandra*. https://www.pythian.com/blog/lightweight-transactions-cassandra
- Open Mobility Foundation, *Mobility Data Specification* (chuẩn dữ liệu chuyến và trạng thái phương tiện; tham khảo cách mô hình hóa máy trạng thái).
  https://github.com/openmobilityfoundation/mobility-data-specification
- iamSahdeep, *fu_uber* (ứng dụng mẫu Flutter kiểu Uber; tham khảo luồng màn hình khách/tài xế). https://github.com/iamSahdeep/fu_uber
