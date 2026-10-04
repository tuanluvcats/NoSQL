// =====================================================================
// BAI TAP 7 & 8 - Trang 35, 36 (TH_HUONG DAN THUC HANH NoSQL_2025.pdf)
// Aggregation Framework
//   Bai 7: CSDL quan ly ban san pham  -> collection hoadon (16 cau)
//   Bai 8: CSDL quan ly sinh vien     -> collection sv     (6 cau)
//
// Cach dung: chay TUNG LENH mot trong mongosh, chup man hinh ket qua,
// dan vao file 47_2001230855_PhamAnhTuan(1).docx ngay duoi tieu de
// tuong ung (dung format: dong tieu de -> anh chup ket qua).
//
// Mo shell:
//   docker start nosql-mongo
//   docker exec -it nosql-mongo mongosh
//
// ---------------------------------------------------------------------
// VI SAO PHAI SEED LAI DU LIEU (PHAN A)
// ---------------------------------------------------------------------
// Du lieu hoadon hien tai da bi bai 3 cau b (xoa hoa don ngay 2020-03-25)
// va cau c (xoa hoa don cua kh001) lam mat mot so document: anh chup cau 1
// khong con kh001, anh chup cau 3 khong con hd001 va hd005.
// Hau qua: bai 7 cau 5 (dia chi TPHCM), cau 15 (nam 2020), cau 16
// (thang 7 nam 2020) co the tra ve rong.
// Phan A ben duoi seed lai bo du lieu thoa DAY DU rang buoc cua bai 3,
// bai 6 va bai 7 nen moi cau deu co ket qua de chup man hinh.
// Luu y: sau khi seed lai can chup lai 3 anh cua cau 1, 2, 3.
// =====================================================================


// =====================================================================
// PHAN A - SEED DU LIEU
// =====================================================================

// ---------------------------------------------------------------------
// A1. Collection hoadon (CSDL quan ly ban san pham - bai 3)
// Cau truc theo bai 3 trang 34:
//   MaHD, NgayLap, KhachHang{MaKH, TenKH, DiaChi},
//   SanPhamBan:[{MaSP, TenSP, SoLuong, GiaBan, ThanhTien}]
//
// Bo du lieu nay thoa cac rang buoc:
//   - bai 3: hd001, hd003, kh001, kh003, ngay 2020-03-25, ngay 2021-02-25
//   - bai 6: ngay 12/03/2021; kh001; sp012 voi SoLuong > 30;
//            khoang 01/03/2020 - 30/05/2021; ngay 05/07/2020
//   - bai 7: khach "Tran Minh Tuan"; dia chi TPHCM; khoang 12/03/2021 -
//            20/03/2021; khach co tren 2 hoa don; hoa don thang 7;
//            hoa don nam 2020; hoa don thang 7 nam 2020;
//            mot san pham co 2 muc gia khac nhau (de cau 9 tinh $avg
//            ra so co y nghia: sp001 ban gia 500000 va 550000)
//
// Chay ca khoi lenh nay mot lan (khong can chup man hinh).
// ---------------------------------------------------------------------
use qlbanhang

db.hoadon.drop()

db.hoadon.insertMany([
  {
    MaHD: "hd001",
    NgayLap: ISODate("2020-03-25"),
    KhachHang: { MaKH: "kh001", TenKH: "Trần Thị Lan", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp001", TenSP: "Bàn phím cơ", SoLuong: 2, GiaBan: 500000, ThanhTien: 1000000 },
      { MaSP: "sp002", TenSP: "Chuột không dây", SoLuong: 1, GiaBan: 200000, ThanhTien: 200000 }
    ]
  },
  {
    MaHD: "hd002",
    NgayLap: ISODate("2021-03-12"),
    KhachHang: { MaKH: "kh002", TenKH: "Trần Minh Tuấn", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp003", TenSP: "Màn hình 24 inch", SoLuong: 1, GiaBan: 2500000, ThanhTien: 2500000 },
      { MaSP: "sp001", TenSP: "Bàn phím cơ", SoLuong: 1, GiaBan: 550000, ThanhTien: 550000 }
    ]
  },
  {
    MaHD: "hd003",
    NgayLap: ISODate("2021-03-12"),
    KhachHang: { MaKH: "kh003", TenKH: "Đỗ Thanh Bình", DiaChi: "Hà Nội" },
    SanPhamBan: [
      { MaSP: "sp004", TenSP: "Tai nghe Bluetooth", SoLuong: 2, GiaBan: 450000, ThanhTien: 900000 },
      { MaSP: "sp005", TenSP: "USB 32GB", SoLuong: 3, GiaBan: 150000, ThanhTien: 450000 }
    ]
  },
  {
    MaHD: "hd004",
    NgayLap: ISODate("2021-07-15"),
    KhachHang: { MaKH: "kh002", TenKH: "Trần Minh Tuấn", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp002", TenSP: "Chuột không dây", SoLuong: 2, GiaBan: 200000, ThanhTien: 400000 }
    ]
  },
  {
    MaHD: "hd005",
    NgayLap: ISODate("2020-07-05"),
    KhachHang: { MaKH: "kh001", TenKH: "Trần Thị Lan", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp003", TenSP: "Màn hình 24 inch", SoLuong: 1, GiaBan: 2500000, ThanhTien: 2500000 },
      { MaSP: "sp005", TenSP: "USB 32GB", SoLuong: 5, GiaBan: 150000, ThanhTien: 750000 }
    ]
  },
  {
    MaHD: "hd006",
    NgayLap: ISODate("2020-07-08"),
    KhachHang: { MaKH: "kh004", TenKH: "Lê Văn Nam", DiaChi: "Đà Nẵng" },
    SanPhamBan: [
      { MaSP: "sp001", TenSP: "Bàn phím cơ", SoLuong: 1, GiaBan: 500000, ThanhTien: 500000 }
    ]
  },
  {
    MaHD: "hd007",
    NgayLap: ISODate("2021-04-01"),
    KhachHang: { MaKH: "kh002", TenKH: "Trần Minh Tuấn", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp004", TenSP: "Tai nghe Bluetooth", SoLuong: 1, GiaBan: 450000, ThanhTien: 450000 }
    ]
  },
  {
    MaHD: "hd008",
    NgayLap: ISODate("2021-03-18"),
    KhachHang: { MaKH: "kh004", TenKH: "Lê Văn Nam", DiaChi: "Đà Nẵng" },
    SanPhamBan: [
      { MaSP: "sp012", TenSP: "Giấy in A4", SoLuong: 50, GiaBan: 70000, ThanhTien: 3500000 },
      { MaSP: "sp002", TenSP: "Chuột không dây", SoLuong: 1, GiaBan: 200000, ThanhTien: 200000 }
    ]
  },
  {
    MaHD: "hd009",
    NgayLap: ISODate("2020-11-20"),
    KhachHang: { MaKH: "kh001", TenKH: "Trần Thị Lan", DiaChi: "TPHCM" },
    SanPhamBan: [
      { MaSP: "sp005", TenSP: "USB 32GB", SoLuong: 2, GiaBan: 150000, ThanhTien: 300000 }
    ]
  },
  {
    MaHD: "hd010",
    NgayLap: ISODate("2021-02-25"),
    KhachHang: { MaKH: "kh003", TenKH: "Đỗ Thanh Bình", DiaChi: "Hà Nội" },
    SanPhamBan: [
      { MaSP: "sp012", TenSP: "Giấy in A4", SoLuong: 10, GiaBan: 70000, ThanhTien: 700000 },
      { MaSP: "sp003", TenSP: "Màn hình 24 inch", SoLuong: 1, GiaBan: 2500000, ThanhTien: 2500000 }
    ]
  }
])

db.hoadon.find()

// ---------------------------------------------------------------------
// A2. Collection sv (CSDL quan ly sinh vien - bai 2)
// Cau truc theo bai 2 trang 33-34 + cac truong Tuoi, Diachi, Quoctich,
// Ngoaingu duoc dung o bai 2 cau e/f va bai 5.
//
// Bo du lieu nay thoa cac rang buoc:
//   - bai 2: sv001, sv003, sv005, lop l03, mang Ngoaingu co >= 2 phan tu,
//            mang Monhoc co >= 1 phan tu
//   - bai 5: nu hoc Tieng Anh; nam tren 22 tuoi; ho ten bat dau chu T;
//            ten Lan; Tieng Phap / Tieng Nhat; lop 08DHTH va 09DHTH;
//            09DHTH tuoi <23 hoac >25; mon "Cơ sở dữ liệu" diem > 7.5
//   - bai 8: moi lop co nhieu sinh vien; co mon hoc duoc >= 2 SV hoc
//
// Tuoi duoc dat khop voi Ngaysinh tinh den nam 2026.
// Chay ca khoi lenh nay mot lan (khong can chup man hinh).
// ---------------------------------------------------------------------
use qlsv

db.sv.drop()

db.sv.insertMany([
  {
    Masv: "sv001",
    Hoten: "Trần Thị Lan",
    Ngaysinh: ISODate("2001-05-10"),
    Phai: "Nữ",
    Tuoi: 25,
    Email: ["lan.tran@stu.edu.vn", "tranlan@student.edu.vn"],
    Diachi: "TPHCM",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Anh", "Tiếng Nhật"],
    Lop: { Malop: "l02", Tenlop: "09DHTH" },
    Monhoc: [
      { Mamh: "m001", Tenmh: "Cơ sở dữ liệu", Sotc: 3, Diem: 8 },
      { Mamh: "m002", Tenmh: "Toán cao cấp", Sotc: 2, Diem: 9 }
    ]
  },
  {
    Masv: "sv002",
    Hoten: "Trần Minh",
    Ngaysinh: ISODate("2002-03-14"),
    Phai: "Nam",
    Tuoi: 24,
    Email: ["minh.tran@stu.edu.vn"],
    Diachi: "Hà Nội",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Anh", "Tiếng Pháp"],
    Lop: { Malop: "l01", Tenlop: "08DHTH" },
    Monhoc: [
      { Mamh: "m001", Tenmh: "Cơ sở dữ liệu", Sotc: 3, Diem: 7 },
      { Mamh: "m003", Tenmh: "Công nghệ phần mềm", Sotc: 3, Diem: 8 }
    ]
  },
  {
    Masv: "sv003",
    Hoten: "Phạm Tuấn",
    Ngaysinh: ISODate("2000-11-02"),
    Phai: "Nam",
    Tuoi: 26,
    Email: ["tuan.pham@stu.edu.vn"],
    Diachi: "Đà Nẵng",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Anh", "Tiếng Nhật"],
    Lop: { Malop: "l02", Tenlop: "09DHTH" },
    Monhoc: [
      { Mamh: "m002", Tenmh: "Toán cao cấp", Sotc: 2, Diem: 9 },
      { Mamh: "m004", Tenmh: "Mạng máy tính", Sotc: 3, Diem: 6.5 }
    ]
  },
  {
    Masv: "sv004",
    Hoten: "Trần Minh Nghĩa",
    Ngaysinh: ISODate("2003-04-14"),
    Phai: "Nam",
    Tuoi: 23,
    Email: ["nghia.tran@stu.edu.vn"],
    Diachi: "TPHCM",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Nhật", "Tiếng Pháp"],
    Lop: { Malop: "l01", Tenlop: "08DHTH" },
    Monhoc: [
      { Mamh: "m001", Tenmh: "Cơ sở dữ liệu", Sotc: 3, Diem: 7.5 },
      { Mamh: "m002", Tenmh: "Toán cao cấp", Sotc: 2, Diem: 9 },
      { Mamh: "m003", Tenmh: "Công nghệ phần mềm", Sotc: 3, Diem: 8.5 }
    ]
  },
  {
    Masv: "sv005",
    Hoten: "Nguyễn Thị Hồng",
    Ngaysinh: ISODate("2004-07-21"),
    Phai: "Nữ",
    Tuoi: 22,
    Email: ["hong.nguyen@stu.edu.vn"],
    Diachi: "Cần Thơ",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Anh", "Tiếng Hàn"],
    Lop: { Malop: "l03", Tenlop: "10DHTH" },
    Monhoc: [
      { Mamh: "m001", Tenmh: "Cơ sở dữ liệu", Sotc: 3, Diem: 9 }
    ]
  },
  {
    Masv: "sv006",
    Hoten: "Lê Văn Nam",
    Ngaysinh: ISODate("2005-01-30"),
    Phai: "Nam",
    Tuoi: 21,
    Email: ["nam.le@stu.edu.vn"],
    Diachi: "TPHCM",
    Quoctich: "Việt Nam",
    Ngoaingu: ["Tiếng Pháp", "Tiếng Anh"],
    Lop: { Malop: "l02", Tenlop: "09DHTH" },
    Monhoc: [
      { Mamh: "m003", Tenmh: "Công nghệ phần mềm", Sotc: 3, Diem: 7 },
      { Mamh: "m004", Tenmh: "Mạng máy tính", Sotc: 3, Diem: 6 }
    ]
  }
])

db.sv.find()


// =====================================================================
// PHAN B - BAI 7 (collection hoadon, db qlbanhang)
// Nho chay: use qlbanhang
// =====================================================================

// 1/ Cho biet ma khach hang va so luong hoa don cua tung khach hang
db.hoadon.aggregate([
  { $group: { _id: "$KhachHang.MaKH", SoLuongHoaDon: { $sum: 1 } } }
]);

// 2/ Cho biet ma khach hang, ten khach hang va so luong hoa don cua tung khach hang
db.hoadon.aggregate([
  { $group: { _id: { MaKH: "$KhachHang.MaKH", TenKH: "$KhachHang.TenKH" }, SoLuongHoaDon: { $sum: 1 } } }
]);

// 3/ Liet ke ma hoa don, ngay lap va so luong mat hang co trong hoa don tuong ung
db.hoadon.aggregate([
  { $project: { _id: 0, MaHD: 1, NgayLap: 1, SoLuongMatHang: { $size: "$SanPhamBan" } } }
]);

// 4/ Hien thi ngay lap va so luong hoa don duoc lap tuong ung cua khach hang Tran Minh Tuan
db.hoadon.aggregate([
  { $match: { "KhachHang.TenKH": "Trần Minh Tuấn" } },
  { $group: { _id: "$NgayLap", SoLuongHoaDon: { $sum: 1 } } },
  { $sort: { _id: 1 } }
]);

// 5/ Hien thi ma va ten nhung khach hang co dia chi o TPHCM
db.hoadon.aggregate([
  { $match: { "KhachHang.DiaChi": "TPHCM" } },
  { $group: { _id: { MaKH: "$KhachHang.MaKH", TenKH: "$KhachHang.TenKH" } } }
]);

// 6/ Hien thi thong tin nhung hoa don duoc lap tu ngay 12/03/2021 den 20/03/2021
db.hoadon.aggregate([
  { $match: { NgayLap: { $gte: ISODate("2021-03-12"), $lte: ISODate("2021-03-20") } } }
]);

// 7/ Hien thi ma hoa don, ngay lap cua khach hang ten Tran Minh Tuan, sap xep tang dan theo ngay lap
db.hoadon.aggregate([
  { $match: { "KhachHang.TenKH": "Trần Minh Tuấn" } },
  { $project: { _id: 0, MaHD: 1, NgayLap: 1 } },
  { $sort: { NgayLap: 1 } }
]);

// 8/ Liet ke ma va ten nhung khach hang co tren 2 hoa don
db.hoadon.aggregate([
  { $group: { _id: { MaKH: "$KhachHang.MaKH", TenKH: "$KhachHang.TenKH" }, SoLuongHoaDon: { $sum: 1 } } },
  { $match: { SoLuongHoaDon: { $gt: 2 } } }
]);

// 9/ Cho biet ma san pham va gia ban trung binh cua tung san pham (dung $unwind)
db.hoadon.aggregate([
  { $unwind: "$SanPhamBan" },
  { $group: { _id: "$SanPhamBan.MaSP", GiaBanTrungBinh: { $avg: "$SanPhamBan.GiaBan" } } }
]);

// 10/ Hien thi ma KH, ten KH va danh sach cac ma hoa don cua khach hang (dung $addToSet)
db.hoadon.aggregate([
  { $group: { _id: { MaKH: "$KhachHang.MaKH", TenKH: "$KhachHang.TenKH" }, DanhSachHD: { $addToSet: "$MaHD" } } }
]);

// 11/ Hien thi ngay lap va danh sach cac ma hoa don cua tung ngay lap tuong ung
db.hoadon.aggregate([
  { $group: { _id: "$NgayLap", DanhSachHD: { $push: "$MaHD" } } },
  { $sort: { _id: 1 } }
]);

// 12/ Hien thi ma san pham, ten san pham va tong so luong ban ra tuong ung
db.hoadon.aggregate([
  { $unwind: "$SanPhamBan" },
  { $group: { _id: { MaSP: "$SanPhamBan.MaSP", TenSP: "$SanPhamBan.TenSP" }, TongSoLuong: { $sum: "$SanPhamBan.SoLuong" } } }
]);

// 13/ Liet ke ma hoa don, ten khach hang va tri gia hoa don = sum(so luong * gia ban)
db.hoadon.aggregate([
  { $unwind: "$SanPhamBan" },
  { $group: { _id: { MaHD: "$MaHD", TenKH: "$KhachHang.TenKH" }, TriGia: { $sum: { $multiply: ["$SanPhamBan.SoLuong", "$SanPhamBan.GiaBan"] } } } }
]);

// 14/ Liet ke ma nhung hoa don duoc lap vao thang 7 (dung $month)
db.hoadon.aggregate([
  { $project: { _id: 0, MaHD: 1, Thang: { $month: "$NgayLap" } } },
  { $match: { Thang: 7 } }
]);

// 15/ Liet ke ma nhung hoa don duoc lap vao nam 2020 (dung $year)
db.hoadon.aggregate([
  { $project: { _id: 0, MaHD: 1, Nam: { $year: "$NgayLap" } } },
  { $match: { Nam: 2020 } }
]);

// 16/ Liet ke ma nhung hoa don duoc lap vao thang 7 nam 2020
db.hoadon.aggregate([
  { $project: { _id: 0, MaHD: 1, Thang: { $month: "$NgayLap" }, Nam: { $year: "$NgayLap" } } },
  { $match: { Thang: 7, Nam: 2020 } }
]);


// =====================================================================
// PHAN C - BAI 8 (collection sv, db qlsv)
// Nho chay: use qlsv
// =====================================================================

// 1/ Hien thi ma sinh vien, ho ten va nam sinh cua sinh vien
db.sv.aggregate([
  { $project: { _id: 0, Masv: 1, Hoten: 1, NamSinh: { $year: "$Ngaysinh" } } }
]);

// 2/ Hien thi ma sinh vien, ten lop va tuoi (tuoi tinh tu ngay sinh, dung $subtract)
db.sv.aggregate([
  { $project: { _id: 0, Masv: 1, Tenlop: "$Lop.Tenlop", Tuoi: { $subtract: [{ $year: new Date() }, { $year: "$Ngaysinh" }] } } }
]);

// 3/ Cho biet ma mon hoc, ten mon hoc va so sinh vien hoc tuong ung, sap xep tang dan theo ma mon hoc
db.sv.aggregate([
  { $unwind: "$Monhoc" },
  { $group: { _id: { Mamh: "$Monhoc.Mamh", Tenmh: "$Monhoc.Tenmh" }, SoSinhVien: { $sum: 1 } } },
  { $sort: { "_id.Mamh": 1 } }
]);

// 4/ Liet ke ma lop, ten lop va danh sach ma sinh vien dua vao mang tuong ung
db.sv.aggregate([
  { $group: { _id: { Malop: "$Lop.Malop", Tenlop: "$Lop.Tenlop" }, DanhSachSV: { $push: "$Masv" } } }
]);

// 5/ Liet ke ma mon hoc, ten mon hoc va danh sach sinh vien dua vao mang tuong ung
db.sv.aggregate([
  { $unwind: "$Monhoc" },
  { $group: { _id: { Mamh: "$Monhoc.Mamh", Tenmh: "$Monhoc.Tenmh" }, DanhSachSV: { $addToSet: "$Hoten" } } }
]);

// 6/ Hien thi ma va ten nhung mon hoc co so luong sinh vien >= 2
db.sv.aggregate([
  { $unwind: "$Monhoc" },
  { $group: { _id: { Mamh: "$Monhoc.Mamh", Tenmh: "$Monhoc.Tenmh" }, SoSinhVien: { $sum: 1 } } },
  { $match: { SoSinhVien: { $gte: 2 } } }
]);
