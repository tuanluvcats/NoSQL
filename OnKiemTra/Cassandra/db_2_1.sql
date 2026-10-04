-- Bài tập 2.1. Thiết kế cơ sở dữ liệu quản lý Cty du lịch, thực hiện tạo các bảng đáp ứng yêu cầu truy vấn người dùng theo các yêu cầu sau:

-- 1. BẢNG KHACH: Mô tả thông tin khách du lịch Họ tên, quốc tịch, số CCCD, …
CREATE TABLE IF NOT EXISTS khach (
    quoc_tich text,
    cccd text,
    ho_ten text,
    PRIMARY KEY (quoc_tich, cccd)
);

INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Malaysia', 'MAL001', 'Đặng Văn Lâm');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Trung quốc', 'CHN001', 'Nguyễn Tiến Linh');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Trung quốc', 'CHN002', 'Quế Ngọc Hải');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Việt Nam', 'VN001', 'Nguyễn Quang Hải');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Việt Nam', 'VN002', 'Nguyễn Công Phượng');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Việt Nam', 'VN003', 'Đỗ Duy Mạnh');
INSERT INTO khach (quoc_tich, cccd, ho_ten) VALUES ('Hàn Quốc', 'KOR001', 'Bùi Hoàng Việt Anh');

SELECT * FROM khach;

-- 2. BẢNG TOUR: Mô tả thông tin về Tour du lịch như thời gian, lịch trình chi tiết, Điểm đi, Điểm đến, giá Tour, …
CREATE TABLE IF NOT EXISTS tour (
    diem_den text,
    gia int,
    ma_tour text,
    thoi_gian text,
    lich_trinh text,
    diem_di text,
    PRIMARY KEY (diem_den, gia, ma_tour)
);

INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Hạ Long', 7000000, 'TOU001', '3 ngày 2 đêm', 'Tham quan vịnh - Chèo ván', 'Hà Nội');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Hạ Long', 12000000, 'TOU002', '4 ngày 3 đêm', 'Du thuyền 5 sao', 'Hà Nội');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Nha Trang', 4500000, 'TOU005', '2 ngày 1 đêm', 'Tắm biển - Vinpearl', 'Sài Gòn');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Hạ Long', 8500000, 'TOU003', '3 ngày 2 đêm', 'Câu mực đêm - Vịnh Hạ Long', 'Hải Phòng');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Đà Lạt', 3000000, 'TOU004', '2 ngày 1 đêm', 'Săn mây - Đồi chè', 'Sài Gòn');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Phú Quốc', 9000000, 'TOU006', '3 ngày 2 đêm', 'Hòn Thơm - Safari', 'Cần Thơ');
INSERT INTO tour (diem_den, gia, ma_tour, thoi_gian, lich_trinh, diem_di) 
VALUES ('Đà Nẵng', 6000000, 'TOU007', '3 ngày 2 đêm', 'Bà Nà Hills - Cầu Rồng', 'Hà Nội');

SELECT * FROM tour

-- 3. BẢNG KHACHSAN: Mô tả thông tin cho mỗi khách sạn như địa điểm, giá, sức chứa, dịch vụ, điểm tham quan…
CREATE TABLE IF NOT EXISTS khach_san (
    dia_diem text,
    diem_tham_quan text,
    ten_ks text,
    gia int,
    suc_chua int,
    dich_vu text,
    PRIMARY KEY (dia_diem, diem_tham_quan, ten_ks)
);

INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('Bình Phước', 'Thác mơ', 'KS Hoàng Đức', 500000, 100, 'Hồ bơi, Ăn sáng');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('TP Hạ Long', 'Vịnh Hạ Long', 'KS Văn Toàn', 1500000, 300, 'Spa, Gym, Buffet');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('TP Hạ Long', 'Tuần Châu', 'KS Bùi Tiến Dũng', 800000, 150, 'View biển cực đẹp');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('TP Hạ Long', 'Bãi Cháy', 'KS Đình Trọng', 2500000, 500, 'Hồ bơi vô cực, Bar');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('Đà Lạt', 'Hồ Tuyền Lâm', 'KS Tuấn Anh', 1200000, 200, 'Sân golf, Ăn sáng');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('Nha Trang', 'Hòn Tằm', 'KS Hồng Duy', 3000000, 400, 'Cáp treo, Buffet');
INSERT INTO khach_san (dia_diem, diem_tham_quan, ten_ks, gia, suc_chua, dich_vu) 
VALUES ('Bình Phước', 'Thác mơ', 'KS Lương Xuân Trường', 650000, 120, 'Sân vườn, BBQ');

SELECT * FROM khach_san
-- 4. BẢNG DIADIEM: Mô tả thông tin cho từng dịa điểm du lịch mà khách sẽ đến như vị trí, thời tiết, ngày, ẩm thực,… 
CREATE TABLE IF NOT EXISTS dia_diem (
    diem_tham_quan text,
    ngay date,
    vi_tri text,
    thoi_tiet text,
    am_thuc text,
    PRIMARY KEY (diem_tham_quan, ngay)
);

INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Suối mơ', '2024-10-15', 'Đồng Nai', 'Nắng đẹp', 'Gà nướng, Xôi le le');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Cầu rồng Đà nẵng', '2024-10-20', 'Đà Nẵng', 'Mưa nhẹ', 'Mì Quảng, Bánh tráng cuốn thịt heo');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Cầu rồng Đà nẵng', '2024-10-21', 'Đà Nẵng', 'Nắng to', 'Hải sản tươi sống');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Suối mơ', '2024-10-16', 'Đồng Nai', 'Râm mát', 'Cá nướng trui');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Vịnh Hạ Long', '2024-11-01', 'Quảng Ninh', 'Nắng đẹp', 'Chả mực, Sá sùng');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Bà Nà Hills', '2024-12-24', 'Đà Nẵng', 'Sương mù', 'Buffet Bà Nà');
INSERT INTO dia_diem (diem_tham_quan, ngay, vi_tri, thoi_tiet, am_thuc) 
VALUES ('Phố cổ Hội An', '2024-10-20', 'Quảng Nam', 'Trăng sáng', 'Cao lầu, Chè bắp');

SELECT * FROM dia_diem

-- 5. BẢNG VE: Mô tả thông tin cho từng vé tour mà khách đã book, bao gồm  giá vé, khách mua, thời gian mua, đổi trả,…
CREATE TABLE IF NOT EXISTS ve (
    ma_ve text,
    ten_tour text,
    thoi_gian_mua date,
    khach_mua text,
    gia_ve int,
    doi_tra boolean,
    PRIMARY KEY (ma_ve)
);

INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE001', 'Sài gòn – Nha trang', '2024-09-15', 'Nguyễn Tuấn Anh', 4500000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE002', 'Hà Nội – Hạ Long', '2024-10-01', 'Đoàn Văn Hậu', 7000000, true);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE003', 'Sài gòn – Phú Quốc', '2024-08-20', 'Phan Văn Đức', 5500000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE004', 'Đà Nẵng – Hội An', '2024-09-25', 'Hồ Tấn Tài', 1200000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE005', 'Hà Nội – Sapa', '2024-11-05', 'Vũ Văn Thanh', 3500000, true);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE006', 'Sài gòn – Đà Lạt', '2024-10-10', 'Đỗ Hùng Dũng', 2500000, false);
INSERT INTO ve (ma_ve, ten_tour, thoi_gian_mua, khach_mua, gia_ve, doi_tra) 
VALUES ('VE007', 'Cần Thơ – Phú Quốc', '2024-09-30', 'Phạm Tuấn Hải', 4000000, true);

SELECT * FROM ve

--  TRUY VẤN

-- 1. Tìm những khách du lịch có quốc tịch là “Malaysia”. 
SELECT * FROM khach WHERE quoc_tich = 'Malaysia';

-- 2. Có bao nhiêu khách du lịch có quốc tịch là “Trung quốc”. 
SELECT COUNT(*) FROM khach WHERE quoc_tich = 'Trung quốc';

-- 3. Cho biết lịch trình của những tour có giá từ 5 triệu đến 10 triệu và điểm đến là Hạ Long. 
SELECT lich_trinh, gia FROM tour 
WHERE diem_den = 'Hạ Long' AND gia >= 5000000 AND gia <= 10000000;

-- 4. Cho biết thời gian thực hiện của Tour có mã “TOU005”. 
SELECT thoi_gian FROM tour WHERE ma_tour = 'TOU005' ALLOW FILTERING;

-- 5. Cho biết những khách sạn nào có địa điểm gần điểm tham quan là “Thác mơ”. 
SELECT ten_ks, dia_diem FROM khach_san WHERE diem_tham_quan = 'Thác mơ' ALLOW FILTERING;

-- 6. Cho biết giá cao nhất, thấp nhất của những khách sạn có địa điểm tại TP Hạ Long. 
SELECT MIN(gia) AS gia_thap_nhat, MAX(gia) AS gia_cao_nhat 
FROM khach_san 
WHERE dia_diem = 'TP Hạ Long';

-- 7. Cho biết những món ăn ẩm thực nào của địa điểm tham quan “Suối mơ”. 
SELECT am_thuc FROM dia_diem WHERE diem_tham_quan = 'Suối mơ';

-- 8. Cho biết thông tin thời tiết ngày 20/10/2024 của địa điểm du lịch “Cầu rồng Đà nẵng”. 
SELECT thoi_tiet FROM dia_diem 
WHERE diem_tham_quan = 'Cầu rồng Đà nẵng' AND ngay = '2024-10-20';

-- 9. Cho biết thông tin khách đã book vé có mã là “VE001” cho tour Sài gòn – Nha trang và thời gian mua vé là tháng 9/2024. 
SELECT khach_mua, ten_tour, thoi_gian_mua 
FROM ve 
WHERE ma_ve = 'VE001';

-- 10. Vé có mã “VE003” đã được mua vào thời gian nào.
SELECT thoi_gian_mua FROM ve WHERE ma_ve = 'VE003';