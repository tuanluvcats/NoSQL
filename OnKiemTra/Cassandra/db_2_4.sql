CREATE KEYSPACE IF NOT EXISTS qlnhanvien 
WITH REPLICATION = { 'class': 'SimpleStrategy', 'replication_factor': 1 };

USE qlnhanvien;

CREATE TABLE IF NOT EXISTS nhanvien (
    manv text PRIMARY KEY,
    hoten text,
    ngaysinh date,
    phai text,
    dienthoai text,
    email text,
    phong text
);

INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV001', 'Đỗ Thị Lan', '1990-04-23', 'Nữ', '0914045226', 'landt@gmail.com', 'P01');
INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV002', 'Võ Minh Trung', '1982-08-15', 'Nam', '0904591163', 'trungvm@gmail.com', 'P01');
INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV003', 'Lê Thị Mỹ Ngọc', '1992-05-14', 'Nữ', '0376578895', 'ngoc@gmail.com', 'P02');
INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV004', 'Trần Văn Bình', '1992-03-24', 'Nam', '0982556227', 'binh@gmail.com', 'P02');
INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV005', 'Đỗ Thị Lài', '1983-05-26', 'Nữ', '0902234888', 'thanhdt@gmail.com', 'P03');
INSERT INTO nhanvien (manv, hoten, ngaysinh, phai, dienthoai, email, phong) VALUES ('NV006', 'Trương Hữu Chí', '1977-05-18', 'Nam', '0964435675', 'chi@gmail.com', 'P03');