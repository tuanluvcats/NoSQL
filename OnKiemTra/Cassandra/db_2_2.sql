-- Bài tập 2.2. Thiết kế cơ sở dữ liệu quản lý tra cứu thông tin công dân, thực hiện tạo các bảng đáp ứng yêu cầu truy vấn người dùng theo các yêu cầu sau: 

-- KHỞI TẠO KEYSPACE
CREATE KEYSPACE IF NOT EXISTS ql_congdan 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_congdan;

-- 1. BẢNG CONGDAN: Mô tả thông tin của công dân như Họ tên, quốc tịch, số CCCD, địa chỉ cư trú, …
CREATE TABLE IF NOT EXISTS congdan (
    dia_chi text,
    quoc_tich text,
    cccd text,
    ho_ten text,
    PRIMARY KEY (dia_chi, quoc_tich, cccd)
);

INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', 'VN001', 'Huỳnh Kim Bảo Ngọc');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('TP. HCM', 'Việt Nam', 'VN002', 'Huỳnh Kim Thanh Trà');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('TP. HCM', 'Mỹ', 'US001', 'John Smith');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('Hà Nội', 'Việt Nam', 'VN003', 'Phạm Thu Thủy');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('Đà Nẵng', 'Việt Nam', 'VN004', 'Nguyễn Bảo Long');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('Cần Thơ', 'Việt Nam', 'VN005', 'Vũ Minh Tuấn');
INSERT INTO congdan (dia_chi, quoc_tich, cccd, ho_ten) VALUES ('TP. HCM', 'Hàn Quốc', 'KR001', 'Park Hang Seo');

SELECT * FROM congdan

-- 2. BẢNG DIAPHUONG: Mô tả thông tin của địa phương như xã/phường, quận/huyện, tỉnh/thành, gồm những hộ công dân nào,…
CREATE TABLE IF NOT EXISTS diaphuong (
    tinh_thanh text,
    quan_huyen text,
    xa_phuong text,
    ho_cong_dan text,
    PRIMARY KEY (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan)
);

INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('TP. HCM', 'Quận 1', 'Bến Nghé', 'Hộ Huỳnh Khương Ninh');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('TP. HCM', 'Quận 3', 'Phường 6', 'Hộ Huỳnh Kim Thanh Trà');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('TP. HCM', 'Tân Bình', 'Phường 2', 'Hộ Lê Hải Đường');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('Hà Nội', 'Hoàn Kiếm', 'Hàng Bài', 'Hộ Phạm Thu Thủy');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('Đà Nẵng', 'Hải Châu', 'Thạch Thang', 'Hộ Nguyễn Bảo Long');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('Cần Thơ', 'Ninh Kiều', 'An Phú', 'Hộ Vũ Minh Tuấn');
INSERT INTO diaphuong (tinh_thanh, quan_huyen, xa_phuong, ho_cong_dan) VALUES ('TP. HCM', 'Quận 1', 'Bến Thành', 'Hộ Huỳnh Kim Ngọc Hà');

SELECT * FROM diaphuong

-- 3. BẢNG HOKHAU: Mô tả thông tin của sổ hộ khẩu công dân như địa chỉ, tên chủ hộ, thành viên trong họ khẩu, mối quan hệ với chủ hộ, …
CREATE TABLE IF NOT EXISTS hokhau (
    ten_chu_ho text,
    thanh_vien text,
    dia_chi text,
    moi_quan_he text,
    tuoi_chu_ho int,
    PRIMARY KEY (ten_chu_ho, thanh_vien)
);

INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'Huỳnh Khương Ninh', '123 Lê Lợi TP.HCM', 'Chủ hộ', 65);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'Nguyễn Thị Mai', '123 Lê Lợi TP.HCM', 'Vợ', 65);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Huỳnh Khương Ninh', 'Huỳnh Kim Thanh Trà', '123 Lê Lợi TP.HCM', 'Con gái', 65);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Trần Trường Sinh', 'Trần Trường Sinh', '456 Hai Bà Trưng TP.HCM', 'Chủ hộ', 80);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Lê Hải Đường', 'Lê Hải Đường', '789 Trường Chinh TP.HCM', 'Chủ hộ', 22);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Huỳnh Kim Bảo Ngọc', 'Huỳnh Kim Bảo Ngọc', '101 Võ Văn Tần TP.HCM', 'Chủ hộ', 30);
INSERT INTO hokhau (ten_chu_ho, thanh_vien, dia_chi, moi_quan_he, tuoi_chu_ho) VALUES ('Phạm Thu Thủy', 'Phạm Thu Thủy', '12 Hàng Bài, Hà Nội', 'Chủ hộ', 45);

SELECT * FROM hokhau

-- 4. BẢNG QUANHECONGDAN: Mô tả thông tin mối quan hệ của một công dân như Họ tên công dân, năm sinh, họ tên người có mối quan hệ như Cha/mẹ/anh/chị/em/con, …
CREATE TABLE IF NOT EXISTS quanhecongdan (
    ho_ten text,
    moi_quan_he text,
    nguoi_quan_he text,
    nam_sinh int,
    PRIMARY KEY (ho_ten, moi_quan_he, nguoi_quan_he)
);

INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Cha', 'Huỳnh Khương Ninh', 1959);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Huỳnh Kim Thanh Trà', 'Mẹ', 'Nguyễn Thị Mai', 1964);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Anh/chị/em ruột', 'Huỳnh Kim Long', 1994);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Huỳnh Kim Bảo Ngọc', 'Anh/chị/em ruột', 'Huỳnh Kim Phượng', 1998);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Trần Trường Sinh', 'Con', 'Trần Lập', 1980);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Lê Hải Đường', 'Mẹ', 'Phạm Thu Thủy', 1975);
INSERT INTO quanhecongdan (ho_ten, moi_quan_he, nguoi_quan_he, nam_sinh) VALUES ('Nguyễn Bảo Long', 'Vợ', 'Đinh Thu Trà', 1990);

SELECT * FROM quanhecongdan

-- 5. BẢNG TAISAN: Mô tả thông tin tài sản của một công dân như Họ tên công dân,mã tài sản, trị giá tài sản, mô tả tài sản, …
CREATE TABLE IF NOT EXISTS taisan (
    ho_ten text,
    ma_tai_san text,
    tri_gia bigint,
    mo_ta text,
    PRIMARY KEY (ho_ten, ma_tai_san)
);

INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Kim Ngọc Hà', 'TS001', 5000000000, 'Nhà phố Quận 1');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Kim Ngọc Hà', 'TS002', 1000000000, 'Xe ô tô Mazda 3');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Huỳnh Khương Ninh', 'TS003', 1500000000, 'Xe ô tô CX-5 biển số 51B-00797');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Trần Trường Sinh', 'TS004', 20000000000, 'Biệt thự Thảo Điền');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Lê Hải Đường', 'TS005', 50000000, 'Xe máy SH 150i');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Nguyễn Bảo Long', 'TS006', 3000000000, 'Căn hộ chung cư cao cấp');
INSERT INTO taisan (ho_ten, ma_tai_san, tri_gia, mo_ta) VALUES ('Vũ Minh Tuấn', 'TS007', 800000000, 'Đất nền Cần Thơ');

SELECT * FROM taisan

--  TRUY VẤN

-- 1. Tìm những công dân có địa chỉ cư trú là “TP. HCM”.
SELECT * FROM congdan WHERE dia_chi = 'TP. HCM';

-- 2. Có bao nhiêu công dân có quốc tịch là “Việt Nam” đang cư trú tại “TP. HCM”.
SELECT COUNT(*) FROM congdan WHERE dia_chi = 'TP. HCM' AND quoc_tich = 'Việt Nam';

-- 3. Địa phương nào có nhiều công dân nhất.
SELECT COUNT(ho_cong_dan) AS so_luong_ho_tphcm FROM diaphuong WHERE tinh_thanh = 'TP. HCM';

-- 4. Thành phố Hồ Chí Minh có bao nhiêu hộ công dân.
SELECT COUNT(ho_cong_dan) AS tong_ho FROM diaphuong WHERE tinh_thanh = 'TP. HCM';

-- 5. Hộ khẩu có tên chủ hộ là “Huỳnh Khương Ninh” có bao nhiêu thành viên?
SELECT COUNT(thanh_vien) AS so_thanh_vien FROM hokhau WHERE ten_chu_ho = 'Huỳnh Khương Ninh';

-- 6. Hộ khẩu nào có chủ hộ tuổi lớn nhất, nhỏ nhất được quản lý.
SELECT MIN(tuoi_chu_ho) AS tuoi_nho_nhat, MAX(tuoi_chu_ho) AS tuoi_lon_nhat FROM hokhau;

-- 7. Tìm tất cả các mối quan hệ của công dân có tên “Huỳnh Kim Thanh Trà”.
SELECT moi_quan_he, nguoi_quan_he FROM quanhecongdan WHERE ho_ten = 'Huỳnh Kim Thanh Trà';

-- 8. Công dân “Huỳnh Kim Bảo Ngọc” có bao nhiêu anh chị em ruột.
SELECT COUNT(*) FROM quanhecongdan WHERE ho_ten = 'Huỳnh Kim Bảo Ngọc' AND moi_quan_he = 'Anh/chị/em ruột';

-- 9. Trích xuất thông tin tất cả tài sản của công dân “Huỳnh Kim Ngọc Hà” và tổng trị giá tài sản.
--  Lấy chi tiết tài sản
SELECT * FROM taisan WHERE ho_ten = 'Huỳnh Kim Ngọc Hà';
--  Lấy tổng trị giá
SELECT SUM(tri_gia) AS tong_tri_gia FROM taisan WHERE ho_ten = 'Huỳnh Kim Ngọc Hà';

-- 10. Tài sản “Xe ô tô CX-5” biển số 51B-00797 của công dân nào.
SELECT ho_ten FROM taisan WHERE mo_ta = 'Xe ô tô CX-5 biển số 51B-00797' ALLOW FILTERING;