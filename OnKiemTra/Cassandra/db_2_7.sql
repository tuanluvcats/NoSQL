-- Bài tập 2.7 Quản lý học trực tuyến, thiết kế CSDL cho nền tảng học trực tuyến: 
CREATE KEYSPACE IF NOT EXISTS ql_hoctructuyen 
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 1 
};

USE ql_hoctructuyen;


-- 1. BẢNG NGUOI_DUNG
CREATE TABLE IF NOT EXISTS nguoi_dung (
    role text,
    joined_date date,
    user_id text,
    full_name text,
    email text,
    PRIMARY KEY (role, joined_date, user_id)
);

INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('teacher', '2022-11-20', 'GV002', 'Lê Thị Bình', 'binh.lt@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('teacher', '2023-05-10', 'GV001', 'Nguyễn Văn An', 'an.nv@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('teacher', '2023-10-01', 'GV004', 'Đinh Hữu Khoa', 'khoa.dh@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('teacher', '2024-01-15', 'GV003', 'Trần Minh Cường', 'cuong.tm@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('student', '2023-01-20', 'SV009', 'Hoàng Thanh Trúc', 'truc.ht@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('student', '2023-08-05', 'SV007', 'Phạm Quốc Đạt', 'dat.pq@gmail.com');
INSERT INTO nguoi_dung (role, joined_date, user_id, full_name, email) VALUES ('student', '2024-02-10', 'SV008', 'Vũ Ngọc Hân', 'han.vn@gmail.com');

SELECT * FROM nguoi_dung

-- 2. BẢNG KHOA_HOC
CREATE TABLE IF NOT EXISTS khoa_hoc (
    category text,
    course_id text,
    title text,
    teacher_id text,
    created_date date,
    PRIMARY KEY (category, course_id)
);

INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Công nghệ thông tin', 'IT001', 'Lập trình Java căn bản', 'GV001', '2023-06-01');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Công nghệ thông tin', 'IT002', 'Backend với Spring Boot', 'GV001', '2023-09-15');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Công nghệ thông tin', 'IT003', 'Cơ sở dữ liệu NoSQL', 'GV003', '2024-02-20');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Công nghệ thông tin', 'IT004', 'Cấu trúc dữ liệu và giải thuật', 'GV003', '2024-03-01');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Kinh tế', 'EC001', 'Kinh tế vi mô', 'GV002', '2022-12-05');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Ngoại ngữ', 'EN001', 'Tiếng Anh giao tiếp', 'GV004', '2023-11-10');
INSERT INTO khoa_hoc (category, course_id, title, teacher_id, created_date) VALUES ('Ngoại ngữ', 'EN002', 'Luyện thi IELTS 6.5', 'GV004', '2024-01-05');

SELECT * FROM khoa_hoc

-- 3. BẢNG THAM_GIA_KHOA_HOC
CREATE TABLE IF NOT EXISTS tham_gia_khoa_hoc (
    user_id text,
    course_id text,
    progress int,
    last_access date,
    PRIMARY KEY (user_id, course_id)
);

INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV007', 'IT001', 100, '2024-05-10');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV007', 'IT002', 45, '2024-06-15');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV007', 'EN002', 10, '2024-06-18');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV008', 'EC001', 80, '2024-04-20');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV008', 'IT003', 60, '2024-05-25');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV009', 'EN001', 20, '2024-06-01');
INSERT INTO tham_gia_khoa_hoc (user_id, course_id, progress, last_access) VALUES ('SV009', 'IT004', 90, '2024-06-10');

SELECT * FROM tham_gia_khoa_hoc

--  TRUY VẤN

-- BẢNG NGƯỜI DÙNG
-- 1. Liệt kê danh sách giảng viên đã tham gia từ năm 2023.
SELECT * FROM nguoi_dung 
WHERE role = 'teacher' AND joined_date >= '2023-01-01';

-- BẢNG KHÓA HỌC
-- 2. Cho biết các khóa học thuộc danh mục “Công nghệ thông tin”.
SELECT * FROM khoa_hoc 
WHERE category = 'Công nghệ thông tin';

-- BẢNG THAM GIA KHÓA HỌC
-- 3. Cho biết danh sách khóa học mà sinh viên “SV007” đã tham gia.
SELECT course_id, progress, last_access 
FROM tham_gia_khoa_hoc 
WHERE user_id = 'SV007';