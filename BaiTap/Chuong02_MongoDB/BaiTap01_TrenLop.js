// ==========================================================
// BÀI TẬP THỰC HÀNH MONGODB - BUỔI 1
// Bài tập 1 (bài tập trên lớp) - câu 2 đến câu 21
//
// Câu 1 (import) và câu 22 (export) chạy bằng mongoimport/mongoexport
// ở ngoài mongosh - xem file HUONG_DAN_BAI01.md.
//
// Chạy cả file:
//   docker exec -it nosql-mongo mongosh QLSinhVien /baitap/Chuong02_MongoDB/BaiTap01_TrenLop.js
//
// Hoặc gõ từng lệnh trong mongosh (cách học trên lớp):
//   docker exec -it nosql-mongo mongosh
//   use QLSinhVien
//   rồi chép từng lệnh bên dưới vào.
// ==========================================================

db = db.getSiblingDB("QLSinhVien");

// ---------- Câu 2: Thêm field Diachi cho SV011 ----------
db.sinhvien.updateOne(
  { Masv: "SV011" },
  { $set: { Diachi: "123 Lê Lợi, Quận 1, TP.HCM" } }
);

// ---------- Câu 3: Sửa Hoten của SV012 ----------
db.sinhvien.updateOne(
  { Masv: "SV012" },
  { $set: { Hoten: "Trần Thị Lan Anh" } }
);

// ---------- Câu 4: Xóa field Phai của SV013 ----------
// $unset xóa hẳn field khỏi document. Giá trị "" chỉ là chỗ giữ chỗ, không có ý nghĩa.
db.sinhvien.updateOne(
  { Masv: "SV013" },
  { $unset: { Phai: "" } }
);

// ---------- Câu 5: Đổi Ngaysinh của SV014 ----------
db.sinhvien.updateOne(
  { Masv: "SV014" },
  { $set: { Ngaysinh: "2004-03-01" } }
);

// ---------- Câu 6: Thêm field SoDT cho TẤT CẢ sinh viên ----------
// Filter rỗng {} = khớp mọi document. Dùng updateMany chứ không phải updateOne.
db.sinhvien.updateMany(
  {},
  { $set: { SoDT: "0900000000" } }
);

// ---------- Câu 7: Sửa Tenlop của lớp CTK45A ----------
// Lop là sub-document nên dùng đường dẫn chấm "Lop.Malop", nhớ đặt trong dấu nháy.
db.sinhvien.updateMany(
  { "Lop.Malop": "CTK45A" },
  { $set: { "Lop.Tenlop": "Công nghệ Thông tin 45A" } }
);

// ---------- Câu 8: Thêm field Khoa vào sub-document Lop của SV015 ----------
db.sinhvien.updateOne(
  { Masv: "SV015" },
  { $set: { "Lop.Khoa": "Khoa Kinh tế" } }
);

// ---------- Câu 9: Xóa toàn bộ sub-document Lop của SV016 ----------
db.sinhvien.updateOne(
  { Masv: "SV016" },
  { $unset: { Lop: "" } }
);

// ---------- Câu 10: Đổi Malop của SV017 từ KT45B sang KT45C ----------
db.sinhvien.updateOne(
  { Masv: "SV017" },
  { $set: { "Lop.Malop": "KT45C" } }
);

// ---------- Câu 11: Sửa Tenlop cho tất cả sinh viên lớp SPV44A ----------
db.sinhvien.updateMany(
  { "Lop.Malop": "SPV44A" },
  { $set: { "Lop.Tenlop": "Sư phạm Văn Khóa 44A" } }
);

// ---------- Câu 12: Thêm 1 email vào mảng Email của SV011 ----------
// $push thêm 1 phần tử vào cuối mảng.
db.sinhvien.updateOne(
  { Masv: "SV011" },
  { $push: { Email: "nam.nguyen@student.edu.vn" } }
);

// ---------- Câu 13: Xóa 1 email khỏi mảng Email của SV012 ----------
// $pull xóa mọi phần tử khớp giá trị.
db.sinhvien.updateOne(
  { Masv: "SV012" },
  { $pull: { Email: "lan.tran@gmail.com" } }
);

// ---------- Câu 14: Sửa email thứ 2 trong mảng của SV016 ----------
// Mảng đánh chỉ số từ 0, nên phần tử thứ 2 là "Email.1".
db.sinhvien.updateOne(
  { Masv: "SV016" },
  { $set: { "Email.1": "mai.nguyen@student.edu.vn" } }
);

// ---------- Câu 15: Thêm 2 email cùng lúc cho SV019 ----------
// $each cho phép $push nhiều phần tử trong một lệnh.
db.sinhvien.updateOne(
  { Masv: "SV019" },
  { $push: { Email: { $each: ["hung.dang@student.edu.vn", "hungdv@stu.edu.vn"] } } }
);

// ---------- Câu 16: Xóa toàn bộ danh sách Email của SV020 ----------
// Gán mảng rỗng: field Email vẫn còn nhưng không còn phần tử nào.
// Nếu muốn xóa hẳn field thì dùng: { $unset: { Email: "" } }
db.sinhvien.updateOne(
  { Masv: "SV020" },
  { $set: { Email: [] } }
);

// ---------- Câu 17: Thêm 1 môn học mới cho SV011 ----------
db.sinhvien.updateOne(
  { Masv: "SV011" },
  { $push: { Monhoc: { Mamh: "MH010", Tenmh: "Trí tuệ nhân tạo", Sotc: 3, Diem: 9.0 } } }
);

// ---------- Câu 18: Sửa Diem môn MH001 của SV012 thành 9.5 ----------
// Toán tử vị trí $ trỏ tới phần tử mảng đã khớp trong phần filter.
// Bắt buộc phải có điều kiện "Monhoc.Mamh" trong filter thì $ mới biết trỏ vào đâu.
db.sinhvien.updateOne(
  { Masv: "SV012", "Monhoc.Mamh": "MH001" },
  { $set: { "Monhoc.$.Diem": 9.5 } }
);

// ---------- Câu 19: Xóa môn MH003 của SV013 ----------
// $pull với điều kiện: xóa phần tử mảng có Mamh khớp.
db.sinhvien.updateOne(
  { Masv: "SV013" },
  { $pull: { Monhoc: { Mamh: "MH003" } } }
);

// ---------- Câu 20: Sửa Sotc môn "Mạng máy tính" từ 3 thành 4, cho cả lớp CTK45A ----------
db.sinhvien.updateMany(
  { "Lop.Malop": "CTK45A", "Monhoc.Tenmh": "Mạng máy tính" },
  { $set: { "Monhoc.$.Sotc": 4 } }
);

// ---------- Câu 21: Xóa toàn bộ danh sách Monhoc của SV020 ----------
db.sinhvien.updateOne(
  { Masv: "SV020" },
  { $set: { Monhoc: [] } }
);

// ---------- Kiểm tra kết quả ----------
print("Tong so sinh vien: " + db.sinhvien.countDocuments());
printjson(db.sinhvien.findOne({ Masv: "SV011" }));
