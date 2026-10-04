// Chương 2 - MongoDB - Bài 1
// Chạy: docker exec -it nosql-mongo mongosh /baitap/Chuong02_MongoDB/bai01.js

db = db.getSiblingDB("baitap");

db.sinhvien.drop();

db.sinhvien.insertMany([
  { mssv: "001", ten: "An",  lop: "14DH", diem: 8.5 },
  { mssv: "002", ten: "Binh", lop: "14DH", diem: 6.0 },
  { mssv: "003", ten: "Chi",  lop: "14DH", diem: 9.2 }
]);

print("Sinh vien co diem >= 8:");
printjson(db.sinhvien.find({ diem: { $gte: 8 } }).toArray());

print("Diem trung binh theo lop:");
printjson(db.sinhvien.aggregate([
  { $group: { _id: "$lop", diemTB: { $avg: "$diem" }, siSo: { $sum: 1 } } }
]).toArray());
