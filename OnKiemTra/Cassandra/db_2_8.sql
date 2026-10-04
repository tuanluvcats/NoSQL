-- Bài tập 2.8 Hệ thống đặt vé xem phim, thiết kế CSDL phục vụ cho hệ thống đặt vé:
CREATE KEYSPACE IF NOT EXISTS ql_datvephim 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_datvephim;

-- 1. BẢNG PHIM
CREATE TABLE IF NOT EXISTS phim (
    genre text,
    release_date date,
    movie_id text,
    title text,
    duration int,
    PRIMARY KEY (genre, release_date, movie_id)
);

INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Hành động', '2024-05-15', 'MOV001', 'Fast & Furious 11', 130);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Hành động', '2024-08-20', 'MOV002', 'Deadpool 3', 120);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Hành động', '2023-12-10', 'MOV003', 'Mission Impossible', 140);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Hành động', '2025-01-01', 'MOV006', 'Avatar 3', 180);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Hài', '2024-02-14', 'MOV004', 'Mai', 110);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Kinh dị', '2024-10-31', 'MOV005', 'The Nun 3', 95);
INSERT INTO phim (genre, release_date, movie_id, title, duration) VALUES ('Tình cảm', '2024-03-08', 'MOV007', 'Lật Mặt 7', 105);

SELECT * from phim
-- 2. BẢNG RAP_CHIEU
CREATE TABLE IF NOT EXISTS rap_chieu (
    address text,
    capacity int,
    cinema_id text,
    name text,
    PRIMARY KEY (address, capacity, cinema_id)
);

INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('Hà Nội', 250, 'CGV01', 'CGV Vincom Bà Triệu');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('Hà Nội', 300, 'LOT01', 'Lotte Cinema Liễu Giai');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('Hà Nội', 150, 'BHD01', 'BHD Star Phạm Ngọc Thạch');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('Hà Nội', 180, 'GLX02', 'Galaxy Mipec Long Biên');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('TP. HCM', 400, 'CGV02', 'CGV Sư Vạn Hạnh');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('TP. HCM', 200, 'GLX01', 'Galaxy Nguyễn Du');
INSERT INTO rap_chieu (address, capacity, cinema_id, name) VALUES ('Đà Nẵng', 250, 'CGV03', 'CGV Vincom Đà Nẵng');

SELECT * from rap_chieu
-- 3. BẢNG VE_XEM_PHIM
CREATE TABLE IF NOT EXISTS ve_xem_phim (
    ticket_id text,
    movie_id text,
    cinema_id text,
    showtime timestamp,
    price int,
    customer_name text,
    PRIMARY KEY (ticket_id)
);

INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE789', 'MOV001', 'CGV01', '2024-05-15 19:00:00', 150000, 'Phan Thanh Trí');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE002', 'MOV001', 'CGV02', '2024-05-15 20:00:00', 120000, 'Nguyễn Văn A');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE003', 'MOV001', 'CGV01', '2024-05-15 19:00:00', 150000, 'Lê Thị B');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE004', 'MOV002', 'LOT01', '2024-08-20 18:30:00', 100000, 'Trần C');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE005', 'MOV004', 'BHD01', '2024-02-14 20:00:00', 90000, 'Hoàng D');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE006', 'MOV001', 'GLX01', '2024-05-16 10:00:00', 80000, 'Phạm E');
INSERT INTO ve_xem_phim (ticket_id, movie_id, cinema_id, showtime, price, customer_name) VALUES ('VE007', 'MOV007', 'CGV03', '2024-03-08 19:00:00', 110000, 'Vũ F');

SELECT * from ve_xem_phim

-- TRUY VẤN

-- BẢNG PHIM
-- 1. Tìm các phim thuộc thể loại “Hành động” công chiếu trong năm 2024.
SELECT * FROM phim 
WHERE genre = 'Hành động' 
AND release_date >= '2024-01-01' AND release_date <= '2024-12-31';

-- BẢNG RẠP CHIẾU
-- 2. Liệt kê các rạp chiếu tại Hà Nội có sức chứa trên 200 người.
SELECT * FROM rap_chieu 
WHERE address = 'Hà Nội' AND capacity > 200;

-- BẢNG VÉ XEM PHIM
-- 3. Cho biết thông tin vé có mã “VE789”, gồm tên khách, phim, rạp, thời gian chiếu, giá.
SELECT customer_name, movie_id, cinema_id, showtime, price 
FROM ve_xem_phim 
WHERE ticket_id = 'VE789';

-- 4. Tính tổng doanh thu bán vé cho phim “Fast & Furious 11” (Mã phim tương ứng là MOV001).
SELECT SUM(price) AS tong_doanh_thu 
FROM ve_xem_phim 
WHERE movie_id = 'MOV001' ALLOW FILTERING;