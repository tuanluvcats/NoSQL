-- Chương 3 - Cassandra - Bài 1
-- Chạy: docker exec -it nosql-cassandra cqlsh -f /baitap/Chuong03_Cassandra/bai01.cql

CREATE KEYSPACE IF NOT EXISTS baitap
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE baitap;

DROP TABLE IF EXISTS sinhvien;

CREATE TABLE sinhvien (
  lop  text,
  mssv text,
  ten  text,
  diem double,
  PRIMARY KEY (lop, mssv)
);

INSERT INTO sinhvien (lop, mssv, ten, diem) VALUES ('14DH', '001', 'An',   8.5);
INSERT INTO sinhvien (lop, mssv, ten, diem) VALUES ('14DH', '002', 'Binh', 6.0);
INSERT INTO sinhvien (lop, mssv, ten, diem) VALUES ('14DH', '003', 'Chi',  9.2);

SELECT * FROM sinhvien WHERE lop = '14DH';
