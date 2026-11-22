"""Sinh Chương 5 (Word) từ các file .cql, dùng chính file Word giữa kỳ làm khuôn định dạng.

Chạy (PowerShell, tại thư mục gốc repo):
    $env:PYTHONUTF8 = 1; python DoAn\\cassandra\\tools\\build_chuong5.py
Kết quả: DoAn\\Chuong5_CSDL_Cassandra.docx (không sửa file Word giữa kỳ).
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).parent))
from docx_lib import Builder, W  # noqa: E402
from docx.oxml import parse_xml  # noqa: E402

DORAN = Path(__file__).resolve().parents[2]
DRAFT = DORAN / 'Báo cáo giữa kỳ NoSQL về DbSchema và Apache Cassandra.docx'
OUT = DORAN / (sys.argv[1] if len(sys.argv) > 1 else 'Chuong5_CSDL_Cassandra.docx')
CQL = DORAN / 'cassandra'

# ----------------------------------------------------------------------------------------
# Tài liệu tham khảo (số thứ tự được gán theo lần xuất hiện đầu tiên trong chương)
# ----------------------------------------------------------------------------------------
from refs import REFS, PRE_ORDER  # noqa: E402


def parse_cql(name):
    blocks, cur = {}, None
    for line in (CQL / name).read_text(encoding='utf8').replace('\r\n', '\n').split('\n'):
        m = re.match(r'^-- \[(\w+)\]', line)
        if m:
            cur = m.group(1)
            blocks[cur] = []
            continue
        if cur and not line.startswith('--'):
            blocks[cur].append(line)
    return {k: '\n'.join(v).strip() for k, v in blocks.items()}


BASIC = parse_cql('03_queries_basic.cql')
ADV = parse_cql('04_queries_advanced.cql')
TX = parse_cql('05_transactions.cql')
PROJ = 'D:\\NOSQL\\cassandra'   # thư mục chứa file .cql trên máy (giả định, sửa theo máy)

b = Builder(REFS, PRE_ORDER)

# =========================================================================================
b.chapter('CHƯƠNG 5: THIẾT KẾ VÀ XÂY DỰNG CƠ SỞ DỮ LIỆU CASSANDRA CHO HỆ THỐNG QUẢN LÝ DỮ LIỆU ĐẶT XE CÔNG NGHỆ')

b.para('Chương này trình bày phần xây dựng cơ sở dữ liệu của đề tài: phân tích nghiệp vụ, thiết kế bảng theo truy vấn, tạo keyspace, nạp dữ liệu, '
       'thực hiện truy vấn cơ bản và nâng cao, nhập/xuất dữ liệu, sao lưu và khôi phục. Mọi lệnh đều được chạy thật trên Cassandra, '
       'kết quả được chụp lại từ DbSchema và từ cqlsh. Cách thiết kế bám theo phương pháp “thiết kế theo truy vấn” (query-first) trong slide môn học {{slide}} '
       'và trong sách Cassandra: The Definitive Guide {{book|tr. 86–100}}.')

# -----------------------------------------------------------------------------------------
b.h2('5.1. Môi trường thực nghiệm')
b.h3('5.1.1. Cấu hình')
b.para('Môi trường được cài đặt theo tài liệu hướng dẫn thực hành {{guide|tr. 37–42}}. Cấu hình máy tối thiểu để cài Cassandra trên Windows 10 trở lên là 2 nhân, 8 GB RAM và 5 GB ổ đĩa. Ngoài DbSchema, đề tài không dùng thêm công cụ GUI nào khác cho Cassandra.')
b.bullets([
    '**Hệ quản trị:** Apache Cassandra 3.11.4 (gói nhị phân `apache-cassandra-3.11.4-bin`), giải nén vào `c:\\apache-cassandra-3.11.4`. Đây cùng nhánh 3.x với máy đã chụp Hình 4.1 ở Chương 4.',
    '**Java:** JDK 8 (bản 8u231, 64 bit).',
    '**Python:** Python 2.7.17 (64 bit), vì `cqlsh` của Cassandra 3.11 chạy bằng Python 2.7.',
    '**Cluster:** một node cục bộ, datacenter `datacenter1`, cổng CQL 9042.',
    '**Công cụ GUI:** DbSchema 10.5.2 (bản dùng thử), kết nối theo phương thức Standard tới `localhost:9042` như Hình 2.6.',
    '**Công cụ dòng lệnh:** `cqlsh` và `nodetool` nằm trong thư mục `bin` của Cassandra. Mở Command Prompt rồi chuyển vào thư mục này, hoặc thêm thư mục này vào biến môi trường PATH.',
])
b.h3('5.1.2. Khởi động và kiểm tra')
b.step(1, 'Mở Command Prompt, chuyển vào thư mục `bin` của Cassandra rồi khởi động dịch vụ {{guide|tr. 41}}. Giữ cửa sổ này mở trong suốt thời gian làm việc.')
b.code('cd c:\\apache-cassandra-3.11.4\\bin\ncassandra')
b.figure('Khởi động dịch vụ Cassandra.', 'Chạy 2 lệnh trên, chụp cửa sổ khi log khởi động kết thúc', 'Dòng cuối của log có “Node localhost/127.0.0.1 state jump to NORMAL”', 'Command Prompt', 'Bắt buộc')
b.step(2, 'Mở một cửa sổ Command Prompt thứ hai, vào thư mục `bin` và kiểm tra trạng thái node.')
b.code('nodetool status')
b.figure('Trạng thái node Cassandra.', 'Chạy lệnh nodetool status', 'Dòng bắt đầu bằng UN (Up/Normal), Datacenter: datacenter1', 'Command Prompt', 'Bắt buộc')
b.step(3, 'Kiểm tra phiên bản và tên cluster.')
b.code('cqlsh -e "SHOW VERSION; SELECT cluster_name, data_center, release_version FROM system.local;"')
b.figure('Phiên bản Cassandra và thông tin cluster.', 'Chạy lệnh trên, chụp kết quả', 'Cassandra 3.11.4, data_center = datacenter1', 'Command Prompt', 'Bắt buộc')
b.para('Nếu màn hình console hiển thị sai dấu tiếng Việt thì chạy các truy vấn trong DbSchema. Trước khi dùng `cqlsh` để ghi kết quả ra file (lệnh `DESCRIBE`), đặt `set PYTHONIOENCODING=utf-8` trong cùng cửa sổ, vì `cqlsh` của Cassandra 3.11 chạy bằng Python 2.7.')
b.step(4, 'Mở DbSchema, kết nối tới Cassandra như Chương 2 (Standard, This computer, default port).')
b.figure('Kết nối DbSchema tới Cassandra.', 'Mở DbSchema, vào hộp thoại kết nối, bấm Test Connection', 'Thông báo kết nối thành công', 'DbSchema', 'Nên có')

# -----------------------------------------------------------------------------------------
b.h2('5.2. Phân tích nghiệp vụ')
b.h3('5.2.1. Tác nhân và chức năng')
b.para('Hệ thống quản lý dữ liệu đặt xe công nghệ phục vụ bốn nhóm người dùng, mỗi nhóm có các chức năng chính sau.')
b.bullets([
    '**Khách hàng:** đăng ký, đăng nhập, xem hồ sơ, đặt xe, áp mã khuyến mãi, xem lịch sử chuyến, hủy chuyến và đánh giá tài xế.',
    '**Tài xế:** đăng nhập, bật/tắt trạng thái nhận chuyến, gửi vị trí GPS, nhận chuyến, bắt đầu/kết thúc chuyến, xem thu nhập tháng và đánh giá.',
    '**Điều phối viên:** xem các chuyến trong ngày theo khu vực, tìm tài xế đang rảnh quanh khu vực, theo dõi vị trí tài xế.',
    '**Quản trị viên:** khóa/mở tài khoản, quản lý danh mục khách hàng, tài xế, xe, khuyến mãi, xem báo cáo doanh thu và thống kê chuyến, sao lưu và khôi phục dữ liệu.',
])
b.h3('5.2.2. Vòng đời của một chuyến đi')
b.para('Một chuyến đi đi qua các trạng thái sau; mỗi lần chuyển trạng thái là một thao tác có điều kiện nên được kiểm soát bằng giao dịch nhẹ (LWT) ở mục 5.8.')
b.bullets([
    '`REQUESTED` (khách vừa đặt) chuyển sang `ACCEPTED` khi một tài xế nhận chuyến, hoặc sang `CANCELLED` khi khách hủy.',
    '`ACCEPTED` chuyển sang `ONGOING` khi tài xế đón khách, hoặc sang `CANCELLED` khi khách hay tài xế hủy.',
    '`ONGOING` chuyển sang `COMPLETED` khi trả khách và thanh toán. Sau đó khách có thể đánh giá tài xế.',
])
b.h3('5.2.3. Danh sách truy vấn của ứng dụng')
b.para('Theo phương pháp query-first, bước đầu tiên là liệt kê các truy vấn mà ứng dụng cần trả lời {{slide}} {{book|tr. 86}}. Bảng dưới đây gồm 18 truy vấn Q1–Q18 cùng điều kiện tìm kiếm của từng truy vấn.')
b.table(
    ['Mã', 'Truy vấn nghiệp vụ', 'Điều kiện truy vấn', 'Bảng phục vụ'],
    [
        ['Q1', 'Đăng nhập; đăng ký tài khoản không trùng username', '`username =`', '`user_accounts`'],
        ['Q2', 'Xem hồ sơ khách hàng', '`customer_id =`', '`customers`'],
        ['Q3', 'Xem hồ sơ tài xế (điểm, trạng thái)', '`driver_id =`', '`drivers`'],
        ['Q4', 'Xem xe theo mã, theo biển số, theo tài xế', '`vehicle_id =`, `license_plate =`, `driver_id =`', '`vehicles`, `vehicles_by_plate`'],
        ['Q5', 'Tìm tài xế đang rảnh trong một khu vực', '`city =`, `district =`', '`drivers_by_area`'],
        ['Q6', 'Đặt chuyến mới, không tạo trùng khi gửi lại', '`ride_id =` (IF NOT EXISTS)', '`rides`'],
        ['Q7', 'Nhận chuyến: chỉ một tài xế thắng', '`ride_id =` (IF status)', '`rides`'],
        ['Q8', 'Xem chi tiết một chuyến', '`ride_id =`', '`rides`'],
        ['Q9', 'Lịch sử chuyến của khách, mới nhất trước, lọc theo ngày', '`customer_id =`, `ride_date` trong khoảng', '`rides_by_customer`'],
        ['Q10', 'Lịch sử chuyến và thu nhập tháng của tài xế', '`driver_id =`, `yyyymm =`', '`rides_by_driver_month`'],
        ['Q11', 'Các chuyến trong ngày của một khu vực', '`city =`, `district =`, `ride_date =`', '`rides_by_area_date`'],
        ['Q12', 'Doanh thu ngày theo phương thức thanh toán', '`city =`, `pay_date =`', '`payments_by_city_date`'],
        ['Q13', 'Số chuyến đặt/hoàn thành/hủy theo ngày', '`city =`, `yyyymm =`', '`ride_stats_by_city`'],
        ['Q14', 'Vị trí GPS mới nhất và lộ trình trong ngày của tài xế', '`driver_id =`, `day =`', '`driver_locations`'],
        ['Q15', 'Đánh giá của tài xế, mới nhất trước; điểm trung bình', '`driver_id =`', '`ratings_by_driver`'],
        ['Q16', 'Kiểm tra mã khuyến mãi; tăng lượt dùng an toàn', '`promo_code =`', '`promotions`'],
        ['Q17', 'Đánh giá mới nhất của mỗi tài xế', 'toàn bảng, `PER PARTITION LIMIT 1`', '`ratings_by_driver`'],
        ['Q18', 'Duyệt toàn bộ danh sách khách hàng theo trang', '`token(customer_id) >`', '`customers`'],
    ],
    [750, 3300, 2450, 2550],
    'Danh sách truy vấn của ứng dụng (Q1–Q18).')

# -----------------------------------------------------------------------------------------
b.h2('5.3. Thiết kế cơ sở dữ liệu theo truy vấn')
b.h3('5.3.1. Nguyên tắc thiết kế')
b.para('Khác với CSDL quan hệ, nơi thiết kế bắt đầu từ các thực thể rồi mới viết truy vấn, Cassandra thiết kế bắt đầu từ truy vấn {{slide}}. Các nguyên tắc áp dụng trong đề tài như sau.')
b.bullets([
    '**Mỗi truy vấn được phục vụ bởi một bảng** có khóa chính phù hợp. Dữ liệu được lặp lại (phi chuẩn hóa) giữa các bảng thay vì dùng JOIN, vì Cassandra không hỗ trợ JOIN {{book|tr. 83}}.',
    '**Khóa phân vùng (partition key)** quyết định dữ liệu nằm ở node nào. Mọi truy vấn phải chỉ định đủ khóa phân vùng để chỉ đọc một partition.',
    '**Khóa gom nhóm (clustering column)** quyết định thứ tự các dòng trong partition, dùng cho `ORDER BY` và lọc theo khoảng.',
    '**Kích thước partition** được ước lượng để tránh partition quá lớn. Sách khuyến nghị không quá 100.000 ô (cell) mỗi partition {{book|tr. 97}}; nếu có nguy cơ vượt thì thêm “bucket” (tháng, ngày, khu vực) vào khóa phân vùng.',
    '**Ký hiệu Chebotko:** K là khóa phân vùng, C↑ và C↓ là cột gom nhóm tăng và giảm dần, S là cột static {{book|tr. 88–89}}.',
])
b.h3('5.3.2. Thiết kế vật lý')
b.para('Từ 18 truy vấn, đề tài giữ nguyên 4 bảng đã có trong báo cáo giữa kỳ (`customers`, `drivers`, `vehicles`, `rides_by_customer`) để các hình đã chụp vẫn đúng, và bổ sung 10 bảng cùng 1 materialized view. Bảng dưới đây tổng hợp khóa chính của từng bảng.')
b.table(
    ['Bảng', 'Khóa phân vùng (K)', 'Cột gom nhóm (C)', 'Truy vấn'],
    [
        ['`customers`, `drivers`, `vehicles` (cũ)', '`customer_id` / `driver_id` / `vehicle_id`', '—', 'Q2, Q3, Q4'],
        ['`rides_by_customer` (cũ)', '`customer_id`', '`ride_date` ↑, `ride_id` ↑', 'Q9'],
        ['`vehicles_by_plate` (view)', '`license_plate`', '`vehicle_id` ↑', 'Q4'],
        ['`user_accounts`', '`username`', '—', 'Q1'],
        ['`rides`', '`ride_id`', '—', 'Q6, Q7, Q8'],
        ['`rides_by_driver_month`', '`driver_id`, `yyyymm`', '`requested_at` ↓, `ride_id` ↑', 'Q10'],
        ['`rides_by_area_date`', '`city`, `district`, `ride_date`', '`requested_at` ↓, `ride_id` ↑', 'Q11'],
        ['`drivers_by_area`', '`city`, `district`', '`driver_id` ↑', 'Q5'],
        ['`driver_locations`', '`driver_id`, `day`', '`ts` ↓', 'Q14'],
        ['`ratings_by_driver`', '`driver_id`', '`rated_at` ↓, `ride_id` ↑', 'Q15, Q17'],
        ['`payments_by_city_date`', '`city`, `pay_date`', '`payment_method` ↑, `paid_at` ↓, `ride_id` ↑', 'Q12'],
        ['`promotions`', '`promo_code`', '—', 'Q16'],
        ['`ride_stats_by_city` (counter)', '`city`, `yyyymm`', '`ride_date` ↑', 'Q13'],
    ],
    [2500, 2300, 2950, 1300],
    'Khóa chính của các bảng trong keyspace ride_booking.')
b.figure('Sơ đồ Chebotko rút gọn: truy vấn và bảng phục vụ.', 'Vẽ sơ đồ (draw.io hoặc diagram của DbSchema): mỗi hộp là một bảng có K, C↑/C↓, S; mũi tên từ truy vấn Q1–Q18 tới bảng', 'Đủ 14 bảng và 1 view, mỗi mũi tên ghi mã Qn', 'draw.io / DbSchema', 'Nên có')
b.h3('5.3.3. Giải thích các lựa chọn chính')
b.bullets([
    '**`rides_by_customer`** giữ khóa `((customer_id), ride_date, ride_id)` như đã có. Khách dùng nhiều nhất cũng chỉ vài nghìn chuyến nên partition không phình quá lớn. Đọc “mới nhất trước” bằng `ORDER BY ride_date DESC, ride_id DESC`, vì Cassandra cho phép đảo ngược toàn bộ thứ tự gom nhóm.',
    '**`rides`** có khóa là `ride_id`, một dòng mỗi partition. Bảng này là nơi duy nhất ghi nhận trạng thái chuyến bằng LWT, nên mọi bảng khác chỉ là bản sao đọc nhanh.',
    '**`rides_by_driver_month`** thêm tháng vào khóa phân vùng để partition của một tài xế không tăng mãi. Hai cột `driver_name` và `vehicle_plate` là cột static, chỉ lưu một lần cho cả partition {{book|tr. 101}}.',
    '**`rides_by_area_date`** dùng khóa phân vùng gồm thành phố, quận và ngày, nên mỗi partition chỉ chứa các chuyến của một quận trong một ngày.',
    '**`drivers_by_area`** chỉ chứa tài xế đang rảnh. Nhận chuyến thì xóa dòng, xong chuyến thì ghi lại dòng kèm `USING TTL 300`; tài xế mất tín hiệu quá 5 phút sẽ tự biến mất khỏi danh sách. Không đặt `status` hay `rating` vào khóa chính vì cột khóa chính không thể `UPDATE`.',
    '**`driver_locations`** chia partition theo ngày, đặt TTL mặc định 24 giờ và dùng chiến lược nén theo cửa sổ thời gian (TWCS) phù hợp dữ liệu có TTL.',
    '**`ride_stats_by_city`** là bảng counter, chỉ dùng cho số đếm chuyến. Counter không idempotent (thử lại khi lỗi có thể cộng trùng) {{book|tr. 71–72}}, nên tiền không lưu bằng counter mà lấy từ `payments_by_city_date`.',
    '**`vehicles_by_plate`** là materialized view, kỹ thuật tối ưu truy vấn của slide Chương 3 {{slide}} {{book|tr. 148}}. Cassandra tự giữ view đồng bộ với bảng gốc, nhưng báo đây là tính năng thử nghiệm, nên chỉ dùng cho bảng nhỏ này. Tra xe theo tài xế dùng secondary index trên bảng nhỏ {{book|tr. 144}}.',
])
b.h3('5.3.4. Ước lượng kích thước partition')
b.para('Theo công thức trong sách {{book|tr. 97}}, số ô của một partition là Nv = Nr × (Nc − Npk − Ns) + Ns, trong đó Nr là số dòng, Nc số cột, Npk số cột khóa chính và Ns số cột static. Với giả định một hãng đặt xe ở giai đoạn đầu (10.000 chuyến mỗi ngày mỗi thành phố, khu vực đông nhất chiếm 20%), kết quả cho trong bảng dưới đây: mọi bảng đều dưới ngưỡng 100.000 ô.')
b.table(
    ['Bảng', 'Nr', 'Nc', 'Npk', 'Ns', 'Nv', 'Nhận xét'],
    [
        ['`rides_by_customer`', '7.300', '8', '3', '0', '36.500', 'Khách dùng nhiều, 5 năm'],
        ['`rides_by_driver_month`', '1.240', '12', '4', '2', '7.442', 'Bucket tháng'],
        ['`rides_by_area_date`', '2.000', '12', '5', '0', '14.000', 'Bucket khu vực + ngày'],
        ['`drivers_by_area`', '1.000', '9', '3', '0', '6.000', 'Chỉ tài xế đang rảnh'],
        ['`driver_locations`', '11.520', '5', '3', '0', '23.040', 'Bucket ngày, TTL 24 giờ'],
        ['`ratings_by_driver`', '7.300', '7', '3', '0', '29.200', 'Mỗi năm; nên thêm bucket năm sau ~3 năm'],
        ['`payments_by_city_date`', '10.000', '10', '5', '0', '50.000', 'Thêm quận/giờ vào khóa nếu vượt ~20.000 giao dịch/ngày'],
    ],
    [2150, 800, 600, 600, 500, 900, 3500],
    'Ước lượng số ô trong một partition.')
b.h3('5.3.5. Các phương án đã cân nhắc nhưng không chọn')
b.bullets([
    'Đặt `status` và `rating` vào khóa chính của bảng tài xế rảnh: mỗi lần đổi phải xóa dòng cũ rồi ghi dòng mới, và partition `AVAILABLE` dễ thành điểm nóng.',
    'Lưu vị trí GPS theo `((driver_id), ts)` không có bucket: partition của mỗi tài xế phình mãi, và dữ liệu hết hạn TTL thành tombstone tồn tại tối thiểu `gc_grace_seconds` (10 ngày).',
    'Dùng `ALLOW FILTERING` trên toàn bảng: buộc quét toàn cụm; chỉ dùng khi đã cố định khóa phân vùng (xem A01 ở mục 5.7).',
])

# -----------------------------------------------------------------------------------------
b.h2('5.4. Tạo cơ sở dữ liệu')
b.para('Keyspace, hai kiểu dữ liệu người dùng định nghĩa (UDT), 14 bảng, một chỉ mục phụ và một materialized view được tạo bằng file `01_schema.cql`. Cú pháp `CREATE KEYSPACE` và `CREATE TABLE` theo hướng dẫn thực hành {{guide}}; mọi lệnh đều có `IF NOT EXISTS` nên chạy lại không lỗi và không thay đổi bốn bảng đã có.')
b.code("CREATE KEYSPACE IF NOT EXISTS ride_booking\n  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};")
b.para('`SimpleStrategy` với `replication_factor = 1` phù hợp cluster một node dùng cho học tập. Khi triển khai thật nhiều datacenter thì dùng `NetworkTopologyStrategy` và hệ số sao lưu từ 3 {{book|tr. 48, 115}}.')
b.step(1, 'Chạy file tạo CSDL.')
b.code('cqlsh -f ' + PROJ + '\\01_schema.cql')
b.figure('Chạy file 01_schema.cql.', 'Chạy lệnh trên, chụp màn hình sau khi chạy', 'Không có lỗi; có cảnh báo “Materialized views are experimental…” là bình thường', 'Command Prompt', 'Bắt buộc')
b.step(2, 'Liệt kê các bảng của keyspace.')
b.code('cqlsh -e "USE ride_booking; DESCRIBE TABLES;"')
b.figure('Danh sách 14 bảng của keyspace ride_booking.', 'Chạy lệnh trên, chụp kết quả', 'Đủ 14 bảng: promotions, customers, vehicles, rides_by_area_date, driver_locations, drivers, ...', 'Command Prompt', 'Bắt buộc')
b.step(3, 'Xem định nghĩa keyspace và một bảng để kiểm tra khóa chính.')
b.code('cqlsh -e "DESCRIBE KEYSPACE ride_booking"\n' + 'cqlsh -e "DESCRIBE TABLE ride_booking.rides_by_driver_month"')
b.figure('Định nghĩa keyspace ride_booking.', 'Chụp phần đầu kết quả DESCRIBE KEYSPACE', 'Dòng CREATE KEYSPACE ... SimpleStrategy, replication_factor 1', 'Command Prompt', 'Bắt buộc')
b.figure('Định nghĩa bảng rides_by_driver_month.', 'Chụp kết quả DESCRIBE TABLE', 'PRIMARY KEY ((driver_id, yyyymm), requested_at, ride_id), cột STATIC, CLUSTERING ORDER BY', 'Command Prompt', 'Nên có')
b.step(4, 'Trong DbSchema, mở file `test1.dbs`, chọn Refresh/Synchronize Model and Database để nhập các bảng mới vào model, giống Mục 3.4.')
b.figure('DbSchema phát hiện 10 bảng mới và materialized view.', 'Mở Synchronize Model and Database, chụp danh sách difference', 'Các bảng present trong Database, absent trong Model', 'DbSchema', 'Bắt buộc')
b.step(5, 'Kéo các bảng vào diagram, tạo Virtual Foreign Key giữa `rides.customer_id` và `customers.customer_id`, `rides.driver_id` và `drivers.driver_id`, `ratings_by_driver.driver_id` và `drivers.driver_id`, `payments_by_city_date.ride_id` và `rides.ride_id`.')
b.figure('Diagram của keyspace ride_booking sau khi bổ sung bảng.', 'Sắp xếp diagram cho dễ nhìn rồi chụp', 'Thấy các bảng mới cùng các đường Virtual Foreign Key', 'DbSchema', 'Bắt buộc')

# -----------------------------------------------------------------------------------------
b.h2('5.5. Nạp dữ liệu mẫu')
b.h3('5.5.1. Bộ dữ liệu')
b.para('Dữ liệu mô phỏng một tuần hoạt động từ 28/09 đến 04/10/2026 tại TP.HCM (28 chuyến) và Hà Nội (8 chuyến). Thời điểm hiện tại của dữ liệu là 10:00 sáng 04/10/2026, khi đó có một chuyến chờ tài xế, một chuyến đã được nhận, hai chuyến đang chạy và sáu tài xế đang rảnh. Dữ liệu được sinh bằng script `gen_data.py` rồi kiểm tra tự động: tài xế không có hai chuyến chồng giờ, mã khuyến mãi đúng thành phố và đủ cước tối thiểu, điểm trung bình của tài xế khớp các đánh giá.')
b.para('Tổng cộng bộ dữ liệu có **285 dòng** trong 14 bảng; số dòng của từng bảng nằm ở phụ lục của chương.')
b.h3('5.5.2. Các bước thực hiện')
b.step(1, 'Nếu bảng còn dữ liệu ngẫu nhiên do Data Generator sinh ra ở Mục 3.5 (ví dụ `vehicle_id = ‘John is shopping. Tony is shopping.’`), dọn sạch trước bằng `99_reset_data.cql`. `TRUNCATE` còn tự tạo snapshot trước khi xóa nên luôn có đường lui {{book|tr. 292}}.')
b.code('cqlsh -f ' + PROJ + '\\99_reset_data.cql')
b.figure('Dọn dữ liệu cũ bằng 99_reset_data.cql.', 'Chỉ làm nếu bảng còn dữ liệu Data Generator; chụp kết quả chạy', 'Chạy xong không báo lỗi', 'PowerShell', 'Tùy chọn')
b.step(2, 'Nạp dữ liệu mẫu. Mỗi chuyến đi được ghi vào bốn bảng phi chuẩn hóa cùng lúc trong một logged BATCH để các bảng nhất quán với nhau {{book|tr. 194–196}}.')
b.code('cqlsh -f ' + PROJ + '\\02_data.cql')
b.figure('Nạp dữ liệu mẫu bằng 02_data.cql.', 'Chạy lệnh trên, chụp kết quả', 'Không có lỗi; các câu có IF NOT EXISTS in [applied] True', 'Command Prompt', 'Bắt buộc')
b.para('Cấu trúc một logged BATCH ghi một chuyến vào các bảng:')
b.code('\n'.join([
    'BEGIN BATCH',
    '  INSERT INTO rides (...) VALUES (...);                  -- bảng gốc, tra theo ride_id',
    '  INSERT INTO rides_by_customer (...) VALUES (...);       -- lịch sử của khách',
    '  INSERT INTO rides_by_area_date (...) VALUES (...);      -- điều phối theo khu vực và ngày',
    '  INSERT INTO rides_by_driver_month (...) VALUES (...);   -- lịch sử của tài xế theo tháng',
    'APPLY BATCH;']))
b.step(3, 'Kiểm tra số dòng của một số bảng.')
b.code('cqlsh -e "SELECT COUNT(*) FROM ride_booking.rides; SELECT COUNT(*) FROM ride_booking.rides_by_customer; SELECT COUNT(*) FROM ride_booking.payments_by_city_date;"')
b.figure('Số dòng sau khi nạp dữ liệu.', 'Chạy lệnh trên, chụp kết quả', 'rides = 36, rides_by_customer = 36, payments_by_city_date = 27', 'Command Prompt', 'Bắt buộc')
b.step(4, 'Mở dữ liệu bảng `rides` trong DbSchema (chuột phải bảng, mở dữ liệu) để xem trực quan.')
b.figure('Dữ liệu bảng rides trong DbSchema.', 'Mở dữ liệu bảng rides trong DbSchema', 'Thấy các dòng RIDE_1001… với trạng thái, cước, thời gian', 'DbSchema', 'Nên có')

# -----------------------------------------------------------------------------------------
b.h2('5.6. Truy vấn cơ bản trên DbSchema')
b.para('Các truy vấn cơ bản đều chỉ định đủ khóa phân vùng nên mỗi câu chỉ đọc một partition. Truy vấn được viết trong SQL Editor của DbSchema (đặt con trỏ vào câu cần chạy rồi bấm Run) hoặc dựng bằng Query Builder. Driver JDBC của DbSchema chuyển nguyên câu CQL cho Cassandra {{jdbc}}, nên cú pháp giống cqlsh; riêng các lệnh `COPY`, `DESCRIBE` là lệnh của cqlsh và không chạy được trong DbSchema. Query Builder là tính năng của bản Pro {{dbsprice}}. Thời gian trong DbSchema hiển thị theo giờ máy, còn cqlsh hiển thị theo UTC.')
b.para('Danh mục đầy đủ 20 truy vấn B01–B20 nằm ở phụ lục của chương; dưới đây là các truy vấn tiêu biểu chạy trên DbSchema.')


def query_step(n, title, ids, src, caption, do, expect, tool, prio, extra=None, max_lines=None):
    txt = '\n'.join(src[i] for i in ids)
    b.step(n, title)
    b.code(txt, max_lines)
    if extra:
        b.para(extra)
    b.figure(caption, do, expect, tool, prio)


query_step(1, '**B01** – Đăng nhập: lấy tài khoản theo `username`. Ứng dụng so sánh mã băm SHA-256 của mật khẩu với `password_hash`, kiểm tra `is_active` rồi điều hướng theo `role`.', ['B01'], BASIC,
           'Truy vấn B01: đăng nhập theo username.', 'Chạy B01 trong SQL Editor của DbSchema, chụp câu lệnh và lưới kết quả', '1 dòng: cust001, CUSTOMER, CUST001, Nguyễn Văn An, is_active = true', 'DbSchema', 'Nên có')
query_step(2, '**B05** – Tra xe theo biển số bằng materialized view và theo tài xế bằng secondary index. Nếu không có view và index, hai câu này bị từ chối vì `license_plate` và `driver_id` không thuộc khóa chính của `vehicles`.', ['B05'], BASIC,
           'Truy vấn B05: tra xe theo biển số và theo tài xế.', 'Chạy hai câu của B05 trong SQL Editor, chụp cả hai kết quả', 'Cả hai câu trả về VEH_555, DRV_555, 51K-567.89, Toyota Innova', 'DbSchema', 'Bắt buộc')
query_step(3, '**B07** – Lịch sử chuyến của khách, mới nhất trước. Dựng bằng Query Builder: chọn bảng `rides_by_customer`, đặt Filter `customer_id` bằng `CUST001`, bấm Run.', ['B07'], BASIC,
           'Truy vấn B07: lịch sử chuyến của khách CUST001.', 'Dựng B07 bằng Query Builder (Pro), chụp vùng Preview CQL cùng kết quả', '4 chuyến: RIDE_1021 (04/10), RIDE_1001 (03/10), RIDE_1013 (01/10), RIDE_1007 (29/09)', 'DbSchema (Query Builder)', 'Bắt buộc')
query_step(4, '**B08** – Lọc theo khoảng ngày trên cột gom nhóm `ride_date`.', ['B08'], BASIC,
           'Truy vấn B08: lọc chuyến theo khoảng ngày.', 'Chạy B08 trong SQL Editor', '3 chuyến từ 01/10 đến 04/10/2026', 'DbSchema', 'Nên có')
query_step(5, '**B11** – Màn hình điều phối: các chuyến trong ngày 04/10/2026 ở Quận 1. Dựng bằng Query Builder với ba điều kiện `city`, `district`, `ride_date`.', ['B11'], BASIC,
           'Truy vấn B11: các chuyến trong ngày tại Quận 1.', 'Dựng B11 bằng Query Builder hoặc SQL Editor, chụp kết quả', '6 chuyến, mới nhất trước (RIDE_1022 ONGOING ở trên cùng)', 'DbSchema (Query Builder)', 'Bắt buộc')
query_step(6, '**B12** – Tài xế đang rảnh ở Tân Phú.', ['B12'], BASIC,
           'Truy vấn B12: tài xế đang rảnh ở Tân Phú.', 'Chạy B12 trong SQL Editor', '1 dòng: DRV_551 Lý Văn Phúc, rating 4.8', 'DbSchema', 'Nên có')
query_step(7, '**B13** – Vị trí GPS mới nhất của tài xế. `LIMIT 1` cho kết quả đúng vì cột `ts` sắp xếp giảm dần.', ['B13'], BASIC,
           'Truy vấn B13: vị trí GPS mới nhất.', 'Chạy B13 trong SQL Editor', '1 dòng có ts, location {lat, lng} và speed_kmh', 'DbSchema', 'Nên có')
query_step(8, '**B15** – Giao dịch thanh toán trong ngày. Kết quả được nhóm sẵn theo phương thức thanh toán nhờ cột gom nhóm `payment_method`.', ['B15'], BASIC,
           'Truy vấn B15: giao dịch thanh toán trong ngày.', 'Chạy B15 trong SQL Editor', '4 giao dịch ngày 03/10 (CASH, MOMO, ZALOPAY)', 'DbSchema', 'Nên có')
query_step(9, '**B17** – Thống kê số chuyến theo ngày từ bảng counter.', ['B17'], BASIC,
           'Truy vấn B17: thống kê chuyến theo ngày.', 'Chạy B17 trong SQL Editor', '4 ngày 01–04/10 với cột rides_requested, rides_completed, rides_cancelled', 'DbSchema', 'Nên có')
b.step(10, '**B18–B20** – Thêm, sửa và xóa dữ liệu (thao tác trên CSDL). Trong Cassandra, `UPDATE` cũng là upsert: nếu chưa có dòng thì sẽ tạo mới. `DELETE` ghi một tombstone chứ không xóa ngay trên đĩa, nên ảnh hưởng đến cả việc khôi phục ở mục 5.10.')
b.code('\n'.join([BASIC['B18'], BASIC['B19'], BASIC['B20']]))
b.figure('Thêm và sửa dữ liệu (B18, B19).', 'Chạy B18 và B19, chụp kết quả SELECT sau mỗi thao tác', 'Khách CUST999 được tạo rồi đổi số điện thoại và địa chỉ', 'DbSchema', 'Bắt buộc')
b.figure('Xóa dữ liệu (B20).', 'Chạy B20, chụp kết quả SELECT sau khi xóa', 'SELECT trả về (0 rows)', 'DbSchema', 'Bắt buộc')

# -----------------------------------------------------------------------------------------
b.h2('5.7. Truy vấn nâng cao')
b.para('Các truy vấn nâng cao dùng hàm gộp, nhóm dữ liệu, kiểu dữ liệu phức hợp (UDT, collection, cột static) và các hàm đặc thù của Cassandra. Chúng vẫn tuân thủ quy tắc “chỉ định đủ khóa phân vùng” để không phải quét toàn cụm.')
b.para('Danh mục đầy đủ 18 truy vấn A01–A18 nằm ở phụ lục của chương; dưới đây là các truy vấn tiêu biểu.')
query_step(1, '**A01** – Thu nhập tháng 10 của một tài xế. `ALLOW FILTERING` ở đây an toàn vì partition `(driver_id, yyyymm)` đã được cố định, Cassandra chỉ lọc vài chục dòng của tài xế trong tháng {{book|tr. 205}}.', ['A01'], ADV,
           'Truy vấn A01: thu nhập tháng của tài xế.', 'Chạy A01 trong SQL Editor', '1 dòng: số chuyến 2, tổng cước 159000, trung bình 79500, thấp nhất 68000, cao nhất 91000', 'DbSchema', 'Nên có')
query_step(2, '**A02** – Doanh thu một ngày theo phương thức thanh toán. `GROUP BY` chỉ nhận cột khóa chính theo đúng thứ tự khai báo (khóa phân vùng trước, rồi đến tiền tố của cột gom nhóm); nhóm theo cột thường sẽ bị lỗi “Group by is currently only supported on the columns of the PRIMARY KEY”.', ['A02'], ADV,
           'Truy vấn A02: doanh thu theo phương thức thanh toán.', 'Chạy A02 trong SQL Editor', '3 dòng: CASH 158000, MOMO 26000, ZALOPAY 110000 (giảm giá 20000)', 'DbSchema', 'Bắt buộc')
query_step(3, '**A03** – Doanh thu bảy ngày: `IN` trên khóa phân vùng kết hợp `GROUP BY`. Cassandra cảnh báo “Aggregation query used on multiple partition keys”, chấp nhận được với vài partition.', ['A03'], ADV,
           'Truy vấn A03: doanh thu bảy ngày.', 'Chạy A03 trong SQL Editor', '7 dòng từ 28/09 đến 04/10; ngày 03/10 có 4 giao dịch, 294000', 'DbSchema', 'Nên có')
query_step(4, '**A04** – Thống kê một khu vực trong ngày bằng hàm gộp trên một partition. Gom theo từng giờ bằng `GROUP BY floor(requested_at, 1h)` chỉ có từ Cassandra 4.1 nên trên 3.11 ứng dụng tự gom theo giờ.', ['A04'], ADV,
           'Truy vấn A04: thống kê khu vực trong ngày.', 'Chạy A04 trong SQL Editor', '1 dòng: 6 chuyến, tổng cước 256000', 'DbSchema', 'Nên có')
query_step(5, '**A06** – Điểm đánh giá trung bình. Hàm `AVG` trên cột `int` trả về số nguyên, nên phải `CAST(stars AS double)`.', ['A06'], ADV,
           'Truy vấn A06: điểm trung bình của tài xế.', 'Chạy A06 trong SQL Editor', '1 dòng: 2 đánh giá, điểm trung bình 4.5', 'DbSchema', 'Nên có')
query_step(6, '**A07** – Đánh giá mới nhất của mỗi tài xế. `LIMIT` giới hạn tổng số dòng, còn `PER PARTITION LIMIT` giới hạn số dòng trong mỗi partition.', ['A07'], ADV,
           'Truy vấn A07: đánh giá mới nhất của mỗi tài xế.', 'Chạy A07 trong SQL Editor', '10 dòng, mỗi tài xế một dòng', 'DbSchema', 'Bắt buộc')
query_step(7, '**A10** – Cột static: tên tài xế và biển số lưu một lần cho cả partition. Đổi biển số chỉ cần một lệnh `UPDATE` theo `(driver_id, yyyymm)`.', ['A10'], ADV,
           'Truy vấn A10: cột static.', 'Chạy A10 trong SQL Editor', '1 dòng: DRV_551, 202610, Lý Văn Phúc, 51F-123.45', 'DbSchema', 'Nên có')
query_step(8, '**A12** – Collection: `map` lịch sử trạng thái, `list` nhãn đánh giá, `set` thành phố áp dụng khuyến mãi {{book|tr. 72}}.', ['A12'], ADV,
           'Truy vấn A12: map, list và set.', 'Chạy 3 câu của A12', 'status_history có các mốc REQUESTED→ACCEPTED→ONGOING→COMPLETED; tags dạng danh sách; cities dạng tập hợp', 'DbSchema', 'Nên có')
query_step(9, '**A13** – `TTL()` và `WRITETIME()`: thời gian sống còn lại (giây) và thời điểm ghi (micro giây) {{book|tr. 65}}. Trên 3.11 hai hàm này không dùng được với collection không frozen.', ['A13'], ADV,
           'Truy vấn A13: TTL và WRITETIME.', 'Chạy A13 trong SQL Editor', 'GIAM20 còn khoảng 7,7 triệu giây (90 ngày); vị trí GPS còn khoảng 86.400 giây (24 giờ)', 'DbSchema', 'Bắt buộc')
b.step(10, '**A18** – Truy vấn bị từ chối để thấy vì sao phải thiết kế theo truy vấn. Bảng `rides` phân vùng theo `ride_id`, nên hỏi theo `customer_id` buộc phải quét mọi node. Câu hỏi “chuyến của một khách” được trả lời bằng bảng riêng `rides_by_customer` (B07).')
b.code("SELECT * FROM rides WHERE customer_id = 'CUST001';")
b.figure('Truy vấn thiếu khóa phân vùng bị Cassandra từ chối.', 'Chạy câu trên trong SQL Editor, chụp thông báo lỗi', 'Lỗi “Cannot execute this query as it might involve data filtering…” gợi ý ALLOW FILTERING', 'DbSchema', 'Bắt buộc')

# -----------------------------------------------------------------------------------------
b.h2('5.8. Luồng ghi nghiệp vụ: LWT, BATCH, counter và TTL')
b.para('File `05_transactions.cql` mô phỏng một kịch bản lúc 10:00–10:40 ngày 04/10/2026: khách `CUST001` đặt chuyến `RIDE_2001` ra sân bay, hai tài xế tranh nhau nhận, khách dùng mã giảm giá, hoàn thành và đánh giá. Song song có một chuyến bị hủy (`RIDE_2002`). Giao dịch nhẹ (LWT) dùng mệnh đề `IF` để kiểm soát tranh chấp {{book|tr. 191}}; LWT dựa trên thuật toán Paxos nên tốn nhiều lượt trao đổi hơn một lần ghi thường {{book|tr. 120}}, vì vậy chỉ dùng ở bước có tranh chấp.')
b.para('Chạy file này **một lần** sau `04_queries_advanced.cql`. Chạy lại thì các câu LWT trả `[applied] = False` (đúng thiết kế) nhưng counter bị cộng thêm; muốn làm lại thì chạy `99_reset_data.cql`, `02_data.cql` rồi `05_transactions.cql`.')
b.para('Các bước T01–T12 của kịch bản được liệt kê ở phụ lục của chương; dưới đây là các bước tiêu biểu.')
b.step(1, '**T01** – Đăng ký tài khoản bằng LWT `IF NOT EXISTS`. Lần thứ hai dùng cùng `username` bị từ chối và Cassandra trả về dòng đang có.', )
b.code(TX['T01'])
b.figure('Đăng ký tài khoản bằng LWT (T01).', 'Chạy T01 trong SQL Editor hoặc cqlsh, chụp hai kết quả [applied]', 'Lần 1: [applied] = True; lần 2: [applied] = False kèm dòng đang có', 'DbSchema / cqlsh', 'Nên có')
b.step(2, '**T05** – Hai tài xế cùng bấm “Nhận chuyến”. LWT trên cột thường `status` bảo đảm chỉ một người thắng. Vì `BATCH` có điều kiện chỉ được nằm trong một partition, LWT chạy riêng trước, `BATCH` cập nhật các bảng phụ chạy sau.')
b.code(TX['T05'], 14)
b.figure('Hai tài xế tranh nhận chuyến (T05).', 'Chạy T05 bằng cqlsh (khối BATCH nên chạy ở cqlsh), chụp hai kết quả LWT', 'DRV_555: [applied] = True; DRV_554: [applied] = False, status = ACCEPTED', 'cqlsh', 'Bắt buộc')
b.step(3, '**T07** – Áp mã `GIAM20` bằng LWT tăng `used_count` có điều kiện (optimistic locking). Lưu ý `UPDATE` không kèm `USING TTL` lên dòng đang có TTL sẽ tạo ô không hết hạn, nên câu lệnh ghi lại TTL.')
b.code(TX['T07'])
b.figure('Áp mã khuyến mãi bằng LWT (T07).', 'Chạy T07, chụp ba kết quả', 'Lần 1 [applied] = True; lần 2 [applied] = False, used_count = 6', 'cqlsh', 'Nên có')
b.step(4, '**T08** – Hoàn thành chuyến: LWT chuyển `ONGOING` sang `COMPLETED`, sau đó một `BATCH` cập nhật ba bảng chuyến, ghi bảng thanh toán, cập nhật tài xế và đưa tài xế trở lại danh sách rảnh (kèm TTL); số đếm chuyến nằm trong `COUNTER BATCH` riêng.')
b.code(TX['T08'], 22)
b.figure('Hoàn thành chuyến và thanh toán (T08).', 'Chạy T08 bằng cqlsh, chụp kết quả', '[applied] = True; không có lỗi ở BATCH', 'cqlsh', 'Bắt buộc')
b.step(5, '**T12** – Kiểm tra lại kết quả sau toàn bộ kịch bản.')
b.code(TX['T12'])
b.figure('Kết quả sau kịch bản T01–T11.', 'Chạy T12, chụp kết quả', 'RIDE_2001 = COMPLETED; RIDE_2002 = CANCELLED; điểm DRV_555 cập nhật; counter tăng', 'cqlsh', 'Nên có')
b.bullets([
    '**Chi phí LWT:** mỗi LWT dùng Paxos nên đắt hơn ghi thường nhiều; chỉ dùng ở bước có tranh chấp.',
    '**Giới hạn của BATCH:** `BATCH` có điều kiện chỉ nằm trong một partition; counter phải ở `COUNTER BATCH` riêng, không trộn với bảng thường.',
    '**TTL:** dòng hết hạn trở thành tombstone, nên dữ liệu tạm như vị trí GPS được đặt TTL mặc định ở mức bảng.',
])

# -----------------------------------------------------------------------------------------
b.h2('5.9. Nhập và xuất dữ liệu')
b.para('Đề tài dùng ba cách trao đổi dữ liệu, được tổng hợp trong bảng dưới đây.')
b.table(
    ['Cách', 'Dùng khi', 'Giữ TTL', 'Chạy ở đâu'],
    [
        ['`COPY ... TO / FROM` (CSV)', 'Trao đổi với Excel, ứng dụng khác; sao lưu logic dữ liệu nhỏ', 'Không', 'cqlsh (không phải câu CQL)'],
        ['`nodetool snapshot` + `sstableloader`', 'Sao lưu – khôi phục vật lý (mục 5.10)', 'Có', 'Trên node'],
        ['DbSchema: Save Results to File, Data Importer', 'Thao tác bằng giao diện', 'Không', 'DbSchema'],
    ],
    [2650, 3200, 800, 2400],
    'Các cách nhập/xuất dữ liệu.')
b.h3('5.9.1. Xuất CSV bằng COPY TO')
b.para('`COPY` là lệnh của cqlsh, tài liệu mô tả đầy đủ các tùy chọn {{cqlsh}}. Ví dụ xuất lịch sử chuyến, chọn cột và đổi dấu phân cách sang `;` để mở bằng Excel tiếng Việt. Thư mục đích phải có sẵn và đường dẫn trong lệnh `COPY` viết bằng dấu `/`:')
b.code('mkdir D:\\NOSQL\\export\ncqlsh -e "COPY ride_booking.rides_by_customer (customer_id, ride_date, ride_id, pickup_address, destination_address, fare, status) TO \'D:/NOSQL/export/lich_su_chuyen.csv\' WITH HEADER = true AND DELIMITER = \';\';"')
b.figure('Xuất lịch sử chuyến ra CSV bằng COPY TO.', 'Chạy 2 lệnh trên, chụp kết quả', '36 rows exported to 1 files (chạy sau 02_data.cql)', 'Command Prompt', 'Bắt buộc')
b.figure('Nội dung file CSV đã xuất.', 'Mở D:\\NOSQL\\export\\lich_su_chuyen.csv bằng Notepad hoặc Excel, chụp một trong hai', 'Dòng tiêu đề và các dòng dữ liệu phân cách bằng dấu ;', 'Notepad / Excel', 'Nên có')
b.h3('5.9.2. Nhập CSV bằng COPY FROM')
b.para('File `csv\\customers_import.csv` có thứ tự cột khác thứ tự trong bảng nên phải liệt kê cột. Cột thời gian phải ghi ở múi giờ UTC (`+0000`) vì `COPY FROM` của cqlsh hiểu ngược dấu độ lệch múi giờ: chuỗi `2026-10-04 08:00:00+0700` bị lưu thành 15:00 UTC.')
b.code('cqlsh -e "COPY ride_booking.customers (customer_id, full_name, phone, email, address, created_at) FROM \'D:/NOSQL/cassandra/csv/customers_import.csv\' WITH HEADER = true;"\ncqlsh -e "SELECT customer_id, full_name, created_at FROM ride_booking.customers WHERE customer_id IN (\'CUST011\', \'CUST012\');"')
b.figure('Nhập 5 khách hàng từ CSV bằng COPY FROM.', 'Chạy 2 lệnh trên, chụp kết quả', '5 rows imported from 1 files; SELECT thấy CUST011, CUST012', 'Command Prompt', 'Bắt buộc')
b.h3('5.9.3. Trên DbSchema')
b.para('DbSchema cho phép xuất toàn bộ kết quả một truy vấn ra file bằng Save Results to File và nạp CSV, XML, XLS bằng Data Importer/Data Loader {{dbsdoc}}. Data Importer thuộc bản Pro {{dbsprice}}. Tài liệu của DbSchema không xác nhận Data Importer chạy với Cassandra, nên cần thử và ghi nhận kết quả; nếu DbSchema báo lỗi kiểu `TIMESTAMP` như ở Data Generator (Hình 3.15) thì dùng `COPY FROM` làm cách chính.')
b.figure('Xuất kết quả truy vấn ra file từ DbSchema.', 'Chạy một truy vấn trong DbSchema rồi chọn Save Results to File; chụp hộp thoại hoặc file kết quả', 'File xuất ra có đủ cột và dòng', 'DbSchema', 'Tùy chọn')
b.figure('Nhập CSV vào bảng bằng Data Importer của DbSchema.', 'Thử Data Importer với customers_import.csv; chụp kết quả hoặc thông báo lỗi nếu có', 'Dữ liệu vào bảng, hoặc thông báo lỗi để ghi nhận hạn chế', 'DbSchema (Pro)', 'Tùy chọn')
b.h3('5.9.4. Những điều đã kiểm chứng')
b.bullets([
    '**Mất TTL.** Mã `GIAM20` có TTL 90 ngày, nhưng sau khi xuất rồi nhập lại thì `TTL(description) = null`. Bảng có TTL thì nhập kèm `WITH TTL = <giây>`.',
    '**Counter bị cộng dồn.** Nhập lại `ride_stats_by_city` vào bảng đang có số liệu sẽ cộng thêm (21 thành 42 khi thử); phải `TRUNCATE` trước.',
    '**`MAXROWS` chỉ có tác dụng với `COPY FROM`.** Dùng với `COPY TO` thì bị bỏ qua và vẫn xuất toàn bộ.',
    '**Excel** mở CSV UTF-8 không có BOM sẽ lỗi dấu tiếng Việt; dùng Data, From Text/CSV, File origin 65001 (UTF-8).',
])

# -----------------------------------------------------------------------------------------
b.h2('5.10. Sao lưu và khôi phục dữ liệu')
b.h3('5.10.1. Cơ sở lý thuyết')
b.para('Cassandra sao lưu bằng snapshot: lệnh `nodetool snapshot` ghi memtable xuống đĩa (flush) rồi tạo một hard link cho mỗi file SSTable, nên rất nhanh và gần như không tốn thêm chỗ lúc tạo {{book|tr. 291}}. Cassandra còn tự tạo snapshot trước mỗi lệnh `DROP KEYSPACE`, `DROP TABLE` và `TRUNCATE` (thuộc tính `auto_snapshot`, mặc định bật) {{book|tr. 292}}. Incremental backup tạo thêm hard link cho mỗi SSTable được flush sau snapshot {{book|tr. 292}}.')
b.para('Khôi phục là chép lại các file SSTable của snapshot cùng các file incremental. Trước khi khôi phục nên `TRUNCATE` bảng để xóa các thay đổi sau snapshot, và phải bảo đảm lược đồ đã có vì snapshot không chứa lược đồ {{book|tr. 293}}. Nếu cấu trúc cụm không đổi thì chép file vào thư mục dữ liệu rồi chạy `nodetool refresh` (từ Cassandra 4.0 dùng `nodetool import`); nếu topology hoặc hệ số sao lưu thay đổi thì dùng `sstableloader`, công cụ đẩy dữ liệu của từng SSTable vào cụm để partitioner và chiến lược sao lưu tự phân phối lại {{book|tr. 293}}.')
b.table(
    ['Phương pháp', 'Sao lưu', 'Khôi phục', 'Ghi chú'],
    [
        ['Lược đồ', '`DESCRIBE KEYSPACE ride_booking`', '`cqlsh -f schema.cql`', 'Snapshot không chứa lược đồ'],
        ['Snapshot', '`nodetool flush` + `nodetool snapshot -t <tên> ride_booking`', '`TRUNCATE`, chép file vào thư mục dữ liệu rồi `nodetool refresh`', 'Nhanh, dùng hard link'],
        ['Incremental', '`nodetool enablebackup`', 'Snapshot gần nhất + file trong `backups`', 'Bật tạm thời, không sửa cấu hình'],
        ['Logic (CSV)', '`COPY ... TO`', '`COPY ... FROM`', 'Mất TTL; mục 5.9'],
        ['Auto snapshot', 'Tự động khi `TRUNCATE`/`DROP`', 'Như snapshot', 'Mặc định bật'],
    ],
    [1500, 3300, 2600, 1650],
    'Các phương pháp sao lưu và khôi phục.')
b.h3('5.10.2. Sao lưu')
b.step(1, 'Lưu lược đồ của keyspace ra file, vì snapshot không chứa lược đồ {{book|tr. 293}}.')
b.code('mkdir D:\\Backup\\bk_20261004\nset PYTHONIOENCODING=utf-8\ncqlsh -e "DESCRIBE KEYSPACE ride_booking" > D:\\Backup\\bk_20261004\\schema.cql')
b.figure('Lưu lược đồ keyspace ra file schema.cql.', 'Chạy 3 lệnh trên, rồi mở schema.cql bằng Notepad và chụp phần đầu', 'File có CREATE KEYSPACE ride_booking và các CREATE TABLE', 'Command Prompt / Notepad', 'Nên có')
b.step(2, 'Ghi memtable xuống đĩa rồi chụp snapshot cho keyspace {{book|tr. 291}}.')
b.code('nodetool flush ride_booking\nnodetool snapshot -t bk_20261004 ride_booking\nnodetool listsnapshots')
b.figure('Chụp snapshot của keyspace ride_booking.', 'Chạy 3 lệnh trên, chụp kết quả', 'Snapshot bk_20261004 liệt kê từng bảng của ride_booking', 'Command Prompt', 'Bắt buộc')
b.step(3, 'Snapshot nằm trong `data\\data\\ride_booking\\<tên bảng>-<mã>\\snapshots\\bk_20261004` của thư mục Cassandra {{book|tr. 291}}. Chép thư mục snapshot của từng bảng ra ổ sao lưu, gom theo cấu trúc `<keyspace>\\<bảng>`. Có thể làm bằng File Explorer, hoặc bằng một lệnh PowerShell:')
b.code("""Get-ChildItem 'c:\\apache-cassandra-3.11.4\\data\\data\\ride_booking\\*\\snapshots\\bk_20261004' -Directory | ForEach-Object { $t = $_.Parent.Parent.Name -replace '-[0-9a-f]{32}$',''; Copy-Item $_.FullName "D:\\Backup\\bk_20261004\\ride_booking\\$t" -Recurse }""")
b.figure('Bản sao lưu snapshot theo từng bảng.', 'Chạy lệnh PowerShell, rồi mở D:\\Backup\\bk_20261004\\ride_booking bằng File Explorer và chụp', 'Mỗi bảng một thư mục, trong đó có file *-Data.db và manifest.json', 'PowerShell / File Explorer', 'Nên có')
b.h3('5.10.3. Gây sự cố và khôi phục')
b.step(4, 'Giả lập hai sự cố: xóa nhầm một chuyến và xóa sạch một bảng.')
b.code("DELETE FROM ride_booking.rides WHERE ride_id = 'RIDE_1001';\nTRUNCATE ride_booking.payments_by_city_date;")
b.figure('Giả lập sự cố mất dữ liệu.', 'Chạy 2 lệnh trong cqlsh, rồi chạy B06 và B15 để cho thấy dữ liệu đã mất', 'B06 không còn RIDE_1001; payments_by_city_date trống', 'cqlsh / DbSchema', 'Bắt buộc')
b.step(5, 'Khôi phục bảng `rides`. Cassandra 3.11 chưa có `nodetool import` nên dùng cách của sách trước bản 4.0: chép file SSTable vào thư mục dữ liệu của bảng rồi chạy `nodetool refresh` {{book|tr. 293}}. Phải `TRUNCATE` bảng trước: lệnh `DELETE` đã ghi một tombstone có timestamp mới hơn dữ liệu trong snapshot, Cassandra luôn giữ phiên bản mới nhất (last-write-wins) nên dữ liệu cũ nạp lại vẫn bị tombstone che. `TRUNCATE` xóa cả dữ liệu lẫn tombstone, đồng thời tránh ghi đè SSTable cùng số thứ tự.')
b.code("""cqlsh -e "TRUNCATE ride_booking.rides;"
$id = (cqlsh -e "SELECT id FROM system_schema.tables WHERE keyspace_name='ride_booking' AND table_name='rides'" | Select-String '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}').Matches.Value -replace '-',''
Copy-Item 'D:\\Backup\\bk_20261004\\ride_booking\\rides\\*' "c:\\apache-cassandra-3.11.4\\data\\data\\ride_booking\\rides-$id"
nodetool refresh ride_booking rides""")
b.para('Chạy các lệnh trong cửa sổ PowerShell, thư mục `bin` của Cassandra đã nằm trong PATH. Thư mục dữ liệu của bảng có tên `<bảng>-<id>`, với `id` lấy từ `system_schema.tables` (bỏ dấu gạch ngang). Không đoán theo tên bảng, vì bảng từng bị xóa hoặc tạo lại sẽ để lại thư mục cũ cùng tên.')
b.figure('Khôi phục bảng rides từ snapshot.', 'Chạy 4 lệnh trên trong PowerShell, chụp kết quả', 'Các lệnh chạy không lỗi', 'PowerShell', 'Bắt buộc')
b.step(6, 'Khôi phục tương tự cho bảng `payments_by_city_date` (thay `rides` bằng tên bảng trong ba lệnh trên).')
b.figure('Khôi phục bảng payments_by_city_date.', 'Làm tương tự bước trên cho payments_by_city_date, chụp kết quả', 'Các lệnh chạy không lỗi', 'PowerShell', 'Nên có')
b.step(7, 'Kiểm tra dữ liệu đã trở lại.')
b.code("SELECT ride_id, status FROM ride_booking.rides WHERE ride_id = 'RIDE_1001';\nSELECT COUNT(*) FROM ride_booking.payments_by_city_date;")
b.figure('Dữ liệu sau khi khôi phục.', 'Chạy 2 câu trên trong DbSchema', 'RIDE_1001 COMPLETED; payments_by_city_date có 27 dòng', 'DbSchema', 'Bắt buộc')
b.bullets([
    'Dữ liệu bị xóa hoặc sửa sai: luôn `TRUNCATE` bảng trước khi khôi phục.',
    'Cassandra cũng đã tự tạo snapshot `truncated-…` và `dropped-…` trước khi xóa, xem bằng `nodetool listsnapshots`.',
    'Nếu topology hoặc hệ số sao lưu thay đổi thì dùng `sstableloader`, công cụ đẩy dữ liệu của từng SSTable vào cụm {{book|tr. 293}}. Ví dụ: `sstableloader -d 127.0.0.1 D:\\Backup\\bk_20261004\\ride_booking\\rides` (đường dẫn phải kết thúc bằng `<keyspace>\\<bảng>`).',
])
b.h3('5.10.4. Incremental backup')
b.step(8, 'Bật incremental backup, ghi thêm một chuyến rồi flush; thư mục `backups` của bảng (cạnh thư mục `snapshots`) có thêm file SSTable mới {{book|tr. 292}}.')
b.code('nodetool statusbackup\nnodetool enablebackup\nnodetool statusbackup')
b.figure('Bật incremental backup.', 'Chạy 3 lệnh trên, chụp kết quả', 'not running, sau đó running', 'Command Prompt', 'Nên có')
b.code("INSERT INTO ride_booking.rides_by_customer (customer_id, ride_date, ride_id, fare, status)\nVALUES ('CUST001', '2026-10-04', 'RIDE_9999', 99000.0, 'COMPLETED');\nnodetool flush ride_booking")

# -----------------------------------------------------------------------------------------
b.h2('5.11. Tổng kết chương')
b.bullets([
    'Đã thiết kế CSDL theo truy vấn với 18 truy vấn, 14 bảng và 1 materialized view; giữ nguyên 4 bảng đã có trong báo cáo giữa kỳ.',
    'Đã tạo keyspace, nạp 285 dòng dữ liệu nhất quán giữa các bảng phi chuẩn hóa bằng logged BATCH.',
    'Đã thực hiện 20 truy vấn cơ bản, 18 truy vấn nâng cao và kịch bản ghi nghiệp vụ T01–T12 (LWT, BATCH, counter, TTL) trên DbSchema và cqlsh.',
    'Đã nhập/xuất dữ liệu bằng `COPY`; sao lưu và khôi phục bằng snapshot, incremental backup, `nodetool refresh`, kèm kịch bản sự cố và giải thích vai trò của tombstone khi khôi phục.',
    'DbSchema hỗ trợ tốt phần thiết kế, trực quan hóa và truy vấn; phần sao lưu/khôi phục dữ liệu Cassandra phải dùng công cụ dòng lệnh của Cassandra, vì DbSchema không có chức năng này.',
])

b.h2('PHỤ LỤC CỦA CHƯƠNG 5 (có thể chuyển xuống cuối báo cáo hoặc bỏ nếu thiếu trang)')
b.h3('Phụ lục 5.1. Số dòng dữ liệu mẫu')
b.table(
    ['Bảng', 'Số dòng', 'Ghi chú'],
    [
        ['`customers`', '10', 'CUST001–CUST010'],
        ['`drivers`', '10', 'DRV_551–DRV_560, có DRV_555 như báo cáo giữa kỳ'],
        ['`vehicles`', '10', 'Mỗi tài xế một xe'],
        ['`user_accounts`', '22', 'admin, dieuphoi, 10 khách, 10 tài xế'],
        ['`rides`', '36', '27 COMPLETED, 5 CANCELLED, 2 ONGOING, 1 ACCEPTED, 1 REQUESTED'],
        ['`rides_by_customer`', '36', 'Có dòng RIDE_1001 như báo cáo giữa kỳ'],
        ['`rides_by_area_date`', '36', ''],
        ['`rides_by_driver_month`', '34', '2 chuyến chưa có tài xế không xuất hiện'],
        ['`payments_by_city_date`', '27', 'Một giao dịch cho mỗi chuyến COMPLETED'],
        ['`ratings_by_driver`', '23', ''],
        ['`promotions`', '3', 'GIAM20, HCMXANH, HANOI10 (TTL 90 ngày)'],
        ['`ride_stats_by_city`', '14', 'Counter, khớp số chuyến theo ngày'],
        ['`drivers_by_area`', '6', 'Tài xế đang rảnh lúc 10:00'],
        ['`driver_locations`', '18', '3 tài xế × 6 điểm GPS'],
        ['**Tổng**', '**285**', ''],
    ],
    [2600, 1100, 5350],
    'Số dòng dữ liệu mẫu của từng bảng.')
b.h3('Phụ lục 5.2. Danh mục truy vấn cơ bản')
b.table(
    ['Mã', 'Nội dung', 'Mã', 'Nội dung'],
    [
        ['B01', 'Đăng nhập theo username', 'B11', 'Chuyến trong ngày của một quận'],
        ['B02–B04', 'Hồ sơ khách, tài xế, xe theo mã', 'B12', 'Tài xế đang rảnh ở một quận'],
        ['B05', 'Tra xe theo biển số (view) và theo tài xế (index)', 'B13', 'Vị trí GPS mới nhất'],
        ['B06', 'Chi tiết một chuyến', 'B14', 'Đánh giá của tài xế'],
        ['B07', 'Lịch sử chuyến của khách, mới nhất trước', 'B15', 'Giao dịch thanh toán trong ngày'],
        ['B08', 'Lọc theo khoảng ngày', 'B16', 'Kiểm tra mã khuyến mãi'],
        ['B09', '3 chuyến gần nhất (LIMIT)', 'B17', 'Thống kê chuyến theo ngày (counter)'],
        ['B10', 'Chuyến của tài xế trong tháng', 'B18–B20', 'Thêm, sửa, xóa'],
    ],
    [1100, 3450, 1100, 3400],
    'Danh mục 20 truy vấn cơ bản B01–B20.')
b.h3('Phụ lục 5.3. Danh mục truy vấn nâng cao')
b.table(
    ['Mã', 'Nội dung', 'Mã', 'Nội dung'],
    [
        ['A01', 'COUNT/SUM/AVG/MIN/MAX + ALLOW FILTERING trong một partition', 'A10', 'Cột STATIC'],
        ['A02', 'GROUP BY theo cột gom nhóm', 'A11', 'Truy cập trường của UDT'],
        ['A03', 'IN trên khóa phân vùng + GROUP BY theo ngày', 'A12', 'Collection: map, list, set'],
        ['A04', 'Hàm gộp trên một partition khu vực–ngày', 'A13', 'TTL và WRITETIME'],
        ['A05', 'Tổng tháng từ bảng counter', 'A14', 'Phân trang bằng token()'],
        ['A06', 'Điểm trung bình với CAST', 'A15', 'DISTINCT trên khóa phân vùng'],
        ['A07', 'PER PARTITION LIMIT', 'A16', 'Lọc theo cột thường trong partition'],
        ['A08', 'IN trên một phần khóa phân vùng', 'A17', 'JSON, CAST và hàm thời gian'],
        ['A09', 'Khoảng thời gian + đảo thứ tự', 'A18', 'Truy vấn bị từ chối'],
    ],
    [700, 3850, 700, 3800],
    'Danh mục 18 truy vấn nâng cao A01–A18.')
b.h3('Phụ lục 5.4. Các bước của kịch bản ghi nghiệp vụ')
b.table(
    ['Bước', 'Câu lệnh chính', 'Kết quả', 'Ý nghĩa'],
    [
        ['T01', '`INSERT INTO user_accounts ... IF NOT EXISTS`', '`True`; đăng ký trùng thì `False`', 'Username duy nhất'],
        ['T02', '`UPDATE ... SET is_active = false ... IF is_active = true`', '`True`', 'Khóa/mở tài khoản'],
        ['T03', '`BATCH` cập nhật tài xế và `INSERT drivers_by_area USING TTL 300`', 'TTL = 300', 'Mất tín hiệu 5 phút thì tự biến mất'],
        ['T04', '`INSERT INTO rides ... IF NOT EXISTS`, `BATCH`, counter', '`True`', 'Không tạo chuyến trùng khi gửi lại'],
        ['T05', '`UPDATE rides ... IF status = ‘REQUESTED’`', 'Tài xế 1 `True`, tài xế 2 `False`', 'Chỉ một tài xế nhận được chuyến'],
        ['T06', '`... IF status = ‘ACCEPTED’ AND driver_id = ...`', '`True`', 'Chỉ đúng tài xế mới bắt đầu'],
        ['T07', '`UPDATE promotions USING TTL ... IF used_count = 5`', '`True`; lần 2 `False`', 'Không vượt giới hạn lượt dùng mã'],
        ['T08', '`... IF status = ‘ONGOING’`, `BATCH` nhiều bảng, counter', '`True`', 'Hoàn thành, thanh toán, cập nhật tài xế'],
        ['T09', '`INSERT ratings_by_driver`, `tags = tags + [...]`, `AVG`', '4,67', 'Điểm tài xế được cập nhật'],
        ['T10', '`UPDATE rides ... IF status IN (‘REQUESTED’, ‘ACCEPTED’)`', '`True`', 'Chỉ hủy được khi chưa chạy'],
        ['T11', '`cities = cities + {‘DN’}` rồi `- {‘DN’}`', '`{‘DN’, ‘HCM’, ‘HN’}`', 'Thêm/bớt phần tử của set'],
    ],
    [700, 3650, 2200, 2500],
    'Các bước của kịch bản T01–T12.')

# =========================================================================================
# Tài liệu tham khảo (bổ sung)
# =========================================================================================
b.h2('TÀI LIỆU THAM KHẢO CỦA CHƯƠNG 5 (đã đồng bộ vào file Word chính, số tiếp theo [1]–[10] của Chương 1–4)')
for i, key in enumerate(b.ref_order, 1):
    if key in PRE_ORDER:
        continue
    b.raw_paragraph('<w:spacing w:after="80" w:line="360" w:lineRule="auto"/><w:ind w:left="567" w:hanging="567"/><w:jc w:val="both"/>',
                    b.run('[%d] ' % i, bold=False) + b.run(REFS[key]))

# =========================================================================================
# Trang hướng dẫn + bảng kiểm ảnh (đặt ở đầu file, xóa trước khi nộp)
# =========================================================================================
head = Builder(REFS)
head.chapter('TRANG HƯỚNG DẪN – XÓA TRANG NÀY TRƯỚC KHI ĐƯA VÀO BÁO CÁO')
head.para('File này là **Chương 5** để dán vào báo cáo. Khung định dạng (font Times New Roman 13, tiêu đề, chú thích hình, bảng) lấy từ chính file Word giữa kỳ, nên khi sao chép sang báo cáo hãy chọn **Keep Source Formatting** (Giữ nguyên định dạng nguồn).')
head.bullets([
    'Mỗi hình có một dòng nền vàng dạng “[CHÈN ẢNH – mức ưu tiên] việc cần làm”. Chạy đúng thao tác ghi ở đó, chụp ảnh, **xóa dòng nền vàng và dán ảnh vào đúng chỗ đó** (đoạn căn giữa nằm ngay trên chú thích).',
    'Ảnh “Tùy chọn” đã được bỏ khỏi chương. “Bắt buộc” là các ảnh chứng minh thang điểm mục 5, 6, 7 và 9; “Nên có” làm báo cáo đầy đủ, có thể bỏ thêm nếu thiếu trang.',
    'Chụp ảnh nhỏ: chỉ cắt vùng cần chứng minh (câu lệnh và kết quả), không chụp cả màn hình; đặt chiều rộng ảnh 11–12 cm và chiều cao không quá 6 cm (Picture Format, Size).',
    'Số hình và số bảng là trường tự đánh số của Word. Sau khi xóa hoặc thêm hình, nhấn **Ctrl + A rồi F9** để cập nhật lại số. Văn bản chương không tham chiếu số hình để tránh sai khi đánh số lại.',
    'Số chương “5” giả định Chương 1–4 như bản nháp hiện có; nếu đổi số chương thì sửa chữ “Hình 5.” và “Bảng 5.” trong chú thích (Find & Replace).',
    'Số tài liệu tham khảo [1], [2]… đánh theo thứ tự xuất hiện trong chương này. Khi ghép vào báo cáo, đánh lại số theo thứ tự xuất hiện của cả báo cáo và dán danh sách ở cuối chương vào mục TÀI LIỆU THAM KHẢO.',
    'Thân bài dùng giãn dòng 1.5 theo yêu cầu của thang điểm. Bản nháp hiện dùng 1.15; nên chuyển cả báo cáo về 1.5 (chọn tất cả, Paragraph, Line spacing 1.5).',
    'Ngân sách trang: thang điểm yêu cầu cả báo cáo 50–60 trang, trong khi Chương 1–4 hiện đã 36 trang. Chương này khi chưa có ảnh dài khoảng 26 trang. Cách giảm: chụp ảnh nhỏ như trên, bỏ bớt ảnh “Nên có”, rút gọn Chương 3–4.',
    'Môi trường: lệnh trong chương viết cho Cassandra cài trực tiếp trên Windows theo tài liệu thực hành (c:\\apache-cassandra-3.11.4, JDK 8, Python 2.7). Thư mục D:\\NOSQL\\cassandra là giả định, sửa theo máy. Máy dùng Docker (container nosql-cassandra-doan) chạy tương đương: thêm tiền tố docker exec nosql-cassandra-doan trước cqlsh và nodetool; đường dẫn /doan/... thay cho D:/NOSQL/cassandra/...; /backup thay cho D:/NOSQL/export và D:/Backup; riêng sao lưu và khôi phục dùng script backup_snapshot.sh và restore_snapshot.sh trong DoAn/cassandra/scripts. Chi tiết từng lệnh có trong DoAn/CASSANDRA.MD.',
    'DbSchema bản dùng thử hết hạn sau 15 ngày và khi đó không mở được file project đã lưu: nên chụp hết các ảnh DbSchema trong cùng một đợt.',
])
head.table(
    ['Hình', 'Việc cần làm', 'Kết quả phải thấy', 'Công cụ', 'Ưu tiên'],
    [[str(n), do, expect, tool, prio] for (n, cap, do, expect, tool, prio) in b.checklist],
    [800, 3000, 2600, 1550, 1100],
    'Bảng kiểm các ảnh cần chụp cho Chương 5.')

# =========================================================================================
# Lắp vào file Word: dùng bản sao của file Word giữa kỳ làm khuôn (styles, numbering, header/footer)
# =========================================================================================
doc = Document(str(DRAFT))
body = doc.element.body
for child in list(body):
    if child.tag != qn('w:sectPr'):
        body.remove(child)
# bỏ các ảnh của bản nháp khỏi gói (file nhỏ lại)
for rid, rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image'):
        doc.part.drop_rel(rid)
# bỏ ngắt phần thừa: giữ sectPr cuối
sect = body.find(qn('w:sectPr'))
for el in head.elements() + b.elements():
    sect.addprevious(el)
doc.core_properties.title = 'Chương 5 – Thiết kế và xây dựng CSDL Cassandra (đặt xe công nghệ)'
doc.save(str(OUT))
print('Đã tạo', OUT)
print('Hình:', b.fig_n, '| Bảng:', b.tab_n, '| Tài liệu tham khảo:', len(b.ref_order))
print('Thứ tự tài liệu tham khảo:', b.ref_order)
import json
(Path(__file__).parent / 'ref_order.json').write_text(json.dumps(b.ref_order), encoding='utf8')
