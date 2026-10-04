-- Bài tập 2.3. Thiết kế cơ sở dữ liệu quản lý nhập kho hàng, thực hiện tạo các bảng đáp ứng yêu cầu truy vấn người dùng theo các yêu cầu sau: 

CREATE KEYSPACE IF NOT EXISTS ql_khohang 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_khohang;


-- 1. BẢNG KHOHANG: Mô tả thông tin của kho hàng như sức chứa, dịa chỉ, loại hàng trong kho, số lượng tồn trong kho, ngày nhập hàng, …
CREATE TABLE IF NOT EXISTS khohang (
    dia_chi text,
    ten_kho text,
    ngay_nhap date,
    loai_hang text,
    suc_chua int,
    so_luong_ton int,
    PRIMARY KEY (dia_chi, ten_kho, ngay_nhap)
);

INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('Vũng Tàu', 'Kho Hải Sản VT', '2024-01-15', 'Đông lạnh', 500, 200);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('Vũng Tàu', 'Kho Dầu Nhớt', '2024-02-10', 'Hóa chất', 1000, 800);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('TP. HCM', 'Thép Việt tiệp', '2024-03-05', 'Vật liệu xây dựng', 5000, 4500);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('TP. HCM', 'Cá hồi Nauy', '2024-02-20', 'Đông lạnh', 200, 150);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('TP. HCM', 'Cá hồi Nauy', '2024-03-10', 'Đông lạnh', 200, 180);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('Hà Nội', 'Kho Gia Dụng', '2024-04-12', 'Tiêu dùng', 300, 100);
INSERT INTO khohang (dia_chi, ten_kho, ngay_nhap, loai_hang, suc_chua, so_luong_ton) VALUES ('Đà Nẵng', 'Kho Điện Máy', '2024-05-01', 'Điện tử', 800, 600);

SELECT * FROM khohang
-- 2. BẢNG MATHANG: Mô tả thông tin của mặt hàng như mã hàng, tên hàng, quy cách, ngày sản xuất, lô hàng, thuộc loại hàng nào (khô hay nước), … 

CREATE TABLE IF NOT EXISTS mathang (
    quy_cach text,
    loai_hang text,
    ten_hang text,
    lo_hang text,
    ma_hang text,
    ngay_sx date,
    PRIMARY KEY (quy_cach, loai_hang, ten_hang, lo_hang)
);

INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('hộp', 'nước', 'Sữa Vinamilk không đường', 'SV01KD', 'MH01', '2024-08-01');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('hộp', 'nước', 'Nước ép cam Vfresh', 'VF02CAM', 'MH02', '2024-08-05');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('thùng', 'nước', 'Bia Heineken', 'HN03T', 'MH03', '2024-07-20');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('gói', 'khô', 'Mì Hảo Hảo', 'HH04G', 'MH04', '2024-09-10');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('hộp', 'nước', 'Sữa chua uống Probi', 'PB05H', 'MH05', '2024-09-15');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('bao', 'khô', 'Gạo ST25', 'ST25B1', 'MH06', '2024-06-15');
INSERT INTO mathang (quy_cach, loai_hang, ten_hang, lo_hang, ma_hang, ngay_sx) VALUES ('hộp', 'khô', 'Bánh Danisa', 'DN07K', 'MH07', '2024-05-20');

SELECT * FROM mathang
-- 3. BẢNG PHIEUNHAP: Mô tả thông tin của phiếu nhập hàng như mã hàng, tên hàng, số lượng nhập, giá nhập, ngày hết hạn, nơi sản xuất, nhân viên nhập, ngày nhập,… 
CREATE TABLE IF NOT EXISTS phieunhap (
    ma_phieu text,
    ngay_nhap date,
    ma_hang text,
    ten_hang text,
    so_luong int,
    gia_nhap int,
    ngay_het_han date,
    noi_sx text,
    nhan_vien text,
    PRIMARY KEY (ma_phieu, ngay_nhap)
);

INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN010', '2024-09-15', 'MH01', 'Sữa Vinamilk', 1000, 250000, '2025-02-01', 'Việt Nam', 'Nguyễn Văn A');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN011', '2024-09-16', 'MH02', 'Nước cam', 500, 300000, '2025-03-01', 'Việt Nam', 'Trần Thị B');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN012', '2024-09-17', 'MH03', 'Bia Heineken', 200, 400000, '2025-07-01', 'Việt Nam', 'Lê Văn C');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN008', '2024-08-10', 'MH04', 'Mì Hảo Hảo', 2000, 100000, '2025-01-01', 'Việt Nam', 'Nguyễn Văn A');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN009', '2024-08-20', 'MH05', 'Sữa chua', 800, 150000, '2024-11-01', 'Việt Nam', 'Trần Thị B');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN013', '2024-10-01', 'MH06', 'Gạo ST25', 1500, 1200000, '2026-01-01', 'Việt Nam', 'Lê Văn C');
INSERT INTO phieunhap (ma_phieu, ngay_nhap, ma_hang, ten_hang, so_luong, gia_nhap, ngay_het_han, noi_sx, nhan_vien) VALUES ('PN014', '2024-10-05', 'MH07', 'Bánh Danisa', 300, 500000, '2025-05-01', 'Indonesia', 'Nguyễn Văn A');

SELECT * FROM phieunhap

-- 4. BẢNG PHIEUXUAT: Mô tả thông tin của phiếu xuất kho mặt hàng, số lượng xuất, ngày xuất, xuất cho khác hàng nào, trị giá,…
CREATE TABLE IF NOT EXISTS phieuxuat (
    khach_hang text,
    ngay_xuat date,
    ma_phieu text,
    mat_hang text,
    so_luong int,
    tri_gia bigint,
    PRIMARY KEY (khach_hang, ngay_xuat, ma_phieu)
);

INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Huỳnh Kim Anh', '2024-08-15', 'PX001', 'Bia Heineken', 10, 4500000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Trần Phú', '2024-08-20', 'PX002', 'Gạo ST25', 5, 6500000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Lê Anh Kiều', '2024-07-10', 'PX003', 'Sữa Vinamilk', 20, 5500000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Lê Anh Kiều', '2024-07-25', 'PX004', 'Nước cam', 15, 4800000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Phạm Văn Đồng', '2024-09-05', 'PX005', 'Mì Hảo Hảo', 50, 5500000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Đinh Tiên Hoàng', '2024-09-12', 'PX006', 'Bánh Danisa', 8, 4200000);
INSERT INTO phieuxuat (khach_hang, ngay_xuat, ma_phieu, mat_hang, so_luong, tri_gia) VALUES ('Huỳnh Kim Anh', '2024-09-20', 'PX007', 'Sữa chua', 12, 2000000);

SELECT * FROM phieuxuat

-- 5. BẢNG KHACHHANG: Mô tả thông tin của khách hàng như họ tên, địa chỉ, điện thoại, loại khách VIP hay khách thường, hoá đơn, lịch sử mua hàng, …
CREATE TABLE IF NOT EXISTS khachhang (
    ho_ten text,
    ngay_mua date,
    dia_chi text,
    dien_thoai text,
    loai_khach text,
    hoa_don text,
    mat_hang_mua text,
    PRIMARY KEY (ho_ten, ngay_mua, hoa_don)
);

INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Lê Anh Kiều', '2024-04-15', 'Q1, TP.HCM', '0901234567', 'VIP', 'HD001', 'Sữa Vinamilk');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Lê Anh Kiều', '2024-05-20', 'Q1, TP.HCM', '0901234567', 'VIP', 'HD002', 'Bia Heineken');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Huỳnh Kim Anh', '2024-06-10', 'Q3, TP.HCM', '0987654321', 'Thường', 'HD003', 'Gạo ST25');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Trần Phú', '2024-08-01', 'Q5, TP.HCM', '0912345678', 'Thường', 'HD004', 'Mì Hảo Hảo');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Lê Anh Kiều', '2024-08-15', 'Q1, TP.HCM', '0901234567', 'VIP', 'HD005', 'Nước cam');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Đinh Tiên Hoàng', '2024-09-05', 'Tân Bình, TP.HCM', '0933445566', 'VIP', 'HD006', 'Bánh Danisa');
INSERT INTO khachhang (ho_ten, ngay_mua, dia_chi, dien_thoai, loai_khach, hoa_don, mat_hang_mua) VALUES ('Phạm Văn Đồng', '2024-09-10', 'Bình Thạnh, TP.HCM', '0977889900', 'Thường', 'HD007', 'Sữa chua');

SELECT * FROM khachhang

--  TRUY VẤN

-- 1. Cho biết có bao nhiêu kho hàng địa chỉ ở Vùng Tàu và sức chứa của từng kho.
SELECT ten_kho, suc_chua FROM khohang WHERE dia_chi = 'Vũng Tàu';
SELECT COUNT(*) AS so_luong_kho FROM khohang WHERE dia_chi = 'Vũng Tàu';

-- 2. Kho hàng “Thép Việt tiệp” tại TP. HCM có sức chứa bao nhiêu tấn.
SELECT suc_chua FROM khohang WHERE dia_chi = 'TP. HCM' AND ten_kho = 'Thép Việt tiệp';

-- 3. Truy xuất lịch sử nhập hàng của kho “Cá hồi Nauy” trong quý 1 năm 2024.
SELECT * FROM khohang 
WHERE ten_kho = 'Cá hồi Nauy' 
  AND ngay_nhap >= '2024-01-01' AND ngay_nhap <= '2024-03-31' 
ALLOW FILTERING;

-- 4. Mặt hàng “Sữa Vinamilk không đường” có lô hàng “SV01KD” ngày sản xuất là ngày nào.
SELECT ngay_sx FROM mathang 
WHERE ten_hang = 'Sữa Vinamilk không đường' AND lo_hang = 'SV01KD' 
ALLOW FILTERING;

-- 5. Có bao nhiêu mặt hàng có quy cách là hộp và thuộc loại hàng nước.
SELECT COUNT(*) FROM mathang WHERE quy_cach = 'hộp' AND loai_hang = 'nước';

-- 6. Thông tin nhập hàng của phiếu nhập “PN010” tháng 9/2024
SELECT * FROM phieunhap 
WHERE ma_phieu = 'PN010' 
  AND ngay_nhap >= '2024-09-01' AND ngay_nhap <= '2024-09-30';

-- 7. Cho biết phiếu nhập “PN011” do nhân viên nào nhập, số lượng hàng nhập bao nhiêu.
SELECT nhan_vien, so_luong FROM phieunhap WHERE ma_phieu = 'PN011';

-- 8. Phiếu xuất cho khách hàng “Huỳnh Kim Anh” trị giá bao nhiêu.
SELECT SUM(tri_gia) AS tong_tri_gia FROM phieuxuat WHERE khach_hang = 'Huỳnh Kim Anh';

-- 9. Phiếu xuất nào có trị giá lớn nhất, nhỏ nhất trong quý 3/2024.
SELECT MIN(tri_gia) AS tri_gia_nho_nhat, MAX(tri_gia) AS tri_gia_lon_nhat FROM phieuxuat 
WHERE ngay_xuat >= '2024-07-01' AND ngay_xuat <= '2024-09-30' 
ALLOW FILTERING;

-- 10. Xem thông tin khách hàng và lịch sử mua hàng của khách hàng “Lê Anh Kiều” trong quý 2 năm 2024.
SELECT * FROM khachhang 
WHERE ho_ten = 'Lê Anh Kiều' 
  AND ngay_mua >= '2024-04-01' AND ngay_mua <= '2024-06-30';