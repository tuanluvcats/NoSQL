
CREATE KEYSPACE IF NOT EXISTS ql_banhang 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_banhang;

-- 1. BẢNG KHACH_HANG
CREATE TABLE IF NOT EXISTS khach_hang (
    vip_status text,
    customer_id text,
    name text,
    email text,
    phone text,
    address text,
    PRIMARY KEY (vip_status, customer_id)
);

INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('VIP', 'KH201', 'Trần Lực', 'luc.tran@gmail.com', '0901112223', 'Q1, TP.HCM');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('Thường', 'KH202', 'Lê Mai', 'mai.le@gmail.com', '0902223334', 'Q3, TP.HCM');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('VIP', 'KH203', 'Nguyễn Tiến', 'tien.ng@gmail.com', '0903334445', 'Hà Nội');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('VIP', 'KH204', 'Phạm Hương', 'huong.p@gmail.com', '0904445556', 'Đà Nẵng');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('Thường', 'KH205', 'Vũ Tùng', 'tung.vu@gmail.com', '0905556667', 'Cần Thơ');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('Thường', 'KH206', 'Đỗ Quyên', 'quyen.do@gmail.com', '0906667778', 'Hải Phòng');
INSERT INTO khach_hang (vip_status, customer_id, name, email, phone, address) VALUES ('VIP', 'KH207', 'Lý Hải', 'hai.ly@gmail.com', '0907778889', 'Bình Dương');

SELECT * FROM khach_hang
-- 2. BẢNG DON_HANG
CREATE TABLE IF NOT EXISTS don_hang (
    customer_id text,
    order_date date,
    order_id text,
    total_amount int,
    PRIMARY KEY (customer_id, order_date, order_id)
);

INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH201', '2025-01-15', 'ORD001', 1500000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH203', '2025-04-20', 'ORD002', 3000000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH203', '2025-05-10', 'ORD003', 4500000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH204', '2025-05-25', 'ORD004', 1200000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH205', '2025-06-15', 'ORD005', 800000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH206', '2025-07-01', 'ORD006', 2000000);
INSERT INTO don_hang (customer_id, order_date, order_id, total_amount) VALUES ('KH203', '2025-08-10', 'ORD007', 5000000);

SELECT * FROM don_hang

-- 3. BẢNG CHI_TIET_DON_HANG
CREATE TABLE IF NOT EXISTS chi_tiet_don_hang (
    order_id text,
    quantity int,
    product_id text,
    unit_price int,
    PRIMARY KEY (order_id, quantity, product_id)
) WITH CLUSTERING ORDER BY (quantity DESC, product_id ASC);

INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD010', 2, 'SP001', 500000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD010', 10, 'SP002', 150000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD010', 5, 'SP003', 300000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD010', 1, 'SP004', 2000000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD002', 3, 'SP001', 500000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD003', 15, 'SP005', 300000);
INSERT INTO chi_tiet_don_hang (order_id, quantity, product_id, unit_price) VALUES ('ORD004', 4, 'SP006', 300000);

SELECT * FROM chi_tiet_don_hang

-- TRUY VẤN

-- BẢNG KHÁCH HÀNG
-- 1. Tìm các khách hàng có trạng thái VIP.
SELECT * FROM khach_hang WHERE vip_status = 'VIP';

-- BẢNG ĐƠN HÀNG
-- 2. Cho biết các đơn hàng trong quý 2 năm 2025 (Tháng 4, 5, 6).
SELECT * FROM don_hang 
WHERE order_date >= '2025-04-01' AND order_date <= '2025-06-30' 
ALLOW FILTERING;

-- 3. Tính tổng giá trị đơn hàng của khách hàng có mã “KH203”.
SELECT SUM(total_amount) AS tong_gia_tri FROM don_hang WHERE customer_id = 'KH203';

-- BẢNG CHI TIẾT ĐƠN HÀNG
-- 4. Tìm sản phẩm có số lượng mua nhiều nhất trong đơn hàng “ORD010”.
SELECT product_id, quantity, unit_price 
FROM chi_tiet_don_hang 
WHERE order_id = 'ORD010' LIMIT 1;