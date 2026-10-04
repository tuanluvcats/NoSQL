// =====================================================================
// BAI TAP 1 - BAI 2 (ve nha): Database QLThuVien, collection MuonSach
// Chay TUNG LENH mot trong mongosh, chup man hinh sau moi lenh.
// =====================================================================

// ---------------------------------------------------------------------
// Yeu cau 1: Tao database QLThuVien
use QLThuVien

// ---------------------------------------------------------------------
// Yeu cau 2: Tao collection MuonSach
db.createCollection("MuonSach")
show collections

// ---------------------------------------------------------------------
// Yeu cau 3 + 4: Nhap lieu (10 sinh vien, moi SV mot mang Sachs)
db.MuonSach.insertMany([
  {
    Masv: "SV001", Hoten: "Nguyễn Văn An", Namhoc: 2,
    Khoa: { Makhoa: "CNTT", Tenkhoa: "Công nghệ Thông tin" },
    Sachs: [
      { Masach: "B001", Tensach: "Cơ sở dữ liệu", Tacgia: "Nguyễn Văn Hòa",
        Ngaymuon: ISODate("2025-08-01"), Ngaytra: ISODate("2025-08-20"), Trangthai: "Đã trả" },
      { Masach: "B002", Tensach: "Mạng máy tính", Tacgia: "Phạm Quang Huy",
        Ngaymuon: ISODate("2025-08-15"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV002", Hoten: "Trần Thị Mai", Namhoc: 3,
    Khoa: { Makhoa: "CNTT", Tenkhoa: "Công nghệ Thông tin" },
    Sachs: [
      { Masach: "B001", Tensach: "Cơ sở dữ liệu", Tacgia: "Nguyễn Văn Hòa",
        Ngaymuon: ISODate("2025-07-10"), Ngaytra: ISODate("2025-07-30"), Trangthai: "Đã trả" },
      { Masach: "B003", Tensach: "Trí tuệ nhân tạo", Tacgia: "Hoàng Minh",
        Ngaymuon: ISODate("2025-08-18"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV003", Hoten: "Phạm Văn Khánh", Namhoc: 1,
    Khoa: { Makhoa: "KT", Tenkhoa: "Kinh tế" },
    Sachs: [
      { Masach: "B004", Tensach: "Kinh tế vi mô", Tacgia: "Trần Văn Quý",
        Ngaymuon: ISODate("2025-07-25"), Ngaytra: ISODate("2025-08-10"), Trangthai: "Đã trả" },
      { Masach: "B005", Tensach: "Kinh tế vĩ mô", Tacgia: "Ngô Thị Hạnh",
        Ngaymuon: ISODate("2025-08-15"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV004", Hoten: "Lê Hoàng Phúc", Namhoc: 2,
    Khoa: { Makhoa: "KT", Tenkhoa: "Kinh tế" },
    Sachs: [
      { Masach: "B004", Tensach: "Kinh tế vi mô", Tacgia: "Trần Văn Quý",
        Ngaymuon: ISODate("2025-08-01"), Ngaytra: ISODate("2025-08-22"), Trangthai: "Đã trả" },
      { Masach: "B004", Tensach: "Kinh tế vi mô", Tacgia: "Trần Văn Quý",
        Ngaymuon: ISODate("2025-08-25"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV005", Hoten: "Nguyễn Thị Hồng", Namhoc: 4,
    Khoa: { Makhoa: "SPV", Tenkhoa: "Sư phạm Văn" },
    Sachs: [
      { Masach: "B006", Tensach: "Văn học Việt Nam", Tacgia: "Nguyễn Thị Mai",
        Ngaymuon: ISODate("2025-07-28"), Ngaytra: ISODate("2025-08-14"), Trangthai: "Đã trả" },
      { Masach: "B007", Tensach: "Ngữ pháp tiếng Việt", Tacgia: "Hoàng Văn Quang",
        Ngaymuon: ISODate("2025-08-20"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV006", Hoten: "Đỗ Văn Hùng", Namhoc: 2,
    Khoa: { Makhoa: "VL", Tenkhoa: "Vật lý" },
    Sachs: [
      { Masach: "B008", Tensach: "Cơ học cổ điển", Tacgia: "Phạm Thanh Bình",
        Ngaymuon: ISODate("2025-08-02"), Ngaytra: ISODate("2025-08-18"), Trangthai: "Đã trả" },
      { Masach: "B009", Tensach: "Điện từ học", Tacgia: "Nguyễn Văn Thành",
        Ngaymuon: ISODate("2025-08-22"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV007", Hoten: "Nguyễn Thị Lan", Namhoc: 3,
    Khoa: { Makhoa: "SH", Tenkhoa: "Sinh học" },
    Sachs: [
      { Masach: "B010", Tensach: "Sinh học tế bào", Tacgia: "Trần Văn Hải",
        Ngaymuon: ISODate("2025-07-30"), Ngaytra: ISODate("2025-08-12"), Trangthai: "Đã trả" },
      { Masach: "B011", Tensach: "Di truyền học", Tacgia: "Phan Thị Thu",
        Ngaymuon: ISODate("2025-08-18"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV008", Hoten: "Hoàng Văn Quang", Namhoc: 1,
    Khoa: { Makhoa: "CNTT", Tenkhoa: "Công nghệ Thông tin" },
    Sachs: [
      { Masach: "B002", Tensach: "Mạng máy tính", Tacgia: "Phạm Quang Huy",
        Ngaymuon: ISODate("2025-08-01"), Ngaytra: ISODate("2025-08-17"), Trangthai: "Đã trả" },
      { Masach: "B003", Tensach: "Trí tuệ nhân tạo", Tacgia: "Hoàng Minh",
        Ngaymuon: ISODate("2025-08-20"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV009", Hoten: "Bùi Văn Khoa", Namhoc: 3,
    Khoa: { Makhoa: "KT", Tenkhoa: "Kinh tế" },
    Sachs: [
      { Masach: "B005", Tensach: "Kinh tế vĩ mô", Tacgia: "Ngô Thị Hạnh",
        Ngaymuon: ISODate("2025-07-22"), Ngaytra: ISODate("2025-08-08"), Trangthai: "Đã trả" },
      { Masach: "B006", Tensach: "Văn học Việt Nam", Tacgia: "Nguyễn Thị Mai",
        Ngaymuon: ISODate("2025-08-15"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  },
  {
    Masv: "SV010", Hoten: "Ngô Thị Thu", Namhoc: 2,
    Khoa: { Makhoa: "SPV", Tenkhoa: "Sư phạm Văn" },
    Sachs: [
      { Masach: "B006", Tensach: "Văn học Việt Nam", Tacgia: "Nguyễn Thị Mai",
        Ngaymuon: ISODate("2025-08-05"), Ngaytra: ISODate("2025-08-21"), Trangthai: "Đã trả" },
      { Masach: "B006", Tensach: "Văn học Việt Nam", Tacgia: "Nguyễn Thị Mai",
        Ngaymuon: ISODate("2025-08-23"), Ngaytra: null, Trangthai: "Đang mượn" }
    ]
  }
])

db.MuonSach.find()

// =====================================================================
// CAC THAO TAC
// =====================================================================

// ---------------------------------------------------------------------
// Cau 1: Them field Diachi cho SV001
db.MuonSach.updateOne(
  { Masv: "SV001" },
  { $set: { Diachi: "25 Nguyễn Huệ, Quận 1, TP.HCM" } }
)
db.MuonSach.find({ Masv: "SV001" }, { Masv: 1, Hoten: 1, Diachi: 1 })

// ---------------------------------------------------------------------
// Cau 2: Cap nhat Hoten cua SV002 thanh "Tran Thi Mai Anh"
db.MuonSach.updateOne(
  { Masv: "SV002" },
  { $set: { Hoten: "Trần Thị Mai Anh" } }
)
db.MuonSach.find({ Masv: "SV002" }, { Masv: 1, Hoten: 1 })

// ---------------------------------------------------------------------
// Cau 3: Xoa field Namhoc cua SV003
db.MuonSach.updateOne(
  { Masv: "SV003" },
  { $unset: { Namhoc: "" } }
)
db.MuonSach.find({ Masv: "SV003" }, { Masv: 1, Hoten: 1, Namhoc: 1 })

// ---------------------------------------------------------------------
// Cau 4: Doi Namhoc cua SV004 thanh 3
db.MuonSach.updateOne(
  { Masv: "SV004" },
  { $set: { Namhoc: 3 } }
)
db.MuonSach.find({ Masv: "SV004" }, { Masv: 1, Hoten: 1, Namhoc: 1 })

// ---------------------------------------------------------------------
// Cau 5: Them field SoDT cho TAT CA sinh vien
db.MuonSach.updateMany(
  {},
  { $set: { SoDT: "0912345678" } }
)
db.MuonSach.find({}, { Masv: 1, Hoten: 1, SoDT: 1 })

// ---------------------------------------------------------------------
// Cau 6: Cap nhat Tenkhoa cua khoa CNTT
db.MuonSach.updateMany(
  { "Khoa.Makhoa": "CNTT" },
  { $set: { "Khoa.Tenkhoa": "Công nghệ thông tin và truyền thông" } }
)
db.MuonSach.find({ "Khoa.Makhoa": "CNTT" }, { Masv: 1, Khoa: 1 })

// ---------------------------------------------------------------------
// Cau 7: Them field Truongkhoa vao sub-document Khoa cua SV005
db.MuonSach.updateOne(
  { Masv: "SV005" },
  { $set: { "Khoa.Truongkhoa": "TS. Nguyễn Văn Bình" } }
)
db.MuonSach.find({ Masv: "SV005" }, { Masv: 1, Khoa: 1 })

// ---------------------------------------------------------------------
// Cau 8: Xoa sub-document Khoa cua SV006
db.MuonSach.updateOne(
  { Masv: "SV006" },
  { $unset: { Khoa: "" } }
)
db.MuonSach.find({ Masv: "SV006" }, { Masv: 1, Hoten: 1, Khoa: 1 })

// ---------------------------------------------------------------------
// Cau 9: Cap nhat Makhoa cua SV007 tu "SH" thanh "SINH"
db.MuonSach.updateOne(
  { Masv: "SV007", "Khoa.Makhoa": "SH" },
  { $set: { "Khoa.Makhoa": "SINH" } }
)
db.MuonSach.find({ Masv: "SV007" }, { Masv: 1, Khoa: 1 })

// ---------------------------------------------------------------------
// Cau 10: Cap nhat Tenkhoa cua tat ca SV khoa SPV
db.MuonSach.updateMany(
  { "Khoa.Makhoa": "SPV" },
  { $set: { "Khoa.Tenkhoa": "Sư phạm Ngữ văn" } }
)
db.MuonSach.find({ "Khoa.Makhoa": "SPV" }, { Masv: 1, Khoa: 1 })

// ---------------------------------------------------------------------
// Cau 11: Them mot sach moi cho SV001
db.MuonSach.updateOne(
  { Masv: "SV001" },
  { $push: { Sachs: {
      Masach: "B012", Tensach: "Phân tích dữ liệu", Tacgia: "Lê Văn Bình",
      Ngaymuon: ISODate("2025-08-24"), Ngaytra: null, Trangthai: "Đang mượn"
  } } }
)
db.MuonSach.find({ Masv: "SV001" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 12: Xoa sach B003 khoi mang Sachs cua SV002
db.MuonSach.updateOne(
  { Masv: "SV002" },
  { $pull: { Sachs: { Masach: "B003" } } }
)
db.MuonSach.find({ Masv: "SV002" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 13: Cap nhat Trangthai = "Da tra" cho sach B005 cua SV003
db.MuonSach.updateOne(
  { Masv: "SV003", "Sachs.Masach": "B005" },
  { $set: { "Sachs.$.Trangthai": "Đã trả" } }
)
db.MuonSach.find({ Masv: "SV003" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 14: Cap nhat Ngaytra = "2025-09-01" cho sach B004 cua SV004
// (SV004 co 2 ban ghi B004 -> dung arrayFilters de cap nhat CA HAI)
db.MuonSach.updateOne(
  { Masv: "SV004" },
  { $set: { "Sachs.$[s].Ngaytra": ISODate("2025-09-01") } },
  { arrayFilters: [ { "s.Masach": "B004" } ] }
)
db.MuonSach.find({ Masv: "SV004" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 15: Xoa toan bo danh sach Sachs cua SV005
db.MuonSach.updateOne(
  { Masv: "SV005" },
  { $unset: { Sachs: "" } }
)
db.MuonSach.find({ Masv: "SV005" })

// ---------------------------------------------------------------------
// Cau 16: Them nhieu sach mot luc ($each) cho SV006
db.MuonSach.updateOne(
  { Masv: "SV006" },
  { $push: { Sachs: { $each: [
      { Masach: "B013", Tensach: "Vật lý đại cương", Tacgia: "Lương Duyên Bình",
        Ngaymuon: ISODate("2025-08-24"), Ngaytra: null, Trangthai: "Đang mượn" },
      { Masach: "B014", Tensach: "Quang học", Tacgia: "Trần Ngọc Hợi",
        Ngaymuon: ISODate("2025-08-24"), Ngaytra: null, Trangthai: "Đang mượn" }
  ] } } }
)
db.MuonSach.find({ Masv: "SV006" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 17: Doi Tensach "Ngu phap tieng Viet" -> "... nang cao" cho TAT CA SV
db.MuonSach.updateMany(
  { "Sachs.Tensach": "Ngữ pháp tiếng Việt" },
  { $set: { "Sachs.$[s].Tensach": "Ngữ pháp tiếng Việt nâng cao" } },
  { arrayFilters: [ { "s.Tensach": "Ngữ pháp tiếng Việt" } ] }
)
db.MuonSach.find({ "Sachs.Tensach": "Ngữ pháp tiếng Việt nâng cao" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 18: Xoa tat ca sach co Trangthai = "Da tra" cua SV007
db.MuonSach.updateOne(
  { Masv: "SV007" },
  { $pull: { Sachs: { Trangthai: "Đã trả" } } }
)
db.MuonSach.find({ Masv: "SV007" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 19: Cap nhat Tacgia = "Nguyen Van A" cho sach B006 cua TAT CA SV
db.MuonSach.updateMany(
  { "Sachs.Masach": "B006" },
  { $set: { "Sachs.$[s].Tacgia": "Nguyễn Văn A" } },
  { arrayFilters: [ { "s.Masach": "B006" } ] }
)
db.MuonSach.find({ "Sachs.Masach": "B006" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 20: Xoa sach muon truoc ngay "2025-08-01" cua SV009
db.MuonSach.updateOne(
  { Masv: "SV009" },
  { $pull: { Sachs: { Ngaymuon: { $lt: ISODate("2025-08-01") } } } }
)
db.MuonSach.find({ Masv: "SV009" }, { Masv: 1, Sachs: 1 })

// ---------------------------------------------------------------------
// Cau 21: Backup du lieu ra thu muc QLTV
// Chay o PowerShell (KHONG phai trong mongosh):
//   docker exec -it nosql-mongo mongodump -d QLThuVien -o /QLTV
//   docker cp nosql-mongo:/QLTV "D:\Documents\Homework\Nam4\NoSQL\BaiTap\Bai01\QLTV"
