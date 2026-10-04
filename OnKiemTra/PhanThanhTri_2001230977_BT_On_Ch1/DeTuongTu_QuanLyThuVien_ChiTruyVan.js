// DE TUONG TU: QUAN LY THU VIEN
// Huong dan: Chay phan khoi tao va insert du lieu truoc.
// Sinh vien tu viet lenh truy van cho cac yeu cau o phia duoi.

// Câu 1. Tao co so du lieu, collection va them du lieu

use QuanLyThuVien;

db.createCollection("sach");
db.createCollection("phieumuon");

// Tao unique index cho sach.maSach va phieumuon.maPhieu
db.sach.createIndex({ maSach: 1 }, { unique: true });
db.phieumuon.createIndex({ maPhieu: 1 }, { unique: true });

// Du lieu collection sach
db.sach.insertMany([
    {
        maSach: "S001",
        tenSach: "Lap trinh Java co ban",
        theLoai: "Lap trinh",
        namXuatBan: 2023,
        giaSach: 185000,
        soLuongTon: 8,
        tacGia: { maTG: "TG01", tenTG: "Nguyen Van Minh", quocGia: "Viet Nam" },
        tuKhoa: ["Java", "OOP", "lap trinh co ban"]
    },
    {
        maSach: "S002",
        tenSach: "Co so du lieu MongoDB",
        theLoai: "Co so du lieu",
        namXuatBan: 2024,
        giaSach: 240000,
        soLuongTon: 12,
        tacGia: { maTG: "TG02", tenTG: "Tran Thi Hoa", quocGia: "Viet Nam" },
        tuKhoa: ["MongoDB", "NoSQL", "aggregation"]
    },
    {
        maSach: "S003",
        tenSach: "Clean Code",
        theLoai: "Ky thuat phan mem",
        namXuatBan: 2022,
        giaSach: 320000,
        soLuongTon: 5,
        tacGia: { maTG: "TG03", tenTG: "Robert C. Martin", quocGia: "My" },
        tuKhoa: ["clean code", "refactoring", "software"]
    },
    {
        maSach: "S004",
        tenSach: "Lap trinh Python ung dung",
        theLoai: "Lap trinh",
        namXuatBan: 2024,
        giaSach: 210000,
        soLuongTon: 15,
        tacGia: { maTG: "TG04", tenTG: "Le Quang Huy", quocGia: "Viet Nam" },
        tuKhoa: ["Python", "ung dung", "lap trinh"]
    },
    {
        maSach: "S005",
        tenSach: "Kien truc may tinh",
        theLoai: "Cong nghe thong tin",
        namXuatBan: 2021,
        giaSach: 175000,
        soLuongTon: 3,
        tacGia: { maTG: "TG05", tenTG: "Andrew Tanenbaum", quocGia: "My" },
        tuKhoa: ["CPU", "bo nho", "phan cung"]
    }
]);

// Du lieu collection phieumuon
db.phieumuon.insertMany([
    {
        maPhieu: "PM001",
        ngayMuon: ISODate("2026-04-01"),
        ngayHenTra: ISODate("2026-04-15"),
        trangThai: "Da tra",
        docGia: { maDG: "DG01", hoTen: "Pham Thanh An", lop: "CNTT01", thanhPho: "TPHCM" },
        chiTiet: [
            { maSach: "S001", tenSach: "Lap trinh Java co ban", soLuong: 1, soNgayMuon: 14, tienPhat: 0 },
            { maSach: "S002", tenSach: "Co so du lieu MongoDB", soLuong: 1, soNgayMuon: 14, tienPhat: 0 }
        ],
        tongSoSach: 2,
        tongTienPhat: 0
    },
    {
        maPhieu: "PM002",
        ngayMuon: ISODate("2026-04-03"),
        ngayHenTra: ISODate("2026-04-17"),
        trangThai: "Dang muon",
        docGia: { maDG: "DG02", hoTen: "Nguyen Thi Mai", lop: "QTKD02", thanhPho: "Ha Noi" },
        chiTiet: [
            { maSach: "S003", tenSach: "Clean Code", soLuong: 1, soNgayMuon: 14, tienPhat: 0 },
            { maSach: "S004", tenSach: "Lap trinh Python ung dung", soLuong: 1, soNgayMuon: 14, tienPhat: 0 }
        ],
        tongSoSach: 2,
        tongTienPhat: 0
    },
    {
        maPhieu: "PM003",
        ngayMuon: ISODate("2026-04-05"),
        ngayHenTra: ISODate("2026-04-12"),
        trangThai: "Qua han",
        docGia: { maDG: "DG01", hoTen: "Pham Thanh An", lop: "CNTT01", thanhPho: "TPHCM" },
        chiTiet: [
            { maSach: "S002", tenSach: "Co so du lieu MongoDB", soLuong: 1, soNgayMuon: 21, tienPhat: 30000 },
            { maSach: "S005", tenSach: "Kien truc may tinh", soLuong: 1, soNgayMuon: 21, tienPhat: 45000 }
        ],
        tongSoSach: 2,
        tongTienPhat: 75000
    },
    {
        maPhieu: "PM004",
        ngayMuon: ISODate("2026-04-08"),
        ngayHenTra: ISODate("2026-04-22"),
        trangThai: "Dang muon",
        docGia: { maDG: "DG03", hoTen: "Le Minh Khang", lop: "CNTT02", thanhPho: "Da Nang" },
        chiTiet: [
            { maSach: "S001", tenSach: "Lap trinh Java co ban", soLuong: 1, soNgayMuon: 14, tienPhat: 0 },
            { maSach: "S004", tenSach: "Lap trinh Python ung dung", soLuong: 1, soNgayMuon: 14, tienPhat: 0 },
            { maSach: "S005", tenSach: "Kien truc may tinh", soLuong: 1, soNgayMuon: 14, tienPhat: 0 }
        ],
        tongSoSach: 3,
        tongTienPhat: 0
    }
]);

// Câu 2. Truy van du lieu co ban

// 2a. Liet ke sach co soLuongTon lon hon 7.
// Chi hien thi maSach, tenSach, theLoai, soLuongTon; khong hien thi _id.
// Sap xep soLuongTon giam dan.
db.sach.find(
    {'soLuongTon': {$gt: 7}},
    {maSach : 1, tenSach: 1, theLoai: 1, soLuongTon: 1, _id: 0}
).sort({soLuongTon: -1})
// 2b. Liet ke sach cua tac gia Viet Nam va co namXuatBan tu nam 2023 tro di.
// Chi hien thi maSach, tenSach, namXuatBan va tacGia.
db.sach.find(
    {'tacGia.quocGia': 'Viet Nam', namXuatBan : {$gte: 2023}},
    {maSach : 1, tenSach: 1, namXuatBan: 1, tacGia:1, _id: 0}
)
// 2c. Liet ke cac phieu muon cua doc gia co maDG la DG01.
// Chi hien thi maPhieu, ngayMuon, trangThai, tongSoSach va tongTienPhat.
db.phieumuon.find(
    {'docGia.maDG' : 'DG01'},
    {maPhieu:1,ngayMuon:1,trangThai:1,tongSoSach:1,tongTienPhat:1}
)
// 2d. Liet ke phieu muon tu ngay 01/04/2026 den 08/04/2026 co trangThai khac "Da tra".
db.phieumuon.find(
    {ngayMuon: {$gte: ISODate("2026-04-01"), $lte: ISODate("2026-04-08")}},
    {trangThai: {$ne: 'Da tra'}}
)
// 2e. Tim cac sach co tuKhoa chua tu "lap trinh".
// Chi hien thi maSach, tenSach, tuKhoa.
db.sach.find(
    {$unwind: tuKhoa},
    {tuKhoa: "Lap trinh"},
    {maSach:1, tenSach:1, tuKhoa:1, _id: 0}
)
// Câu 3. Truy van nang cao bang Aggregation Framework

// 3a. Thong ke theo doc gia: hien thi maDG, hoTen, soLuongPhieuMuon,
// tongSoSachMuon va tongTienPhat.
db.phieumuon.aggregate([
    {$group: 'docGia'},
    {$project: {maDG:1, hoTen:1, soLuongPhieuMuon:1, tongSoSachMuon:1, tongTienPhat:1}}
])
// 3b. Thong ke theo sach: hien thi maSach, tenSach, tongSoLanMuon,
// tongTienPhatLienQuan va soPhieuCoMuon.

// 3c. Thong ke theo the loai sach: hien thi theLoai, tongSoSachMuon,
// soPhieuMuon va danhSachMaPhieu.
// Goi y: dung $unwind, $lookup voi collection sach va $group.

// 3d. Tim doc gia co tong tien phat lon hon 0.
// Hien thi maDG, hoTen va tongTienPhat.

// Câu 4. Them, cap nhat va xoa du lieu

// 4a. Them sach moi S006 voi thong tin:
// tenSach: "He dieu hanh", theLoai: "Cong nghe thong tin", namXuatBan: 2023,
// giaSach: 195000, soLuongTon: 7,
// tacGia: { maTG: "TG06", tenTG: "Silberschatz", quocGia: "My" },
// tuKhoa: ["he dieu hanh", "Linux", "Windows"].

// 4b. Cap nhat giaSach cua S002 thanh 260000.

// 4c. Tang soLuongTon them 5 cho tat ca sach co theLoai la "Lap trinh".

// 4d. Cap nhat thanhPho thanh "Binh Duong" cho doc gia DG01 trong tat ca phieu muon.

// 4e. Xoa tat ca phieu muon co trangThai la "Da tra".
