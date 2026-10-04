
CREATE KEYSPACE IF NOT EXISTS ql_thuvien 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_thuvien;

-- 1. BẢNG SACH
CREATE TABLE IF NOT EXISTS sach (
    language text,
    category text,
    published_year int,
    book_id text,
    title text,
    author text,
    PRIMARY KEY (language, category, published_year, book_id)
);

INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Anh', 'Khoa học máy tính', 2021, 'BK101', 'Clean Code', 'Robert C. Martin');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Anh', 'Khoa học máy tính', 2022, 'BK102', 'System Design Interview', 'Alex Xu');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Anh', 'Văn học', 2019, 'BK103', 'The Great Gatsby', 'F. Scott Fitzgerald');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Việt', 'Khoa học máy tính', 2023, 'BK104', 'Lập trình Java', 'Quách Tuấn Ngọc');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Việt', 'Văn học', 2018, 'BK105', 'Dế Mèn Phiêu Lưu Ký', 'Tô Hoài');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Việt', 'Kinh tế', 2021, 'BK106', 'Dạy con làm giàu', 'Robert Kiyosaki');
INSERT INTO sach (language, category, published_year, book_id, title, author) VALUES ('Tiếng Pháp', 'Văn học', 2015, 'BK107', 'Những người khốn khổ', 'Victor Hugo');

SELECT * FROM sach

-- 2. BẢNG THU_VIEN
CREATE TABLE IF NOT EXISTS thu_vien (
    location text,
    library_id text,
    name text,
    contact_info text,
    PRIMARY KEY (location, library_id)
);

INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('TP. HCM', 'LIB001', 'Thư viện Trung tâm ĐHQG', '0283123456');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('TP. HCM', 'LIB002', 'Thư viện Khoa học Tổng hợp', '0283654321');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('TP. HCM', 'LIB003', 'Thư viện ĐH Công Thương', '0283816167');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('Hà Nội', 'LIB004', 'Thư viện Quốc gia Việt Nam', '0243111222');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('Hà Nội', 'LIB005', 'Thư viện ĐH Bách Khoa HN', '0243999888');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('Đà Nẵng', 'LIB006', 'Thư viện Khoa học Tổng hợp Đà Nẵng', '0236777666');
INSERT INTO thu_vien (location, library_id, name, contact_info) VALUES ('Cần Thơ', 'LIB007', 'Thư viện Đại học Cần Thơ', '0292555444');

SELECT * FROM thu_vien
-- 3. BẢNG PHIEU_MUON
CREATE TABLE IF NOT EXISTS phieu_muon (
    book_id text,
    borrow_date date,
    borrow_id text,
    student_id text,
    return_date date,
    PRIMARY KEY (book_id, borrow_date, borrow_id)
);

INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK101', '2025-07-05', 'PM001', '2001230977', '2025-07-20');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK101', '2025-07-22', 'PM002', 'SV002', '2025-08-05');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK101', '2025-08-10', 'PM003', 'SV003', '2025-08-25');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK102', '2025-07-12', 'PM004', '2001230977', '2025-07-25');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK103', '2025-06-15', 'PM005', 'SV005', '2025-06-30');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK104', '2025-07-18', 'PM006', 'SV006', '2025-08-02');
INSERT INTO phieu_muon (book_id, borrow_date, borrow_id, student_id, return_date) VALUES ('BK105', '2025-09-01', 'PM007', 'SV007', '2025-09-15');

SELECT * FROM phieu_muon

-- TRUY VẤN

-- BẢNG SÁCH
-- 1. Tìm các sách có ngôn ngữ là “Tiếng Anh”.
SELECT * FROM sach WHERE language = 'Tiếng Anh';

-- 2. Cho biết tổng số sách thuộc thể loại “Khoa học máy tính”.
SELECT COUNT(*) FROM sach WHERE category = 'Khoa học máy tính' ALLOW FILTERING;

-- 3. Tìm những sách được xuất bản sau năm 2020.
SELECT * FROM sach WHERE published_year > 2020 ALLOW FILTERING;

-- BẢNG THƯ VIỆN
-- 4. Liệt kê thông tin các thư viện ở TP. HCM.
SELECT * FROM thu_vien WHERE location = 'TP. HCM';

-- BẢNG PHIẾU MƯỢN
-- 5. Cho biết danh sách các sinh viên đã mượn sách trong tháng 7/2025.
SELECT student_id, borrow_date, book_id 
FROM phieu_muon 
WHERE borrow_date >= '2025-07-01' AND borrow_date <= '2025-07-31' 
ALLOW FILTERING;

-- 6. Tính tổng số lượt mượn của sách có mã “BK101”.
SELECT COUNT(*) AS so_luot_muon FROM phieu_muon WHERE book_id = 'BK101';