-- =====================================================================================
-- ĐÁP ÁN — ĐỀ #2 CASSANDRA (datvexe)
-- ĐÃ chạy thử trên Cassandra 4.1 (Docker cassandra:4.1): kết quả "→" khớp, thông báo lỗi Câu 7 đúng như ghi.
-- Khác biệt khi chạy cả file một lượt: SELECT ngay sau CREATE INDEX có thể báo ReadFailure (index xây bất đồng bộ) — chờ vài giây rồi chạy lại.
-- Thứ tự dòng kết quả giữa CÁC PARTITION khác nhau do token quyết định nên có thể khác; trong 1 partition thì theo clustering.
-- =====================================================================================

-- =====================================================================================
-- BẢNG LUẬT CẦN THUỘC (phần lớn điểm Cassandra nằm ở đây)
-- =====================================================================================
-- R1. WHERE PHẢI có đủ PARTITION KEY (dùng = hoặc IN). Partition key ghép ((a,b)) thì phải có CẢ a VÀ b.
-- R2. Cột CLUSTERING dùng theo ĐÚNG THỨ TỰ khai báo, không được bỏ qua cột đứng trước.
--     Cột trước dùng = (hoặc IN); chỉ cột CUỐI CÙNG bị lọc mới được dùng khoảng (<, >, <=, >=).
--     Đã dùng khoảng ở cột nào thì các cột clustering đứng sau nó không được lọc thêm.
--       PRIMARY KEY ((k), c1, c2, c3):  OK: k | k,c1 | k,c1,c2 | k,c1>x | k,c1=x,c2>y   SAI: k,c2 | k,c1>x,c2=y | k,c1,c3
-- R3. ORDER BY chỉ trên cột CLUSTERING, và phải đúng thứ tự khai báo hoặc ĐẢO NGƯỢC HOÀN TOÀN. Có partition key trong WHERE.
-- R4. Lọc theo cột THƯỜNG (không phải khóa) → báo lỗi, phải thêm ALLOW FILTERING (quét, chậm) hoặc dùng INDEX / MATERIALIZED VIEW / bảng mới.
-- R5. KHÔNG có JOIN, OR, LIKE (trừ khi có index SASI/SAI), !=, subquery. Muốn "nối" → lặp dữ liệu (denormalize) hoặc 2 truy vấn ở app.
-- R6. GROUP BY chỉ trên cột khóa chính, theo thứ tự khóa (partition trước, rồi clustering).
-- R7. UPDATE/DELETE phải có ĐỦ khóa chính (riêng DELETE cho phép dừng ở tiền tố clustering → xóa cả dãy dòng, hoặc chỉ partition key → xóa cả partition).
-- R8. Cột khóa chính KHÔNG được sửa bằng UPDATE (muốn đổi = xóa + insert lại). Không DROP được cột thuộc khóa chính.
-- R9. Đặt bảng theo truy vấn: 1 truy vấn chính ≈ 1 bảng. Chọn partition key phân bố đều, đừng để 1 partition phình quá to (hot partition).
-- =====================================================================================

USE datvexe;

-- ------------------------------- Câu 1 -------------------------------
-- 1a.
CREATE KEYSPACE IF NOT EXISTS datvexe_test WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE datvexe_test;
ALTER KEYSPACE datvexe_test WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2} AND DURABLE_WRITES = false;
DESCRIBE KEYSPACE datvexe_test;
DROP KEYSPACE datvexe_test;
USE datvexe;
-- Lưu ý: tài liệu hướng dẫn viết "WITH replication=... WITH DURABLE_WRITES=..." — cú pháp đúng của CQL là nối bằng AND.
-- Máy 1 node thì replication_factor 2 chỉ để luyện cú pháp (dữ liệu thật thì RF ≤ số node).

-- 1b.
DESCRIBE KEYSPACES;
DESCRIBE TABLES;
DESCRIBE TABLE chuyen_by_tuyen;

-- 1c.
--  chuyen_by_tuyen : PARTITION KEY ma_tuyen | CLUSTERING ngay_khoi_hanh, ma_chuyen | sắp ngay ASC rồi ma_chuyen ASC
--                    → "các chuyến của 1 tuyến, lọc theo ngày / khoảng ngày".
--  ve_by_chuyen    : PARTITION KEY ma_chuyen | CLUSTERING so_ghe | → "các vé / 1 ghế cụ thể của 1 chuyến".
--  ve_by_khach     : PARTITION KEY ma_kh | CLUSTERING ngay_dat DESC, ma_ve ASC → "lịch sử vé của 1 khách, mới nhất trước".
--  doanh_thu_nha_xe: PARTITION KEY GHÉP (nha_xe, thang) | CLUSTERING ngay, ma_chuyen → "doanh thu 1 nhà xe trong 1 tháng theo ngày";
--                    bắt buộc có cả nha_xe VÀ thang trong WHERE. Ghép thêm "thang" để 1 nhà xe không dồn hết vào 1 partition khổng lồ.

-- ------------------------------- Câu 2 -------------------------------
-- 2a. Partition key sdt; clustering ngay_mua DESC, ma_ve (ma_ve để 2 vé cùng ngày không đè nhau).
CREATE TABLE IF NOT EXISTS ve_by_sdt (
    sdt text,
    ngay_mua date,
    ma_ve text,
    ma_chuyen text,
    ten_khach text,
    gia int,
    PRIMARY KEY ((sdt), ngay_mua, ma_ve)
) WITH CLUSTERING ORDER BY (ngay_mua DESC, ma_ve ASC);

INSERT INTO ve_by_sdt (sdt, ngay_mua, ma_ve, ma_chuyen, ten_khach, gia) VALUES ('0901000001', '2026-09-10', 'VE001', 'C001', 'Nguyen Van An', 280000);
INSERT INTO ve_by_sdt (sdt, ngay_mua, ma_ve, ma_chuyen, ten_khach, gia) VALUES ('0901000001', '2026-09-20', 'VE004', 'C002', 'Nguyen Van An', 300000);
INSERT INTO ve_by_sdt JSON '{"sdt": "0902000002", "ngay_mua": "2026-09-12", "ma_ve": "VE002", "ma_chuyen": "C001", "ten_khach": "Tran Thi Binh", "gia": 280000}';
SELECT * FROM ve_by_sdt WHERE sdt = '0901000001';   -- → VE004 (20/09) trước, VE001 (10/09) sau

-- 2b. Partition key ma_tuyen; clustering thoi_gian DESC, ma_kh.
CREATE TABLE IF NOT EXISTS danh_gia_by_tuyen (
    ma_tuyen text,
    thoi_gian timestamp,
    ma_kh text,
    so_sao int,
    nhan_xet text,
    PRIMARY KEY ((ma_tuyen), thoi_gian, ma_kh)
) WITH CLUSTERING ORDER BY (thoi_gian DESC, ma_kh ASC);

INSERT INTO danh_gia_by_tuyen (ma_tuyen, thoi_gian, ma_kh, so_sao, nhan_xet) VALUES ('SG-DL', '2026-09-21 08:30:00', 'KH01', 5, 'Xe sach, tai xe than thien');
INSERT INTO danh_gia_by_tuyen (ma_tuyen, thoi_gian, ma_kh, so_sao, nhan_xet) VALUES ('SG-DL', '2026-09-22 10:00:00', 'KH03', 3, 'Xe tre 30 phut');
INSERT INTO danh_gia_by_tuyen JSON '{"ma_tuyen": "SG-DL", "thoi_gian": "2026-09-23 09:15:00", "ma_kh": "KH02", "so_sao": 4, "nhan_xet": "Ok"}';
SELECT * FROM danh_gia_by_tuyen WHERE ma_tuyen = 'SG-DL';   -- → 23/09, 22/09, 21/09 (mới nhất trước)

-- 2c. Partition key ma_tx; clustering ngay_khoi_hanh, ma_chuyen → lọc được khoảng ngày (luật R2).
CREATE TABLE IF NOT EXISTS chuyen_by_tai_xe (
    ma_tx text,
    ngay_khoi_hanh date,
    ma_chuyen text,
    ma_tuyen text,
    nha_xe text,
    gio_khoi_hanh text,
    PRIMARY KEY ((ma_tx), ngay_khoi_hanh, ma_chuyen)
);

INSERT INTO chuyen_by_tai_xe (ma_tx, ngay_khoi_hanh, ma_chuyen, ma_tuyen, nha_xe, gio_khoi_hanh) VALUES ('TX01', '2026-10-01', 'C001', 'SG-DL', 'Phuong Trang', '06:00');
INSERT INTO chuyen_by_tai_xe (ma_tx, ngay_khoi_hanh, ma_chuyen, ma_tuyen, nha_xe, gio_khoi_hanh) VALUES ('TX01', '2026-10-02', 'C003', 'SG-DL', 'Phuong Trang', '06:00');
INSERT INTO chuyen_by_tai_xe JSON '{"ma_tx": "TX02", "ngay_khoi_hanh": "2026-10-01", "ma_chuyen": "C002", "ma_tuyen": "SG-DL", "nha_xe": "Thanh Buoi", "gio_khoi_hanh": "22:00"}';
SELECT * FROM chuyen_by_tai_xe WHERE ma_tx = 'TX01' AND ngay_khoi_hanh >= '2026-10-01' AND ngay_khoi_hanh <= '2026-10-05';   -- → C001, C003

-- 2d. Nếu partition key chỉ là ma_chuyen thì "các chuyến của tuyến X" phải quét mọi partition (không lọc được theo tuyến/ngày);
--     mỗi chuyến 1 partition rất nhỏ, không sắp được theo ngày. Cassandra KHÔNG có JOIN nên mỗi kiểu truy vấn cần 1 bảng riêng
--     (query-first + denormalization): lặp dữ liệu, đổi lại đọc nhanh (1 partition) và ghi rẻ.

-- ------------------------------- Câu 3 -------------------------------
-- 3a. → C001, C002, C003, C004 (theo ngày rồi ma_chuyen)
SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL';
SELECT ma_chuyen, nha_xe, gia_ve FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL';

-- 3b. → C001, C002
SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND ngay_khoi_hanh = '2026-10-01';

-- 3c. → C003, C002, C001. ORDER BY ngay DESC = đảo ngược HOÀN TOÀN thứ tự clustering nên ma_chuyen cũng đảo (C002 trước C001).
SELECT * FROM chuyen_by_tuyen
WHERE ma_tuyen = 'SG-DL' AND ngay_khoi_hanh >= '2026-10-01' AND ngay_khoi_hanh <= '2026-10-02'
ORDER BY ngay_khoi_hanh DESC;

-- 3d. → C001, C002, C004
SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND ngay_khoi_hanh IN ('2026-10-01', '2026-10-05');

-- 3e. → C001, C003. nha_xe là cột thường nên bắt buộc ALLOW FILTERING (đã có partition key nên vẫn chỉ quét 1 partition).
SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' AND nha_xe = 'Phuong Trang' ALLOW FILTERING;

-- 3f. → so_chuyen 4 | re_nhat 280000 | dat_nhat 320000 | trung_binh 297500 | tong 1190000
--     (AVG của cột int trả về int — cắt phần thập phân)
SELECT COUNT(*) AS so_chuyen, MIN(gia_ve) AS re_nhat, MAX(gia_ve) AS dat_nhat, AVG(gia_ve) AS trung_binh, SUM(gia_ve) AS tong
FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL';

-- 3g. → VE002, Tran Thi Binh
SELECT * FROM ve_by_chuyen WHERE ma_chuyen = 'C001' AND so_ghe = 'A02';

-- 3h. → so_ve 3 | tong 840000
SELECT COUNT(*) AS so_ve, SUM(gia) AS tong FROM ve_by_chuyen WHERE ma_chuyen = 'C001';

-- 3i. → VE001, VE002. da_thanh_toan là cột thường → ALLOW FILTERING.
SELECT * FROM ve_by_chuyen WHERE ma_chuyen = 'C001' AND da_thanh_toan = true ALLOW FILTERING;

-- 3j. → C001, C002
SELECT * FROM chuyen_by_tuyen WHERE ma_tuyen = 'SG-DL' LIMIT 2;

-- 3k. → VE004 (20/09/2026). Bảng đã CLUSTERING ORDER ngay_dat DESC nên dòng đầu là mới nhất → LIMIT 1 là đủ.
SELECT * FROM ve_by_khach WHERE ma_kh = 'KH01' LIMIT 1;

-- 3l. [NÂNG CAO]
SELECT DISTINCT ma_tuyen FROM chuyen_by_tuyen;                                              -- → SG-DL, SG-NT, HN-HP (chỉ được DISTINCT trên partition key)
SELECT ma_tuyen, COUNT(*) AS so_chuyen, AVG(gia_ve) AS gia_tb FROM chuyen_by_tuyen GROUP BY ma_tuyen;
--   → SG-DL 4 / 297500 | SG-NT 2 / 245000 | HN-HP 2 / 155000
SELECT * FROM chuyen_by_tuyen PER PARTITION LIMIT 1;                                        -- → C001 (SG-DL), C005 (SG-NT), C007 (HN-HP)
--   LIMIT chặn tổng số dòng; PER PARTITION LIMIT chặn số dòng MỖI partition.

-- 3m. → tong 1340000, so_dong 2 (C001 840000 + C005 500000; tháng 2026-11 nằm partition khác nên không tính)
SELECT SUM(doanh_thu) AS tong, COUNT(*) AS so_dong FROM doanh_thu_nha_xe WHERE nha_xe = 'Phuong Trang' AND thang = '2026-10';
SELECT SUM(doanh_thu) AS tong FROM doanh_thu_nha_xe
WHERE nha_xe = 'Phuong Trang' AND thang = '2026-10' AND ngay >= '2026-10-01' AND ngay <= '2026-10-15';   -- → 1340000

-- ------------------------------- Câu 4 -------------------------------
-- 4a. → set hiển thị sắp xếp tăng dần; map theo key; list theo thứ tự chèn
SELECT ho_ten, sdt, dia_chi, tuyen_hay_di FROM khach_hang WHERE ma_kh = 'KH01';

-- 4b. Set: + để thêm, - để bớt (set không có phần tử trùng, không có thứ tự chèn)
UPDATE khach_hang SET sdt = sdt + {'0988999000'} WHERE ma_kh = 'KH01';
UPDATE khach_hang SET sdt = sdt - {'0911000001'} WHERE ma_kh = 'KH01';
-- → sdt = {'0901000001', '0988999000'}

-- 4c. Map: gán theo key / cộng map / DELETE theo key
UPDATE khach_hang SET dia_chi['que'] = 'Long An' WHERE ma_kh = 'KH01';        -- hoặc: SET dia_chi = dia_chi + {'que': 'Long An'}
UPDATE khach_hang SET dia_chi['nha'] = 'Son Tra, Da Nang' WHERE ma_kh = 'KH03';
DELETE dia_chi['cong_ty'] FROM khach_hang WHERE ma_kh = 'KH01';               -- (hoặc: SET dia_chi = dia_chi - {'cong_ty'})

-- 4d. List: giữ thứ tự, cho phép trùng. Ban đầu KH03: ['SG-DL']
UPDATE khach_hang SET tuyen_hay_di = tuyen_hay_di + ['HN-HP'] WHERE ma_kh = 'KH03';     -- ['SG-DL', 'HN-HP']
UPDATE khach_hang SET tuyen_hay_di = ['SG-NT'] + tuyen_hay_di WHERE ma_kh = 'KH03';     -- ['SG-NT', 'SG-DL', 'HN-HP']
UPDATE khach_hang SET tuyen_hay_di[0] = 'DN-HUE' WHERE ma_kh = 'KH03';                  -- ['DN-HUE', 'SG-DL', 'HN-HP']
UPDATE khach_hang SET tuyen_hay_di = tuyen_hay_di - ['SG-DL'] WHERE ma_kh = 'KH03';     -- ['DN-HUE', 'HN-HP']  (xóa mọi phần tử có giá trị đó)
-- Xóa theo vị trí: DELETE tuyen_hay_di[1] FROM khach_hang WHERE ma_kh = 'KH03';
-- Lưu ý: sửa/xóa list theo vị trí buộc Cassandra đọc trước khi ghi → chậm; set/map nên ưu tiên khi được.

-- 4e. [NÂNG CAO] Collection KHÔNG lọc trực tiếp được nếu chưa có index. CONTAINS dành cho set/list/map values; CONTAINS KEY cho map key.
CREATE INDEX IF NOT EXISTS idx_sdt ON khach_hang (sdt);
SELECT ma_kh, ho_ten FROM khach_hang WHERE sdt CONTAINS '0902000002';                   -- → KH02
CREATE INDEX IF NOT EXISTS idx_dia_chi_key ON khach_hang (KEYS(dia_chi));
SELECT ma_kh, ho_ten FROM khach_hang WHERE dia_chi CONTAINS KEY 'cong_ty';              -- → rỗng nếu đã chạy 4c (KH01 bị xóa key này); chạy lại phần chuẩn bị để thấy KH01

-- ------------------------------- Câu 5 -------------------------------
-- 5a.
INSERT INTO chuyen_by_tuyen JSON '{"ma_tuyen": "SG-DL", "ngay_khoi_hanh": "2026-10-06", "ma_chuyen": "C009", "nha_xe": "Hoang Long", "gio_khoi_hanh": "08:00", "gia_ve": 310000, "so_cho": 28, "bien_so": "51B-33333"}';

-- 5b. UPDATE phải có ĐỦ khóa chính (ma_tuyen + ngay_khoi_hanh + ma_chuyen). Chỉ có ma_chuyen = 'C001' thì báo lỗi.
UPDATE chuyen_by_tuyen SET gia_ve = 290000 WHERE ma_tuyen = 'SG-DL' AND ngay_khoi_hanh = '2026-10-01' AND ma_chuyen = 'C001';

-- 5c.
UPDATE ve_by_chuyen SET da_thanh_toan = true WHERE ma_chuyen = 'C001' AND so_ghe = 'A03';

-- 5d. DELETE cột: chỉ đặt cột về null, dòng vẫn còn. DELETE FROM: xóa dòng.
DELETE sdt FROM ve_by_chuyen WHERE ma_chuyen = 'C005' AND so_ghe = 'A02';
DELETE FROM chuyen_by_tuyen WHERE ma_tuyen = 'HN-HP' AND ngay_khoi_hanh = '2026-10-02' AND ma_chuyen = 'C008';
DELETE FROM chuyen_by_tuyen WHERE ma_tuyen = 'HN-HP' AND ngay_khoi_hanh = '2026-10-01';   -- dừng ở tiền tố clustering → xóa cả dãy (C007)
-- Xóa cả partition: DELETE FROM chuyen_by_tuyen WHERE ma_tuyen = 'HN-HP';

-- 5e.
ALTER TABLE chuyen_by_tuyen ADD ghi_chu text;
ALTER TABLE chuyen_by_tuyen DROP ghi_chu;
-- (Không thể ADD/DROP cột khóa chính. Đổi kiểu cột thường cũng bị hạn chế.)

-- 5f. [NÂNG CAO] Counter: không INSERT được, chỉ UPDATE cộng/trừ; dòng chưa có sẽ tự tạo (bắt đầu từ 0).
UPDATE thong_ke_tuyen SET so_ve_ban = so_ve_ban + 1 WHERE ma_tuyen = 'SG-DL';
UPDATE thong_ke_tuyen SET so_ve_ban = so_ve_ban + 1 WHERE ma_tuyen = 'SG-DL';
UPDATE thong_ke_tuyen SET so_ve_ban = so_ve_ban + 1 WHERE ma_tuyen = 'SG-DL';
UPDATE thong_ke_tuyen SET so_ve_ban = so_ve_ban + 2 WHERE ma_tuyen = 'SG-NT';
SELECT * FROM thong_ke_tuyen;                                                    -- → SG-DL 3 | SG-NT 2

-- 5g. [NÂNG CAO] TTL: sau 60 giây dòng tự biến mất.
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, gia, da_thanh_toan) VALUES ('C001', 'A04', 'VE009', 'Giu cho tam', 280000, false) USING TTL 60;
SELECT ma_ve, ten_khach, TTL(ten_khach) FROM ve_by_chuyen WHERE ma_chuyen = 'C001' AND so_ghe = 'A04';   -- TTL ≈ 60 giảm dần

-- 5h. [NÂNG CAO] Lightweight transaction (LWT, dùng Paxos — chậm hơn ghi thường).
INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, gia, da_thanh_toan) VALUES ('C001', 'A01', 'VE010', 'Trung ghe', 280000, false) IF NOT EXISTS;
--   → [applied] = False kèm dòng đang tồn tại (VE001) — không ghi đè.
UPDATE ve_by_chuyen SET da_thanh_toan = true WHERE ma_chuyen = 'C001' AND so_ghe = 'A03' IF da_thanh_toan = false;
--   → [applied] = True nếu trước đó A03 chưa thanh toán; nếu đã true (đã chạy 5c) thì [applied] = False.

-- 5i. [NÂNG CAO] BATCH giữ 2 bảng lặp dữ liệu nhất quán (logged batch: hoặc ghi cả hai hoặc không ghi gì — đảm bảo nguyên tử, KHÔNG đảm bảo cô lập).
BEGIN BATCH
    INSERT INTO ve_by_chuyen (ma_chuyen, so_ghe, ma_ve, ten_khach, sdt, gia, da_thanh_toan) VALUES ('C004', 'A01', 'VE011', 'Nguyen Van An', '0901000001', 320000, true);
    INSERT INTO ve_by_khach (ma_kh, ngay_dat, ma_ve, ma_chuyen, ma_tuyen, gia) VALUES ('KH01', '2026-09-28', 'VE011', 'C004', 'SG-DL', 320000);
APPLY BATCH;
-- Lặp vì: ve_by_chuyen phục vụ "vé của chuyến", ve_by_khach phục vụ "lịch sử của khách" — khác partition key nên không thể dùng chung 1 bảng.
-- Đừng lạm dụng BATCH để "gộp cho nhanh" (batch nhiều partition làm chậm coordinator).

-- 5j. [NÂNG CAO] Lệnh của cqlsh (không phải CQL thuần), chạy trong cqlsh chứ không phải TablePlus.
COPY chuyen_by_tuyen TO 'chuyen.csv' WITH HEADER = TRUE;
-- Nhập lại: KHÔNG liệt kê cột (hoặc liệt kê ĐÚNG thứ tự cột của file vừa xuất). COPY TO xuất theo thứ tự cột của bảng:
-- ma_tuyen, ngay_khoi_hanh, ma_chuyen, bien_so, gia_ve, gio_khoi_hanh, nha_xe, so_cho (cột khóa trước, cột thường theo thứ tự chữ cái).
-- Liệt kê sai thứ tự sẽ lỗi "ParseError - Failed to parse 06:00 : invalid literal for int()" (đã gặp khi chạy thử).
COPY chuyen_by_tuyen FROM 'chuyen.csv' WITH HEADER = TRUE;
TRUNCATE ve_by_khach;    -- xóa hết dữ liệu, giữ bảng. DROP TABLE mới xóa luôn cấu trúc.

-- ------------------------------- Câu 6 -------------------------------
-- 6a. MV phải: chọn các cột từ bảng gốc; WHERE ... IS NOT NULL cho MỌI cột khóa của view; PRIMARY KEY của view
--     phải chứa TẤT CẢ cột khóa chính của bảng gốc (ở đây chỉ ma_kh) + tối đa 1 cột thường của bảng gốc (thanh_pho).
CREATE MATERIALIZED VIEW IF NOT EXISTS khach_by_thanh_pho AS
    SELECT thanh_pho, ma_kh, ho_ten, email
    FROM khach_hang
    WHERE thanh_pho IS NOT NULL AND ma_kh IS NOT NULL
    PRIMARY KEY ((thanh_pho), ma_kh);
SELECT * FROM khach_by_thanh_pho WHERE thanh_pho = 'TPHCM';                     -- → KH01, KH04

-- 6b.
CREATE MATERIALIZED VIEW IF NOT EXISTS chuyen_by_nha_xe AS
    SELECT nha_xe, ngay_khoi_hanh, ma_tuyen, ma_chuyen, gio_khoi_hanh, gia_ve
    FROM chuyen_by_tuyen
    WHERE nha_xe IS NOT NULL AND ma_tuyen IS NOT NULL AND ngay_khoi_hanh IS NOT NULL AND ma_chuyen IS NOT NULL
    PRIMARY KEY ((nha_xe), ngay_khoi_hanh, ma_tuyen, ma_chuyen)
    WITH CLUSTERING ORDER BY (ngay_khoi_hanh DESC, ma_tuyen ASC, ma_chuyen ASC);
SELECT * FROM chuyen_by_nha_xe WHERE nha_xe = 'Phuong Trang';                   -- → C003 (10-02), C001 (10-01, SG-DL), C005 (10-01, SG-NT)
INSERT INTO chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gio_khoi_hanh, gia_ve, so_cho, bien_so) VALUES ('SG-VT', '2026-10-09', 'C012', 'Phuong Trang', '05:30', 130000, 40, '51B-77777');
SELECT * FROM chuyen_by_nha_xe WHERE nha_xe = 'Phuong Trang';                   -- → C012 (09/10) xuất hiện đầu tiên — view tự cập nhật

-- 6c. [NÂNG CAO]
CREATE INDEX IF NOT EXISTS idx_ten_khach ON ve_by_chuyen (ten_khach);
SELECT ma_ve, ma_chuyen, so_ghe FROM ve_by_chuyen WHERE ten_khach = 'Nguyen Van An';     -- → VE001 (C001, A01), VE004 (C002, B01) [+ VE011 nếu đã chạy 5i]
--   Nhược điểm: index nằm cục bộ trên từng node → truy vấn phải hỏi nhiều node (chậm, không mở rộng tốt);
--   kém với cột có cardinality rất cao (mỗi giá trị 1 dòng) hoặc rất thấp (boolean); mỗi lần ghi thêm chi phí cập nhật index.
--   Nên dùng: bảng thiết kế riêng / MV cho truy vấn chính; index chỉ cho truy vấn phụ, có kèm partition key.

-- 6d. Phải DROP các view phụ thuộc trước, rồi mới DROP bảng gốc.
DROP MATERIALIZED VIEW IF EXISTS chuyen_by_nha_xe;
DROP TABLE IF EXISTS chuyen_by_tuyen;      -- (đừng chạy nếu còn cần bảng)

-- ------------------------------- Câu 7 -------------------------------
-- 7a. LỖI. Thiếu partition key (ma_tuyen). Báo "Cannot execute this query as it might involve data filtering..."
--     Sửa: thêm ma_tuyen (tốt nhất); hoặc ALLOW FILTERING (quét toàn cluster — chỉ khi dữ liệu nhỏ); hoặc tạo bảng/MV có ngay_khoi_hanh làm partition.
-- 7b. LỖI. Bỏ qua clustering column ngay_khoi_hanh: ma_chuyen không thể bị hạn chế khi cột đứng trước (ngay_khoi_hanh) chưa được hạn chế (R2).
--     Sửa: thêm AND ngay_khoi_hanh = '...' ; hoặc ALLOW FILTERING.
-- 7c. LỖI. ORDER BY chỉ dùng được với clustering column (R3); gia_ve là cột thường. ALLOW FILTERING cũng không cứu được.
--     Sửa: tạo bảng mới có gia_ve làm clustering column; hoặc sắp xếp ở ứng dụng.
-- 7d. LỖI. Đã dùng khoảng (>) trên ngay_khoi_hanh thì không được lọc = trên cột clustering đứng sau (ma_chuyen) (R2). Sửa: ALLOW FILTERING, hoặc lọc ma_chuyen ở ứng dụng.
-- 7e. CHẠY ĐƯỢC. IN trên partition key hợp lệ (đọc 2 partition) → C001–C004 và C005, C006. Nhưng nhiều partition → coordinator phải gom, chậm hơn; đừng IN quá nhiều giá trị.
-- 7f. LỖI. UPDATE phải có ĐỦ khóa chính (ma_chuyen + so_ghe) (R7). ma_ve không phải khóa nên không tìm được dòng. Sửa: WHERE ma_chuyen = 'C001' AND so_ghe = 'A01'.
-- 7g. LỖI. LIKE không hỗ trợ trên cột thường (chỉ có khi có index SASI/SAI). Sửa: tạo bảng tra theo ho_ten; hoặc dùng công cụ tìm kiếm ngoài (Elasticsearch...); hoặc regex ở ứng dụng.
-- 7h. LỖI. GROUP BY chỉ trên cột khóa chính theo thứ tự (R6); nha_xe là cột thường. Sửa: dùng MV/bảng chuyen_by_nha_xe rồi GROUP BY nha_xe (nha_xe là partition key của view).
-- 7i. LỖI. Composite partition key (nha_xe, thang) — thiếu 'thang': phải có ĐỦ mọi thành phần partition key (R1).
--     Thông báo thật: "Cannot execute this query as it might involve data filtering..." (giống 7a). Sửa: thêm AND thang = '2026-10'.
-- 7j. LỖI. Bỏ qua clustering ngay (chỉ có ma_chuyen) → như 7b. Sửa: thêm ngay = '2026-10-01'.
-- 7k. CHẠY ĐƯỢC NHƯNG CẦN ALLOW FILTERING. Có partition key nhưng lọc khoảng trên cột thường gia_ve. Kết quả: C001 (280000), C002 (300000), C003 (290000).
-- 7l. KHÔNG JOIN được (R5). Cách làm: (1) lặp dữ liệu: đưa nha_xe vào bảng vé (denormalize); (2) hoặc 2 truy vấn ở app:
--     SELECT ma_chuyen FROM ve_by_chuyen ... rồi SELECT nha_xe FROM chuyen_by_tuyen ... (cần biết ma_tuyen + ngay).

-- ------------------------------- Câu 8 -------------------------------
-- (đoạn C# mẫu theo mục 2.5 tài liệu — cú pháp driver 3.x giống tài liệu)
--
-- using Cassandra;
-- var cluster = Cluster.Builder().AddContactPoint("127.0.0.1").Build();
-- var session = cluster.Connect("datvexe");
--
-- // 8a. Thêm
-- var ins = session.Prepare("insert into chuyen_by_tuyen (ma_tuyen, ngay_khoi_hanh, ma_chuyen, nha_xe, gia_ve) values (?,?,?,?,?)");
-- session.Execute(ins.Bind("SG-DL", new LocalDate(2026, 10, 7), "C013", "Hoang Long", 315000));
--
-- // 8b. Truy vấn theo tham số + duyệt
-- var sel = session.Prepare("select ma_chuyen, gia_ve from chuyen_by_tuyen where ma_tuyen = ?");
-- var rowSet = session.Execute(sel.Bind("SG-DL"));
-- foreach (var row in rowSet)
--     Console.WriteLine(row.GetValue<string>("ma_chuyen") + " - " + row.GetValue<int>("gia_ve"));
--
-- // 8c. Sửa (đủ khóa chính)
-- var upd = session.Prepare("update chuyen_by_tuyen set gia_ve = ? where ma_tuyen = ? and ngay_khoi_hanh = ? and ma_chuyen = ?");
-- session.Execute(upd.Bind(295000, "SG-DL", new LocalDate(2026, 10, 1), "C001"));
-- // Kiểu date trong C# driver là LocalDate; tài liệu dùng row["ten_cot"] cho cách đọc đơn giản.
