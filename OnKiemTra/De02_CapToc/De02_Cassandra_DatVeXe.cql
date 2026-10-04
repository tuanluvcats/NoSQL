-- =====================================================================================
-- ĐỀ TƯƠNG TỰ #2 (CẤP TỐC) — CASSANDRA — 4 điểm / 10 (chiếm 40% điểm)
-- Chủ đề: ĐẶT VÉ XE KHÁCH LIÊN TỈNH
--
-- Cách làm:  1) Chạy PHẦN CHUẨN BỊ (keyspace + bảng + dữ liệu) — đề cho sẵn lược đồ.
--            2) Tự viết lệnh cho Câu 1 → Câu 8 ngay dưới mỗi yêu cầu.
--            3) Làm xong mới mở DapAn02_Cassandra.cql (có kết quả mong đợi + bảng luật WHERE).
-- Chạy được bằng: cqlsh, TablePlus (như bài Tuần 3), hoặc docker exec -it nosql-cassandra cqlsh
-- Lưu ý:     - Chạy TỪNG LỆNH một (Ctrl+Enter trong TablePlus), không bôi đen cả file.
--            - [NÂNG CAO] = ngoài bài tập trong tài liệu / slide, nhưng rất hay ra trong đề kiểm tra Cassandra.
--            - Các câu SELECT: nếu lệnh báo lỗi thì ĐỌC thông báo lỗi, đó chính là kiến thức cần ôn (Câu 7).
-- Thang điểm: C1: 0,4 | C2: 0,6 | C3: 1,0 | C4: 0,5 | C5: 0,5 | C6: 0,4 | C7: 0,4 | C8: 0,2
-- =====================================================================================


-- =====================================================================================
-- PHẦN CHUẨN BỊ — CHẠY TRƯỚC
-- =====================================================================================

CREATE KEYSPACE IF NOT EXISTS datvexe
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE datvexe;

-- Bảng 1: chuyến xe theo tuyến (query: các chuyến của một tuyến, theo ngày)
CREATE TABLE IF NOT EXISTS chuyen_by_tuyen (
    ma_tuyen text,
    ngay_khoi_hanh date,
    ma_chuyen text,
    nha_xe text,
    gio_khoi_hanh text,
    gia_ve int,
    so_cho int,
    bien_so text,
    PRIMARY KEY ((ma_tuyen), ngay_khoi_hanh, ma_chuyen)
) WITH CLUSTERING ORDER BY (ngay_khoi_hanh ASC, ma_chuyen ASC);

-- Bảng 2: vé theo chuyến (query: các vé / ghế của một chuyến)
CREATE TABLE IF NOT EXISTS ve_by_chuyen (
    ma_chuyen text,
    so_ghe text,
    ma_ve text,
    ten_khach text,
    sdt text,
    gia int,
    da_thanh_toan boolean,
    PRIMARY KEY ((ma_chuyen), so_ghe)
);

-- Bảng 3: khách hàng (có collection: set, map, list)
CREATE TABLE IF NOT EXISTS khach_hang (
    ma_kh text PRIMARY KEY,
    ho_ten text,
    email text,
    thanh_pho text,
    sdt set<text>,
    dia_chi map<text, text>,
    tuyen_hay_di list<text>
);

-- Bảng 4: lịch sử đặt vé của khách (mới nhất trước)
CREATE TABLE IF NOT EXISTS ve_by_khach (
    ma_kh text,
    ngay_dat date,
    ma_ve text,
    ma_chuyen text,
    ma_tuyen text,
    gia int,
    PRIMARY KEY ((ma_kh), ngay_dat, ma_ve)
) WITH CLUSTERING ORDER BY (ngay_dat DESC, ma_ve ASC);

-- Bảng 5: doanh thu theo nhà xe + tháng (composite PARTITION key)
CREATE TABLE IF NOT EXISTS doanh_thu_nha_xe (
    nha_xe text,
    thang text,
    ngay date,
    ma_chuyen text,
    so_ve_ban int,
    doanh_thu int,
    PRIMARY KEY ((nha_xe, thang), ngay, ma_chuyen)
);

-- Bảng 6: bộ đếm (counter)
CREATE TABLE IF NOT EXISTS thong_ke_tuyen (
    ma_tuyen text PRIMARY KEY,
    so_ve_ban counter
);

-- ---- Dữ liệu chuyen_by_tuyen
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-DL', '2026-10-01', 'C001', 'Phuong Trang', '06:00', 280000, 40, '51B-11111');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-DL', '2026-10-01', 'C002', 'Thanh Buoi', '22:00', 300000, 34, '51B-22222');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-DL', '2026-10-02', 'C003', 'Phuong Trang', '06:00', 290000, 40, '51B-11111');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-DL', '2026-10-05', 'C004', 'Hoang Long', '09:00', 320000, 28, '51B-33333');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-NT', '2026-10-01', 'C005', 'Phuong Trang', '21:00', 250000, 40, '51B-44444');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-NT', '2026-10-03', 'C006', 'Thanh Buoi', '20:30', 240000, 34, '51B-55555');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('HN-HP', '2026-10-01', 'C007', 'Hoang Long', '07:00', 150000, 30, '29B-66666');
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('HN-HP', '2026-10-02', 'C008', 'Hoang Long', '15:00', 160000, 30, '29B-66666');

-- ---- Dữ liệu ve_by_chuyen
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C001', 'A01', 'VE001', 'Nguyen Van An', '0901000001', 280000, true);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C001', 'A02', 'VE002', 'Tran Thi Binh', '0902000002', 280000, true);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C001', 'A03', 'VE003', 'Le Van Cuong', '0903000003', 280000, false);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C002', 'B01', 'VE004', 'Nguyen Van An', '0901000001', 300000, true);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C002', 'B02', 'VE005', 'Pham Thi Dung', '0904000004', 300000, true);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C005', 'A01', 'VE006', 'Tran Thi Binh', '0902000002', 250000, true);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C005', 'A02', 'VE007', 'Hoang Van Em', '0905000005', 250000, false);
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C007', 'A01', 'VE008', 'Vo Thi Phuong', '0906000006', 150000, true);

-- ---- Dữ liệu khach_hang  (set dùng { }, map dùng { 'k':'v' }, list dùng [ ])
INSERT INTO khach_hang (ma_kh, ho_ten, email, thanh_pho, sdt, dia_chi, tuyen_hay_di) VALUES ('KH01', 'Nguyen Van An', 'an@mail.com', 'TPHCM', {'0901000001', '0911000001'}, {'nha': 'Q1, TPHCM', 'cong_ty': 'Q7, TPHCM'}, ['SG-DL', 'SG-NT']);
INSERT INTO khach_hang (ma_kh, ho_ten, email, thanh_pho, sdt, dia_chi, tuyen_hay_di) VALUES ('KH02', 'Tran Thi Binh', 'binh@mail.com', 'Ha Noi', {'0902000002'}, {'nha': 'Cau Giay, Ha Noi'}, ['SG-NT', 'HN-HP']);
INSERT INTO khach_hang (ma_kh, ho_ten, email, thanh_pho, sdt, dia_chi, tuyen_hay_di) VALUES ('KH03', 'Le Van Cuong', 'cuong@mail.com', 'Da Nang', {'0903000003'}, {'nha': 'Hai Chau, Da Nang'}, ['SG-DL']);
INSERT INTO khach_hang (ma_kh, ho_ten, email, thanh_pho, sdt, dia_chi, tuyen_hay_di) VALUES ('KH04', 'Pham Thi Dung', 'dung@mail.com', 'TPHCM', {'0904000004', '0914000004'}, {'nha': 'Thu Duc, TPHCM'}, ['SG-DL']);

-- ---- Dữ liệu ve_by_khach
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH01', '2026-09-10', 'VE001', 'C001', 'SG-DL', 280000);
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH01', '2026-09-20', 'VE004', 'C002', 'SG-DL', 300000);
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH02', '2026-09-12', 'VE002', 'C001', 'SG-DL', 280000);
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH02', '2026-09-25', 'VE006', 'C005', 'SG-NT', 250000);
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH03', '2026-09-15', 'VE003', 'C001', 'SG-DL', 280000);
INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH04', '2026-09-22', 'VE005', 'C002', 'SG-DL', 300000);

-- ---- Dữ liệu doanh_thu_nha_xe (số liệu tổng hợp, không cần khớp 100% với ve_by_chuyen)
INSERT INTO doanh_thu_nha_xe (nha_xe, thang, ngay, ma_chuyen, so_ve_ban, doanh_thu) VALUES ('Phuong Trang', '2026-10', '2026-10-01', 'C001', 3, 840000);
INSERT INTO doanh_thu_nha_xe (nha_xe, thang, ngay, ma_chuyen, so_ve_ban, doanh_thu) VALUES ('Phuong Trang', '2026-10', '2026-10-01', 'C005', 2, 500000);
INSERT INTO doanh_thu_nha_xe (nha_xe, thang, ngay, ma_chuyen, so_ve_ban, doanh_thu) VALUES ('Phuong Trang', '2026-11', '2026-11-02', 'C011', 5, 1450000);
INSERT INTO doanh_thu_nha_xe (nha_xe, thang, ngay, ma_chuyen, so_ve_ban, doanh_thu) VALUES ('Thanh Buoi', '2026-10', '2026-10-01', 'C002', 2, 600000);
INSERT INTO doanh_thu_nha_xe (nha_xe, thang, ngay, ma_chuyen, so_ve_ban, doanh_thu) VALUES ('Hoang Long', '2026-10', '2026-10-01', 'C007', 1, 150000);


-- =====================================================================================
-- Câu 1. (0,4đ) Keyspace và cấu trúc bảng
-- =====================================================================================

-- 1a. Trên keyspace PHỤ tên datvexe_test (để khỏi làm hỏng datvexe): tạo (SimpleStrategy, replication_factor 1) → dùng (USE)
--     → thay đổi replication_factor thành 2 và DURABLE_WRITES = false → xem cấu trúc keyspace → xóa keyspace.
--     Sau khi xong nhớ USE datvexe; để quay lại.


-- 1b. Liệt kê tất cả keyspace, tất cả bảng của datvexe, xem cấu trúc bảng chuyen_by_tuyen.


-- 1c. Với mỗi bảng chuyen_by_tuyen, ve_by_chuyen, ve_by_khach, doanh_thu_nha_xe: cho biết đâu là
--     PARTITION KEY, đâu là CLUSTERING KEY, dữ liệu trong 1 partition được sắp theo thứ tự nào,
--     và bảng đó phục vụ truy vấn nào.



-- =====================================================================================
-- Câu 2. (0,6đ) Thiết kế bảng theo truy vấn (query-first) và thêm dữ liệu
-- =====================================================================================
-- Với MỖI yêu cầu truy vấn dưới đây: (i) viết CREATE TABLE phù hợp (chỉ rõ partition key / clustering key,
-- kiểu dữ liệu, CLUSTERING ORDER nếu cần); (ii) thêm 2 dòng bằng INSERT ... VALUES và 1 dòng bằng INSERT ... JSON;
-- (iii) viết SELECT thỏa yêu cầu.

-- 2a. "Tra cứu tất cả vé theo SỐ ĐIỆN THOẠI khách, vé mới mua hiển thị trước."
--     (cột gợi ý: sdt, ngay_mua (date), ma_ve, ma_chuyen, ten_khach, gia)


-- 2b. "Xem các đánh giá của một tuyến xe, đánh giá mới nhất hiển thị trước."
--     (cột gợi ý: ma_tuyen, thoi_gian (timestamp), ma_kh, so_sao (int), nhan_xet)


-- 2c. "Xem các chuyến do một TÀI XẾ phụ trách trong một khoảng ngày."
--     (cột gợi ý: ma_tx, ngay_khoi_hanh, ma_chuyen, ma_tuyen, nha_xe, gio_khoi_hanh)


-- 2d. Giải thích ngắn: vì sao KHÔNG nên dùng ma_chuyen làm partition key duy nhất của bảng chuyen_by_tuyen?
--     Vì sao cùng một dữ liệu chuyến xe ta lại tạo thêm bảng chuyen_by_tai_xe (lặp dữ liệu) thay vì "JOIN"?



-- =====================================================================================
-- Câu 3. (1,0đ) Truy vấn dữ liệu: SELECT ... FROM ... WHERE
-- =====================================================================================

-- 3a. Liệt kê tất cả chuyến của tuyến "SG-DL". Sau đó chỉ hiển thị ma_chuyen, nha_xe, gia_ve.


-- 3b. Liệt kê các chuyến của tuyến "SG-DL" khởi hành ngày 01/10/2026.


-- 3c. Liệt kê các chuyến của tuyến "SG-DL" khởi hành từ 01/10/2026 đến 02/10/2026, sắp xếp NGÀY GIẢM DẦN.


-- 3d. Liệt kê các chuyến của tuyến "SG-DL" khởi hành vào ngày 01/10/2026 HOẶC 05/10/2026 (dùng IN).


-- 3e. Liệt kê các chuyến của tuyến "SG-DL" do nhà xe "Phuong Trang" chạy. (Gợi ý: nha_xe không phải cột khóa.)


-- 3f. Với tuyến "SG-DL": cho biết số chuyến, giá vé thấp nhất, cao nhất, trung bình và tổng giá vé
--     (đặt tên cột bằng AS: so_chuyen, re_nhat, dat_nhat, trung_binh, tong).


-- 3g. Cho biết thông tin vé của chuyến "C001" ở ghế "A02".


-- 3h. Với chuyến "C001": đếm số vé đã bán và tổng tiền vé (COUNT, SUM, đặt tên AS).


-- 3i. Liệt kê các vé ĐÃ THANH TOÁN (da_thanh_toan = true) của chuyến "C001".


-- 3j. Lấy 2 chuyến đầu tiên của tuyến "SG-DL".


-- 3k. Cho biết vé GẦN NHẤT mà khách "KH01" đã đặt (chỉ 1 dòng).


-- 3l. [NÂNG CAO] Cho biết danh sách các tuyến khác nhau có trong bảng chuyen_by_tuyen (DISTINCT).
--     Thống kê số chuyến và giá vé trung bình của MỖI tuyến (GROUP BY).
--     Mỗi tuyến chỉ lấy 1 chuyến sớm nhất (PER PARTITION LIMIT).


-- 3m. Cho biết tổng doanh thu (SUM) và số dòng của nhà xe "Phuong Trang" trong tháng "2026-10" (bảng doanh_thu_nha_xe).
--     Rồi giới hạn thêm: chỉ các ngày từ 2026-10-01 đến 2026-10-15.



-- =====================================================================================
-- Câu 4. (0,5đ) Kiểu dữ liệu tập hợp: SET, MAP, LIST
-- =====================================================================================

-- 4a. Xem ho_ten, sdt, dia_chi, tuyen_hay_di của khách "KH01".


-- 4b. Thêm số điện thoại '0988999000' vào tập sdt của KH01. Sau đó xóa số '0911000001' khỏi tập này.


-- 4c. Thêm địa chỉ 'que' = 'Long An' vào map dia_chi của KH01. Sửa địa chỉ 'nha' của KH03 thành 'Son Tra, Da Nang'.
--     Xóa khóa 'cong_ty' khỏi map dia_chi của KH01.


-- 4d. Trong list tuyen_hay_di của KH03: (i) thêm 'HN-HP' vào CUỐI; (ii) thêm 'SG-NT' vào ĐẦU; (iii) sửa phần tử ở vị trí 0
--     thành 'DN-HUE'; (iv) xóa phần tử có giá trị 'SG-DL' khỏi list.


-- 4e. [NÂNG CAO] Tìm khách có số điện thoại '0902000002' (tìm TRONG set). Gợi ý: CREATE INDEX + CONTAINS.
--     Tìm khách có khóa 'cong_ty' trong map dia_chi (CONTAINS KEY).



-- =====================================================================================
-- Câu 5. (0,5đ) Thêm / sửa / xóa dữ liệu và sửa cấu trúc bảng
-- =====================================================================================

-- 5a. Thêm chuyến mới bằng INSERT ... JSON: tuyến SG-DL, ngày 2026-10-06, mã C009, nhà xe Hoang Long,
--     giờ 08:00, giá 310000, 28 chỗ, biển số 51B-33333.


-- 5b. Cập nhật gia_ve của chuyến C001 (tuyến SG-DL, ngày 2026-10-01) thành 290000.


-- 5c. Cập nhật da_thanh_toan = true cho vé chuyến C001 ghế A03.


-- 5d. Xóa giá trị cột sdt (chỉ cột đó, giữ dòng) của vé chuyến C005 ghế A02.
--     Xóa hẳn chuyến C008 (tuyến HN-HP, ngày 2026-10-02).
--     Xóa TẤT CẢ các chuyến của tuyến HN-HP ngày 2026-10-01 (chỉ cần 1 lệnh).


-- 5e. Thêm cột ghi_chu (text) vào bảng chuyen_by_tuyen, sau đó xóa cột này.


-- 5f. [NÂNG CAO] Tăng bộ đếm số vé bán của tuyến SG-DL thêm 1 (làm 3 lần), tuyến SG-NT thêm 2, rồi xem kết quả.


-- 5g. [NÂNG CAO] Thêm vé giữ chỗ tạm cho chuyến C001 ghế A04 (ma_ve 'VE009', ten_khach 'Giu cho tam') CHỈ TỒN TẠI 60 giây (TTL);
--     xem thời gian sống còn lại của cột ten_khach.


-- 5h. [NÂNG CAO] Chỉ thêm vé chuyến C001 ghế A01 (ma_ve 'VE010') NẾU chưa có (IF NOT EXISTS). Quan sát cột [applied].
--     Cập nhật da_thanh_toan = true cho chuyến C001 ghế A03 CHỈ KHI hiện tại đang là false (điều kiện IF).


-- 5i. [NÂNG CAO] Khi khách KH01 đặt vé VE011 (chuyến C004, ghế A01, tuyến SG-DL, giá 320000, ngày đặt 2026-09-28)
--     phải ghi đồng thời vào 2 bảng ve_by_chuyen và ve_by_khach. Dùng BATCH để ghi cả hai. Giải thích vì sao phải lặp dữ liệu.


-- 5j. [NÂNG CAO] Xuất dữ liệu bảng chuyen_by_tuyen ra file CSV có dòng tiêu đề, rồi nhập lại vào bảng (lệnh COPY của cqlsh).
--     Xóa toàn bộ dữ liệu bảng ve_by_khach nhưng giữ cấu trúc (TRUNCATE) — KHÔNG chạy nếu còn cần dữ liệu.



-- =====================================================================================
-- Câu 6. (0,4đ) Tối ưu truy vấn: MATERIALIZED VIEW và INDEX
-- =====================================================================================
-- Nếu báo "Materialized views are disabled": mở cassandra.yaml, đặt enable_materialized_views: true
-- (Cassandra 4.0) hoặc materialized_views_enabled: true (4.1), rồi restart Cassandra.

-- 6a. Tạo materialized view khach_by_thanh_pho để tra cứu khách theo thành phố (cột: thanh_pho, ma_kh, ho_ten, email).
--     Truy vấn danh sách khách ở "TPHCM".


-- 6b. Tạo materialized view chuyen_by_nha_xe từ chuyen_by_tuyen để xem các chuyến của một nhà xe, ngày mới nhất trước.
--     Truy vấn các chuyến của nhà xe "Phuong Trang". Quan sát: chèn 1 chuyến mới vào bảng gốc rồi SELECT lại view.


-- 6c. Tạo secondary INDEX trên ve_by_chuyen(ten_khach) và tìm mọi vé của khách "Nguyen Van An" (qua nhiều chuyến).
--     Nêu 1 nhược điểm của secondary index so với materialized view / bảng thiết kế riêng.


-- 6d. Thứ tự xóa đúng khi muốn DROP bảng chuyen_by_tuyen (có view phụ thuộc)?



-- =====================================================================================
-- Câu 7. (0,4đ) Phân tích lỗi: mỗi câu dưới đây có chạy được không? Nếu không, vì sao và cách sửa?
--          (Chạy thử từng câu để xem thông báo lỗi. Cần ghi rõ cả lý do, không chỉ "chạy được / lỗi".)
-- =====================================================================================

-- 7a. SELECT * FROM chuyen_by_tuyen WHERE ngay_khoi_hanh = '2026-10-01';

-- 7b. SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND ma_chuyen = 'C001';

-- 7c. SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' ORDER BY gia_ve;

-- 7d. SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND ngay_khoi_hanh > '2026-10-01' AND ma_chuyen = 'C003';

-- 7e. SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen IN ('SG-DL', 'SG-NT');

-- 7f. UPDATE ve_by_chuyen SET gia = 999000 WHERE ma_ve = 'VE001';

-- 7g. SELECT * FROM khach_hang WHERE ho_ten LIKE 'Nguyen%';

-- 7h. SELECT nha_xe, AVG(gia_ve) FROM chuyen_by_tuyen GROUP BY nha_xe;

-- 7i. SELECT * FROM doanh_thu_nha_xe WHERE nha_xe = 'Phuong Trang';

-- 7j. SELECT * FROM doanh_thu_nha_xe WHERE nha_xe = 'Phuong Trang' AND thang = '2026-10' AND ma_chuyen = 'C001';

-- 7k. SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND gia_ve >= 280000 AND gia_ve <= 300000;

-- 7l. "Cho biết tên khách VÀ tên nhà xe của vé VE001" — dùng JOIN giữa ve_by_chuyen và chuyen_by_tuyen. Cassandra xử lý thế nào?



-- =====================================================================================
-- Câu 8. (0,2đ) Kết nối ứng dụng C# (CassandraCSharpDriver) — mục 2.5 tài liệu hướng dẫn
-- =====================================================================================
-- Kết nối tới Cassandra tại 127.0.0.1, keyspace datvexe. Viết đoạn mã C#:
-- 8a. Thêm 1 chuyến xe mới bằng câu lệnh Prepare + Bind.
-- 8b. Truy vấn các chuyến của một tuyến (tham số hóa ma_tuyen) và duyệt kết quả in ma_chuyen, gia_ve.
-- 8c. Cập nhật gia_ve của một chuyến (theo đủ khóa chính) bằng Prepare + Bind.
