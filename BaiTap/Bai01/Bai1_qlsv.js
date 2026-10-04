// =====================================================================
// BAI TAP 1 - BAI 1 (tren lop): Database qlsv, collection sv
// Chay TUNG LENH mot trong mongosh, chup man hinh sau moi lenh.
// Mo shell:
//   docker start nosql-mongo
//   docker exec -it nosql-mongo mongosh
// =====================================================================

// ---------------------------------------------------------------------
// Cau 1: Import du lieu tu file duoc cung cap
// Chay 2 lenh sau o PowerShell (KHONG phai trong mongosh):
//   docker cp "D:\Documents\Homework\Nam4\NoSQL\BaiTap\qlsv.SinhVien.json" nosql-mongo:/qlsv.SinhVien.json
//   docker exec -it nosql-mongo mongoimport -d qlsv -c sv --file /qlsv.SinhVien.json --jsonArray --drop
// Roi vao mongosh kiem tra:
use qlsv
db.sv.find()

// ---------------------------------------------------------------------
// Cau 2: Them field Diachi cho sinh vien Masv = "SV011"
db.sv.updateOne(
  { Masv: "SV011" },
  { $set: { Diachi: "12 Le Loi, Quan 1, TP.HCM" } }
)
db.sv.find({ Masv: "SV011" }, { Masv: 1, Hoten: 1, Diachi: 1 })

// ---------------------------------------------------------------------
// Cau 3: Cap nhat Hoten cua SV012 thanh "Tran Thi Lan Anh"
db.sv.updateOne(
  { Masv: "SV012" },
  { $set: { Hoten: "Trần Thị Lan Anh" } }
)
db.sv.find({ Masv: "SV012" }, { Masv: 1, Hoten: 1 })

// ---------------------------------------------------------------------
// Cau 4: Xoa field Phai cua SV013
db.sv.updateOne(
  { Masv: "SV013" },
  { $unset: { Phai: "" } }
)
db.sv.find({ Masv: "SV013" }, { Masv: 1, Hoten: 1, Phai: 1 })

// ---------------------------------------------------------------------
// Cau 5: Doi Ngaysinh cua SV014 sang "2004-03-01"
db.sv.updateOne(
  { Masv: "SV014" },
  { $set: { Ngaysinh: ISODate("2004-03-01T00:00:00.000Z") } }
)
db.sv.find({ Masv: "SV014" }, { Masv: 1, Hoten: 1, Ngaysinh: 1 })

// ---------------------------------------------------------------------
// Cau 6: Them field SoDT cho TAT CA sinh vien
db.sv.updateMany(
  {},
  { $set: { SoDT: "0900000000" } }
)
db.sv.find({}, { Masv: 1, Hoten: 1, SoDT: 1 })

// ---------------------------------------------------------------------
// Cau 7: Cap nhat Tenlop cua lop Malop = "CTK45A"
db.sv.updateMany(
  { "Lop.Malop": "CTK45A" },
  { $set: { "Lop.Tenlop": "Công nghệ Thông tin 45A" } }
)
db.sv.find({ "Lop.Malop": "CTK45A" }, { Masv: 1, Lop: 1 })

// ---------------------------------------------------------------------
// Cau 8: Them field Khoa vao sub-document Lop cua SV015
db.sv.updateOne(
  { Masv: "SV015" },
  { $set: { "Lop.Khoa": "Khoa Kinh tế" } }
)
db.sv.find({ Masv: "SV015" }, { Masv: 1, Lop: 1 })

// ---------------------------------------------------------------------
// Cau 9: Xoa toan bo sub-document Lop cua SV016
db.sv.updateOne(
  { Masv: "SV016" },
  { $unset: { Lop: "" } }
)
db.sv.find({ Masv: "SV016" }, { Masv: 1, Hoten: 1, Lop: 1 })

// ---------------------------------------------------------------------
// Cau 10: Doi Malop cua SV017 tu "KT45B" sang "KT45C"
db.sv.updateOne(
  { Masv: "SV017", "Lop.Malop": "KT45B" },
  { $set: { "Lop.Malop": "KT45C" } }
)
db.sv.find({ Masv: "SV017" }, { Masv: 1, Lop: 1 })

// ---------------------------------------------------------------------
// Cau 11: Cap nhat Tenlop = "Su pham Van Khoa 44A" cho moi SV co Malop = "SPV44A"
db.sv.updateMany(
  { "Lop.Malop": "SPV44A" },
  { $set: { "Lop.Tenlop": "Sư phạm Văn Khóa 44A" } }
)
db.sv.find({ "Lop.Malop": "SPV44A" }, { Masv: 1, Lop: 1 })

// ---------------------------------------------------------------------
// Cau 12: Them email moi vao mang Email cua SV011
db.sv.updateOne(
  { Masv: "SV011" },
  { $push: { Email: "nam.nguyen@student.edu.vn" } }
)
db.sv.find({ Masv: "SV011" }, { Masv: 1, Email: 1 })

// ---------------------------------------------------------------------
// Cau 13: Xoa email "lan.tran@gmail.com" khoi mang Email cua SV012
db.sv.updateOne(
  { Masv: "SV012" },
  { $pull: { Email: "lan.tran@gmail.com" } }
)
db.sv.find({ Masv: "SV012" }, { Masv: 1, Email: 1 })

// ---------------------------------------------------------------------
// Cau 14: Cap nhat email THU 2 (index 1) cua SV016
db.sv.updateOne(
  { Masv: "SV016" },
  { $set: { "Email.1": "mai.nguyen@student.edu.vn" } }
)
db.sv.find({ Masv: "SV016" }, { Masv: 1, Email: 1 })

// ---------------------------------------------------------------------
// Cau 15: Them 2 email moi vao mang Email cua SV019
db.sv.updateOne(
  { Masv: "SV019" },
  { $push: { Email: { $each: [ "hung.dang@student.edu.vn", "hungdang2004@stu.edu.vn" ] } } }
)
db.sv.find({ Masv: "SV019" }, { Masv: 1, Email: 1 })

// ---------------------------------------------------------------------
// Cau 16: Xoa toan bo danh sach Email cua SV020
db.sv.updateOne(
  { Masv: "SV020" },
  { $unset: { Email: "" } }
)
db.sv.find({ Masv: "SV020" }, { Masv: 1, Hoten: 1, Email: 1 })

// ---------------------------------------------------------------------
// Cau 17: Them mon hoc moi cho SV011
db.sv.updateOne(
  { Masv: "SV011" },
  { $push: { Monhoc: { Mamh: "MH010", Tenmh: "Trí tuệ nhân tạo", Sotc: 3, Diem: 9.0 } } }
)
db.sv.find({ Masv: "SV011" }, { Masv: 1, Monhoc: 1 })

// ---------------------------------------------------------------------
// Cau 18: Cap nhat Diem cua MH001 thanh 9.5 cho SV012
db.sv.updateOne(
  { Masv: "SV012", "Monhoc.Mamh": "MH001" },
  { $set: { "Monhoc.$.Diem": 9.5 } }
)
db.sv.find({ Masv: "SV012" }, { Masv: 1, Monhoc: 1 })

// ---------------------------------------------------------------------
// Cau 19: Xoa mon hoc MH003 cua SV013
db.sv.updateOne(
  { Masv: "SV013" },
  { $pull: { Monhoc: { Mamh: "MH003" } } }
)
db.sv.find({ Masv: "SV013" }, { Masv: 1, Monhoc: 1 })

// ---------------------------------------------------------------------
// Cau 20: Sotc cua mon "Mang may tinh" tu 3 -> 4 cho moi SV lop CTK45A
db.sv.updateMany(
  { "Lop.Malop": "CTK45A", "Monhoc.Tenmh": "Mạng máy tính" },
  { $set: { "Monhoc.$.Sotc": 4 } }
)
db.sv.find({ "Lop.Malop": "CTK45A" }, { Masv: 1, Monhoc: 1 })

// ---------------------------------------------------------------------
// Cau 21: Xoa toan bo danh sach Monhoc cua SV020
db.sv.updateOne(
  { Masv: "SV020" },
  { $unset: { Monhoc: "" } }
)
db.sv.find({ Masv: "SV020" })

// ---------------------------------------------------------------------
// Cau 22: Export collection sv ra file sinhvien.json
// Chay o PowerShell (KHONG phai trong mongosh):
//   docker exec -it nosql-mongo mongoexport -d qlsv -c sv --out /sinhvien.json --jsonArray --pretty
//   docker cp nosql-mongo:/sinhvien.json "D:\Documents\Homework\Nam4\NoSQL\BaiTap\Bai01\sinhvien.json"
