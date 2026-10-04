-- BAI TAP 2.1: QUAN LY CTY DU LICH

CREATE KEYSPACE qldulich
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE qldulich;

CREATE TABLE IF NOT EXISTS khach (
    quoc_tich text,
    so_cccd text,
    ho_ten text,
    PRIMARY KEY (quoc_tich, so_cccd)
) WITH CLUSTERING ORDER BY (so_cccd ASC);

INSERT INTO khach (quoc_tich, so_cccd, ho_ten) VALUES ('Malaysia', 'MY0001', 'Ahmad Faiz');
INSERT INTO khach (quoc_tich, so_cccd, ho_ten) VALUES ('Malaysia', 'MY0002', 'Nurul Aina');
INSERT INTO khach (quoc_tich, so_cccd, ho_ten) VALUES ('Trung quốc', 'CN0001', 'Zhang Wei');
INSERT INTO khach (quoc_tich, so_cccd, ho_ten) VALUES ('Trung quốc', 'CN0002', 'Li Na');
INSERT INTO khach (quoc_tich, so_cccd, ho_ten) VALUES ('Trung quốc', 'CN0003', 'Wang Fang');
INSERT INTO khach JSON '{"quoc_tich": "Hàn Quốc", "so_cccd": "KR0001", "ho_ten": "Kim Min Jun"}';

-- 1. Tim nhung khach du lich co quoc tich la "Malaysia"
SELECT * FROM khach WHERE quoc_tich = 'Malaysia';

-- 2. Co bao nhieu khach du lich co quoc tich la "Trung quoc"
SELECT COUNT(*) AS so_khach FROM khach WHERE quoc_tich = 'Trung quốc';

CREATE TABLE IF NOT EXISTS tour_by_diem_den (
    diem_den text,
    gia int,
    ma_tour text,
    thoi_gian text,
    lich_trinh text,
    diem_di text,
    PRIMARY KEY (diem_den, gia, ma_tour)
) WITH CLUSTERING ORDER BY (gia ASC, ma_tour ASC);

CREATE TABLE IF NOT EXISTS tour_by_ma_tour (
    ma_tour text,
    thoi_gian text,
    lich_trinh text,
    diem_di text,
    diem_den text,
    gia int,
    PRIMARY KEY (ma_tour)
);

INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Hạ Long', 7000000, 'TOU001', '3 ngày 2 đêm', 'Tham quan vịnh - Chèo kayak', 'Hà Nội');
INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Hạ Long', 12000000, 'TOU002', '4 ngày 3 đêm', 'Du thuyền 5 sao - Hang Sửng Sốt', 'Hà Nội');
INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Hạ Long', 8500000, 'TOU003', '3 ngày 2 đêm', 'Câu mực đêm - Đảo Ti Tốp', 'Hải Phòng');
INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Đà Lạt', 3000000, 'TOU004', '2 ngày 1 đêm', 'Săn mây - Đồi chè Cầu Đất', 'Sài Gòn');
INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Nha Trang', 4500000, 'TOU005', '2 ngày 1 đêm', 'Tắm biển - Vinpearl', 'Sài Gòn');
INSERT INTO tour_by_diem_den (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) VALUES ('Phú Quốc', 9000000, 'TOU006', '3 ngày 2 đêm', 'Hòn Thơm - Safari', 'Cần Thơ');

INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU001', '3 ngày 2 đêm', 'Tham quan vịnh - Chèo kayak', 'Hà Nội', 'Hạ Long', 7000000);
INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU002', '4 ngày 3 đêm', 'Du thuyền 5 sao - Hang Sửng Sốt', 'Hà Nội', 'Hạ Long', 12000000);
INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU003', '3 ngày 2 đêm', 'Câu mực đêm - Đảo Ti Tốp', 'Hải Phòng', 'Hạ Long', 8500000);
INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU004', '2 ngày 1 đêm', 'Săn mây - Đồi chè Cầu Đất', 'Sài Gòn', 'Đà Lạt', 3000000);
INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU005', '2 ngày 1 đêm', 'Tắm biển - Vinpearl', 'Sài Gòn', 'Nha Trang', 4500000);
INSERT INTO tour_by_ma_tour (ma_tour, thoi_gian, lich_trinh, diem_di, diem_den, gia) VALUES ('TOU006', '3 ngày 2 đêm', 'Hòn Thơm - Safari', 'Cần Thơ', 'Phú Quốc', 9000000);

-- 3. Cho biet lich trinh cua nhung tour co gia tu 5 trieu den 10 trieu va diem den la Ha Long
SELECT ma_tour, gia, lich_trinh FROM tour_by_diem_den
WHERE diem_den = 'Hạ Long' AND gia >= 5000000 AND gia <= 10000000;

-- 4. Cho biet thoi gian thuc hien cua Tour co ma "TOU005"
SELECT ma_tour, thoi_gian FROM tour_by_ma_tour WHERE ma_tour = 'TOU005';

CREATE TABLE IF NOT EXISTS khachsan_by_diem_tham_quan (
    diem_tham_quan text,
    ten_ks text,
    dia_diem text,
    gia int,
    suc_chua int,
    dich_vu set<text>,
    PRIMARY KEY (diem_tham_quan, ten_ks)
) WITH CLUSTERING ORDER BY (ten_ks ASC);

CREATE TABLE IF NOT EXISTS khachsan_by_dia_diem (
    dia_diem text,
    ten_ks text,
    diem_tham_quan text,
    gia int,
    suc_chua int,
    dich_vu set<text>,
    PRIMARY KEY (dia_diem, ten_ks)
) WITH CLUSTERING ORDER BY (ten_ks ASC);

INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Thác mơ', 'KS Hoàng Đức', 'Bình Phước', 500000, 100, {'Hồ bơi', 'Ăn sáng'});
INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Thác mơ', 'KS Lương Xuân Trường', 'Bình Phước', 650000, 120, {'Sân vườn', 'BBQ'});
INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Vịnh Hạ Long', 'KS Văn Toàn', 'TP Hạ Long', 1500000, 300, {'Spa', 'Gym', 'Buffet'});
INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Tuần Châu', 'KS Bùi Tiến Dũng', 'TP Hạ Long', 800000, 150, {'View biển'});
INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Bãi Cháy', 'KS Đình Trọng', 'TP Hạ Long', 2500000, 500, {'Hồ bơi vô cực', 'Bar'});
INSERT INTO khachsan_by_diem_tham_quan (diem_tham_quan, ten_ks, dia_diem, gia, suc_chua, dich_vu) VALUES ('Hồ Tuyền Lâm', 'KS Tuấn Anh', 'Đà Lạt', 1200000, 200, {'Sân golf', 'Ăn sáng'});

INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('Bình Phước', 'KS Hoàng Đức', 'Thác mơ', 500000, 100, {'Hồ bơi', 'Ăn sáng'});
INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('Bình Phước', 'KS Lương Xuân Trường', 'Thác mơ', 650000, 120, {'Sân vườn', 'BBQ'});
INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('TP Hạ Long', 'KS Văn Toàn', 'Vịnh Hạ Long', 1500000, 300, {'Spa', 'Gym', 'Buffet'});
INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('TP Hạ Long', 'KS Bùi Tiến Dũng', 'Tuần Châu', 800000, 150, {'View biển'});
INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('TP Hạ Long', 'KS Đình Trọng', 'Bãi Cháy', 2500000, 500, {'Hồ bơi vô cực', 'Bar'});
INSERT INTO khachsan_by_dia_diem (dia_diem, ten_ks, diem_tham_quan, gia, suc_chua, dich_vu) VALUES ('Đà Lạt', 'KS Tuấn Anh', 'Hồ Tuyền Lâm', 1200000, 200, {'Sân golf', 'Ăn sáng'});

-- 5. Cho biet nhung khach san nao co dia diem gan diem tham quan la "Thac mo"
SELECT ten_ks, dia_diem, gia FROM khachsan_by_diem_tham_quan WHERE diem_tham_quan = 'Thác mơ';

-- 6. Cho biet gia cao nhat, thap nhat cua nhung khach san co dia diem tai TP Ha Long
SELECT MAX(gia) AS gia_cao_nhat, MIN(gia) AS gia_thap_nhat FROM khachsan_by_dia_diem WHERE dia_diem = 'TP Hạ Long';

CREATE TABLE IF NOT EXISTS diadiem (
    ten_dia_diem text,
    ngay date,
    vi_tri text,
    thoi_tiet text,
    am_thuc set<text>,
    PRIMARY KEY (ten_dia_diem, ngay)
) WITH CLUSTERING ORDER BY (ngay ASC);

INSERT INTO diadiem (ten_dia_diem, ngay, vi_tri, thoi_tiet, am_thuc) VALUES ('Suối mơ', '2024-10-15', 'Đồng Nai', 'Nắng đẹp', {'Gà nướng', 'Xôi le le'});
INSERT INTO diadiem (ten_dia_diem, ngay, vi_tri, thoi_tiet, am_thuc) VALUES ('Suối mơ', '2024-10-16', 'Đồng Nai', 'Râm mát', {'Cá nướng trui'});
INSERT INTO diadiem (ten_dia_diem, ngay, vi_tri, thoi_tiet, am_thuc) VALUES ('Cầu rồng Đà nẵng', '2024-10-20', 'Đà Nẵng', 'Mưa nhẹ', {'Mì Quảng', 'Bánh tráng cuốn thịt heo'});
INSERT INTO diadiem (ten_dia_diem, ngay, vi_tri, thoi_tiet, am_thuc) VALUES ('Cầu rồng Đà nẵng', '2024-10-21', 'Đà Nẵng', 'Nắng to', {'Hải sản tươi sống'});
INSERT INTO diadiem (ten_dia_diem, ngay, vi_tri, thoi_tiet, am_thuc) VALUES ('Vịnh Hạ Long', '2024-11-01', 'Quảng Ninh', 'Nắng đẹp', {'Chả mực', 'Sá sùng'});

-- 7. Cho biet nhung mon an am thuc nao cua dia diem tham quan "Suoi mo"
SELECT ten_dia_diem, ngay, am_thuc FROM diadiem WHERE ten_dia_diem = 'Suối mơ';

-- 8. Cho biet thong tin thoi tiet ngay 20/10/2024 cua dia diem du lich "Cau rong Da nang"
SELECT ten_dia_diem, ngay, vi_tri, thoi_tiet FROM diadiem
WHERE ten_dia_diem = 'Cầu rồng Đà nẵng' AND ngay = '2024-10-20';

CREATE TABLE IF NOT EXISTS ve (
    ma_ve text,
    ten_tour text,
    thoi_gian_mua date,
    khach_mua text,
    gia_ve int,
    doi_tra boolean,
    PRIMARY KEY (ma_ve, ten_tour, thoi_gian_mua)
) WITH CLUSTERING ORDER BY (ten_tour ASC, thoi_gian_mua ASC);

INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) VALUES ('VE001', 'Sài gòn – Nha trang', '2024-09-15', 'Nguyễn Tuấn Anh', 4500000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) VALUES ('VE002', 'Hà Nội – Hạ Long', '2024-10-01', 'Đoàn Văn Hậu', 7000000, true);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) VALUES ('VE003', 'Sài gòn – Phú Quốc', '2024-08-20', 'Phan Văn Đức', 5500000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) VALUES ('VE004', 'Đà Nẵng – Hội An', '2024-09-25', 'Hồ Tấn Tài', 1200000, false);

-- 9. Cho biet thong tin khach da book ve co ma la "VE001" cho tour Sai gon - Nha trang va thoi gian mua ve la thang 9/2024
SELECT ma_ve, khach_mua, ten_tour, thoi_gian_mua, gia_ve FROM ve
WHERE ma_ve = 'VE001' AND ten_tour = 'Sài gòn – Nha trang'
  AND thoi_gian_mua >= '2024-09-01' AND thoi_gian_mua <= '2024-09-30';

-- 10. Ve co ma "VE003" da duoc mua vao thoi gian nao
SELECT ma_ve, thoi_gian_mua FROM ve WHERE ma_ve = 'VE003';


-- BAI TAP 2.2: QUAN LY TRA CUU THONG TIN CONG DAN

CREATE KEYSPACE qlcongdan
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE qlcongdan;

CREATE TABLE IF NOT EXISTS congdan (
    dia_chi_cu_tru text,
    quoc_tich text,
    so_cccd text,
    ho_ten text,
    PRIMARY KEY (dia_chi_cu_tru, quoc_tich, so_cccd)
) WITH CLUSTERING ORDER BY (quoc_tich ASC, so_cccd ASC);

INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', '079201000001', 'Huỳnh Khương Ninh');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', '079201000002', 'Nguyễn Thị Lan');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', '079201000003', 'Huỳnh Kim Thanh Trà');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', '079201000004', 'Huỳnh Kim Bảo Ngọc');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', '079201000005', 'Huỳnh Kim Ngọc Hà');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('TP. HCM', 'Hàn Quốc', 'KR0000001', 'Kim Min Jun');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('Đà Nẵng', 'Việt Nam', '048201000001', 'Lê Quang Vinh');
INSERT INTO congdan (dia_chi_cu_tru, quoc_tich, so_cccd, ho_ten) VALUES ('Hà Nội', 'Việt Nam', '001201000001', 'Phạm Minh Tuấn');

-- 1. Tim nhung cong dan co dia chi cu tru la "TP. HCM"
SELECT * FROM congdan WHERE dia_chi_cu_tru = 'TP. HCM';

-- 2. Co bao nhieu cong dan co quoc tich la "Viet Nam" dang cu tru tai "TP. HCM"
SELECT COUNT(*) AS so_cong_dan FROM congdan WHERE dia_chi_cu_tru = 'TP. HCM' AND quoc_tich = 'Việt Nam';

CREATE TABLE IF NOT EXISTS diaphuong (
    tinh_thanh text,
    quan_huyen text,
    phuong_xa text,
    so_cong_dan int,
    ds_ho set<text>,
    PRIMARY KEY (tinh_thanh, quan_huyen, phuong_xa)
) WITH CLUSTERING ORDER BY (quan_huyen ASC, phuong_xa ASC);

CREATE TABLE IF NOT EXISTS diaphuong_ho (
    tinh_thanh text,
    quan_huyen text,
    phuong_xa text,
    ma_ho text,
    ten_chu_ho text,
    PRIMARY KEY (tinh_thanh, quan_huyen, phuong_xa, ma_ho)
) WITH CLUSTERING ORDER BY (quan_huyen ASC, phuong_xa ASC, ma_ho ASC);

INSERT INTO diaphuong (tinh_thanh, quan_huyen, phuong_xa, so_cong_dan, ds_ho) VALUES ('Thành phố Hồ Chí Minh', 'Quận 1', 'Phường Bến Nghé', 8, {'HK001', 'HK002'});
INSERT INTO diaphuong (tinh_thanh, quan_huyen, phuong_xa, so_cong_dan, ds_ho) VALUES ('Thành phố Hồ Chí Minh', 'Quận 3', 'Phường 5', 2, {'HK003'});
INSERT INTO diaphuong (tinh_thanh, quan_huyen, phuong_xa, so_cong_dan, ds_ho) VALUES ('Thành phố Đà Nẵng', 'Quận Hải Châu', 'Phường Hải Châu 1', 1, {'HK004'});
INSERT INTO diaphuong (tinh_thanh, quan_huyen, phuong_xa, so_cong_dan, ds_ho) VALUES ('Thành phố Hà Nội', 'Quận Hoàn Kiếm', 'Phường Hàng Bài', 2, {'HK005'});

INSERT INTO diaphuong_ho (tinh_thanh, quan_huyen, phuong_xa, ma_ho, ten_chu_ho) VALUES ('Thành phố Hồ Chí Minh', 'Quận 1', 'Phường Bến Nghé', 'HK001', 'Huỳnh Khương Ninh');
INSERT INTO diaphuong_ho (tinh_thanh, quan_huyen, phuong_xa, ma_ho, ten_chu_ho) VALUES ('Thành phố Hồ Chí Minh', 'Quận 1', 'Phường Bến Nghé', 'HK002', 'Nguyễn Văn Hải');
INSERT INTO diaphuong_ho (tinh_thanh, quan_huyen, phuong_xa, ma_ho, ten_chu_ho) VALUES ('Thành phố Hồ Chí Minh', 'Quận 3', 'Phường 5', 'HK003', 'Trần Thị Mai');
INSERT INTO diaphuong_ho (tinh_thanh, quan_huyen, phuong_xa, ma_ho, ten_chu_ho) VALUES ('Thành phố Đà Nẵng', 'Quận Hải Châu', 'Phường Hải Châu 1', 'HK004', 'Lê Quang Vinh');
INSERT INTO diaphuong_ho (tinh_thanh, quan_huyen, phuong_xa, ma_ho, ten_chu_ho) VALUES ('Thành phố Hà Nội', 'Quận Hoàn Kiếm', 'Phường Hàng Bài', 'HK005', 'Phạm Minh Tuấn');

-- 3. Dia phuong nao co nhieu cong dan nhat
--    Buoc 1: tim so cong dan lon nhat.
SELECT MAX(so_cong_dan) AS so_cong_dan_lon_nhat FROM diaphuong;
--    Buoc 2: tim dia phuong co so cong dan bang gia tri vua tim duoc (8). so_cong_dan khong phai khoa nen dung ALLOW FILTERING.
SELECT tinh_thanh, quan_huyen, phuong_xa, so_cong_dan FROM diaphuong WHERE so_cong_dan = 8 ALLOW FILTERING;

-- 4. Thanh pho Ho Chi Minh co bao nhieu ho cong dan
SELECT COUNT(*) AS so_ho FROM diaphuong_ho WHERE tinh_thanh = 'Thành phố Hồ Chí Minh';

CREATE TABLE IF NOT EXISTS thanhvien_by_chu_ho (
    ten_chu_ho text,
    ma_ho text,
    ho_ten_tv text,
    dia_chi text,
    quan_he_voi_chu_ho text,
    PRIMARY KEY (ten_chu_ho, ma_ho, ho_ten_tv)
) WITH CLUSTERING ORDER BY (ma_ho ASC, ho_ten_tv ASC);

CREATE TABLE IF NOT EXISTS hokhau (
    ma_ho text,
    dia_chi text,
    ten_chu_ho text,
    tuoi_chu_ho int,
    PRIMARY KEY (ma_ho)
);

INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'HK001', 'Huỳnh Khương Ninh', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Chủ hộ');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'HK001', 'Nguyễn Thị Lan', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Vợ');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'HK001', 'Huỳnh Kim Thanh Trà', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Con');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'HK001', 'Huỳnh Kim Bảo Ngọc', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Con');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'HK001', 'Huỳnh Kim Ngọc Hà', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Con');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Nguyễn Văn Hải', 'HK002', 'Nguyễn Văn Hải', '25 Nguyễn Huệ, P. Bến Nghé, Q.1, TP. HCM', 'Chủ hộ');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Nguyễn Văn Hải', 'HK002', 'Lê Thị Hoa', '25 Nguyễn Huệ, P. Bến Nghé, Q.1, TP. HCM', 'Vợ');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Nguyễn Văn Hải', 'HK002', 'Nguyễn Minh Khôi', '25 Nguyễn Huệ, P. Bến Nghé, Q.1, TP. HCM', 'Con');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Trần Thị Mai', 'HK003', 'Trần Thị Mai', '8 Cách Mạng Tháng 8, P.5, Q.3, TP. HCM', 'Chủ hộ');
INSERT INTO thanhvien_by_chu_ho (ten_chu_ho, ma_ho, ho_ten_tv, dia_chi, quan_he_voi_chu_ho) VALUES ('Trần Thị Mai', 'HK003', 'Võ Văn Sơn', '8 Cách Mạng Tháng 8, P.5, Q.3, TP. HCM', 'Con');

INSERT INTO hokhau (ma_ho, dia_chi, ten_chu_ho, tuoi_chu_ho) VALUES ('HK001', '12 Lê Lợi, P. Bến Nghé, Q.1, TP. HCM', 'Huỳnh Khương Ninh', 62);
INSERT INTO hokhau (ma_ho, dia_chi, ten_chu_ho, tuoi_chu_ho) VALUES ('HK002', '25 Nguyễn Huệ, P. Bến Nghé, Q.1, TP. HCM', 'Nguyễn Văn Hải', 45);
INSERT INTO hokhau (ma_ho, dia_chi, ten_chu_ho, tuoi_chu_ho) VALUES ('HK003', '8 Cách Mạng Tháng 8, P.5, Q.3, TP. HCM', 'Trần Thị Mai', 78);
INSERT INTO hokhau (ma_ho, dia_chi, ten_chu_ho, tuoi_chu_ho) VALUES ('HK004', '15 Trần Phú, P. Hải Châu 1, Q. Hải Châu, Đà Nẵng', 'Lê Quang Vinh', 31);
INSERT INTO hokhau (ma_ho, dia_chi, ten_chu_ho, tuoi_chu_ho) VALUES ('HK005', '3 Hàng Bài, P. Hàng Bài, Q. Hoàn Kiếm, Hà Nội', 'Phạm Minh Tuấn', 53);

-- 5. Ho khau co ten chu ho la "Huynh Khuong Ninh" co bao nhieu thanh vien
SELECT COUNT(*) AS so_thanh_vien FROM thanhvien_by_chu_ho WHERE ten_chu_ho = 'Huỳnh Khương Ninh';

-- 6. Ho khau nao co chu ho tuoi lon nhat, nho nhat duoc quan ly
--    Buoc 1: tim tuoi lon nhat, nho nhat cua chu ho.
SELECT MAX(tuoi_chu_ho) AS tuoi_lon_nhat, MIN(tuoi_chu_ho) AS tuoi_nho_nhat FROM hokhau;
--    Buoc 2: tim ho khau co chu ho tuoi lon nhat (78) va nho nhat (31). tuoi_chu_ho khong phai khoa nen dung ALLOW FILTERING.
SELECT ma_ho, ten_chu_ho, tuoi_chu_ho, dia_chi FROM hokhau WHERE tuoi_chu_ho = 78 ALLOW FILTERING;
SELECT ma_ho, ten_chu_ho, tuoi_chu_ho, dia_chi FROM hokhau WHERE tuoi_chu_ho = 31 ALLOW FILTERING;

CREATE TABLE IF NOT EXISTS quanhecongdan (
    ho_ten_cong_dan text,
    quan_he text,
    ho_ten_nguoi_than text,
    nam_sinh int,
    PRIMARY KEY (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than)
) WITH CLUSTERING ORDER BY (quan_he ASC, ho_ten_nguoi_than ASC);

INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Cha', 'Huỳnh Khương Ninh', 2001);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Mẹ', 'Nguyễn Thị Lan', 2001);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Em', 'Huỳnh Kim Bảo Ngọc', 2001);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Em', 'Huỳnh Kim Ngọc Hà', 2001);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Cha', 'Huỳnh Khương Ninh', 2004);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Mẹ', 'Nguyễn Thị Lan', 2004);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Chị', 'Huỳnh Kim Thanh Trà', 2004);
INSERT INTO quanhecongdan (ho_ten_cong_dan, quan_he, ho_ten_nguoi_than, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Em', 'Huỳnh Kim Ngọc Hà', 2004);

-- 7. Tim tat ca cac moi quan he cua cong dan co ten "Huynh Kim Thanh Tra"
SELECT ho_ten_cong_dan, quan_he, ho_ten_nguoi_than FROM quanhecongdan WHERE ho_ten_cong_dan = 'Huỳnh Kim Thanh Trà';

-- 8. Cong dan "Huynh Kim Bao Ngoc" co bao nhieu anh chi em ruot
SELECT COUNT(*) AS so_anh_chi_em_ruot FROM quanhecongdan
WHERE ho_ten_cong_dan = 'Huỳnh Kim Bảo Ngọc' AND quan_he IN ('Anh', 'Chị', 'Em');

CREATE TABLE IF NOT EXISTS taisan_by_cong_dan (
    ho_ten_cong_dan text,
    ma_tai_san text,
    ten_tai_san text,
    tri_gia bigint,
    mo_ta text,
    PRIMARY KEY (ho_ten_cong_dan, ma_tai_san)
) WITH CLUSTERING ORDER BY (ma_tai_san ASC);

CREATE TABLE IF NOT EXISTS taisan_by_ten_bien_so (
    ten_tai_san text,
    bien_so text,
    ho_ten_cong_dan text,
    tri_gia bigint,
    PRIMARY KEY (ten_tai_san, bien_so)
) WITH CLUSTERING ORDER BY (bien_so ASC);

INSERT INTO taisan_by_cong_dan (ho_ten_cong_dan, ma_tai_san, ten_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Kim Ngọc Hà', 'TS001', 'Xe ô tô CX-5', 850000000, 'Mazda CX-5, biển số 51B-00797');
INSERT INTO taisan_by_cong_dan (ho_ten_cong_dan, ma_tai_san, ten_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Kim Ngọc Hà', 'TS002', 'Xe máy Vision', 35000000, 'Honda Vision, biển số 59A1-12345');
INSERT INTO taisan_by_cong_dan (ho_ten_cong_dan, ma_tai_san, ten_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Kim Ngọc Hà', 'TS003', 'Căn hộ chung cư', 2500000000, 'Căn hộ 70m2, Quận 7');
INSERT INTO taisan_by_cong_dan (ho_ten_cong_dan, ma_tai_san, ten_tai_san, tri_gia, mo_ta) VALUES ('Trần Thị Mai', 'TS004', 'Xe ô tô CX-5', 800000000, 'Mazda CX-5, biển số 51A-11111');

INSERT INTO taisan_by_ten_bien_so (ten_tai_san, bien_so, ho_ten_cong_dan, tri_gia) VALUES ('Xe ô tô CX-5', '51B-00797', 'Huỳnh Kim Ngọc Hà', 850000000);
INSERT INTO taisan_by_ten_bien_so (ten_tai_san, bien_so, ho_ten_cong_dan, tri_gia) VALUES ('Xe ô tô CX-5', '51A-11111', 'Trần Thị Mai', 800000000);
INSERT INTO taisan_by_ten_bien_so (ten_tai_san, bien_so, ho_ten_cong_dan, tri_gia) VALUES ('Xe máy Vision', '59A1-12345', 'Huỳnh Kim Ngọc Hà', 35000000);

-- 9. Trich xuat thong tin tat ca tai san cua cong dan "Huynh Kim Ngoc Ha" va tong tri gia tai san la bao nhieu
SELECT * FROM taisan_by_cong_dan WHERE ho_ten_cong_dan = 'Huỳnh Kim Ngọc Hà';
SELECT SUM(tri_gia) AS tong_tri_gia FROM taisan_by_cong_dan WHERE ho_ten_cong_dan = 'Huỳnh Kim Ngọc Hà';

-- 10. Tai san "Xe o to CX-5" bien so 51B-00797 cua cong dan nao
SELECT ten_tai_san, bien_so, ho_ten_cong_dan FROM taisan_by_ten_bien_so
WHERE ten_tai_san = 'Xe ô tô CX-5' AND bien_so = '51B-00797';
