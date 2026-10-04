// Câu 1. Thiết kế, tạo cơ sở dữ liệu và thêm dữ liệu 

// 1. Tạo database và collection
use QuanLyMuaBanLinhKien;

db.createCollection("linhkien");
db.createCollection("hoadon");

// 2. Tạo unique index cho linhkien.maLK và hoadon.maHD
db.linhkien.createIndex({ maLK: 1 }, { unique: true });
db.hoadon.createIndex({ maHD: 1 }, { unique: true });

// 3. Thêm dữ liệu collection linhkien
db.linhkien.insertMany([
    {
        maLK: "LK01",
        tenLK: "CPU Intel Core i5-13400",
        loai: "CPU",
        donGia: 4500000,
        soLuongTon: 15,
        nhaSanXuat: { maHang: "HSX01", tenHang: "Intel", quocGia: "Mỹ" },
        thongSoKyThuat: [
            { tenThongSo: "Socket", giaTri: "LGA1700" },
            { tenThongSo: "Số nhân", giaTri: "10" },
            { tenThongSo: "Xung nhịp", giaTri: "4.6 GHz" }
        ]
    },
    {
        maLK: "LK02",
        tenLK: "RAM Kingston Fury 16GB",
        loai: "RAM",
        donGia: 1200000,
        soLuongTon: 30,
        nhaSanXuat: { maHang: "HSX02", tenHang: "Kingston", quocGia: "Mỹ" },
        thongSoKyThuat: [
            { tenThongSo: "Dung lượng", giaTri: "16GB" },
            { tenThongSo: "Chuẩn RAM", giaTri: "DDR4" },
            { tenThongSo: "Bus", giaTri: "3200 MHz" }
        ]
    },
    {
        maLK: "LK03",
        tenLK: "SSD Samsung 1TB",
        loai: "Ổ cứng",
        donGia: 2300000,
        soLuongTon: 20,
        nhaSanXuat: { maHang: "HSX03", tenHang: "Samsung", quocGia: "Hàn Quốc" },
        thongSoKyThuat: [
            { tenThongSo: "Dung lượng", giaTri: "1TB" },
            { tenThongSo: "Chuẩn kết nối", giaTri: "NVMe" },
            { tenThongSo: "Tốc độ đọc", giaTri: "3500 MB/s" }
        ]
    }
]);

// 4. Thêm dữ liệu collection hoadon
db.hoadon.insertMany([
    {
        maHD: "HD001",
        ngayLap: ISODate("2026-03-01"),
        trangThai: "Đã thanh toán",
        khachHang: { maKH: "KH01", hoTen: "Nguyễn Văn An", thanhPho: "TPHCM" },
        chiTiet: [
            { maLK: "LK01", tenLK: "CPU Intel Core i5-13400", soLuong: 1, donGia: 4500000, thanhTien: 4500000 },
            { maLK: "LK02", tenLK: "RAM Kingston Fury 16GB", soLuong: 2, donGia: 1200000, thanhTien: 2400000 }
        ],
        tongTien: 6900000
    },
    {
        maHD: "HD002",
        ngayLap: ISODate("2026-03-03"),
        trangThai: "Đã thanh toán",
        khachHang: { maKH: "KH02", hoTen: "Trần Thị Bình", thanhPho: "Hà Nội" },
        chiTiet: [
            { maLK: "LK03", tenLK: "SSD Samsung 1TB", soLuong: 2, donGia: 2300000, thanhTien: 4600000 },
            { maLK: "LK02", tenLK: "RAM Kingston Fury 16GB", soLuong: 1, donGia: 1200000, thanhTien: 1200000 }
        ],
        tongTien: 5800000
    },
    {
        maHD: "HD003",
        ngayLap: ISODate("2026-03-05"),
        trangThai: "Chờ xử lý",
        khachHang: { maKH: "KH01", hoTen: "Nguyễn Văn An", thanhPho: "TPHCM" },
        chiTiet: [
            { maLK: "LK01", tenLK: "CPU Intel Core i5-13400", soLuong: 1, donGia: 4500000, thanhTien: 4500000 },
            { maLK: "LK03", tenLK: "SSD Samsung 1TB", soLuong: 1, donGia: 2300000, thanhTien: 2300000 }
        ],
        tongTien: 6800000
    }
]);

// Câu 2. Truy vấn dữ liệu cơ bản

// 2a. Liệt kê linh kiện có soLuongTon lớn hơn 15
// Chỉ hiển thị maLK, tenLK, soLuongTon; không hiển thị _id.
// Sắp xếp soLuongTon giảm dần.

db.linhkien.find(
    { soLuongTon: { $gt: 15 } },
    { maLK: 1, tenLK: 1, soLuongTon: 1, _id: 0 }
).sort({ soLuongTon: -1 });

// 2b. Liệt kê linh kiện do nhà sản xuất ở quốc gia Mỹ (Chỉ hiển thị maLK, tenLK, donGia và nhaSanXuat.)
db.linhkien.find(
    { "nhaSanXuat.quocGia": "Mỹ" },
    { maLK: 1, tenLK: 1, donGia: 1, nhaSanXuat: 1, _id: 0 }
);

// 2c. Liệt kê các hóa đơn của khách hàng có mã KH01 (Chỉ hiển thị maHD, ngayLap, trangThai, tongTien; không hiển thị _id.)
db.hoadon.find(
    { "khachHang.maKH": "KH01" },
    { maHD: 1, ngayLap: 1, trangThai: 1, tongTien: 1, _id: 0 }
);

// 2d. Liệt kê hóa đơn từ 01/03/2026 đến 03/03/2026 và tongTien > 5.500.000
db.hoadon.find({
    ngayLap: {
        $gte: ISODate("2026-03-01"),
        $lte: ISODate("2026-03-04")
    },
    tongTien: { $gt: 5500000 }
});


// Câu 3. Truy vấn nâng cao bằng Aggregation Framework 

// 3a. Hiển thị maKH, hoTen, soLuongHoaDon, tongTienDaMua và giaTriHoaDonTrungBinh.
db.hoadon.aggregate([
    {
        $group: {
            _id: { maKH: "$khachHang.maKH", hoTen: "$khachHang.hoTen" },
            soLuongHoaDon: { $sum: 1 },
            tongTienDaMua: { $sum: "$tongTien" },
            giaTriHoaDonTrungBinh: { $avg: "$tongTien" }
        }
    },
    {
        $project: {
            _id: 0,
            maKH: "$_id.maKH",
            hoTen: "$_id.hoTen",
            soLuongHoaDon: 1,
            tongTienDaMua: 1,
            giaTriHoaDonTrungBinh: 1
        }
    }
]);

// 3b. Hiển thị maLK, tenLK, tongSoLuongBan, tongDoanhThu và soHoaDonCoBan.
db.hoadon.aggregate([
    { $unwind: "$chiTiet" },
    {
        $group: {
            _id: { maLK: "$chiTiet.maLK", tenLK: "$chiTiet.tenLK" },
            tongSoLuongBan: { $sum: "$chiTiet.soLuong" },
            tongDoanhThu: { $sum: "$chiTiet.thanhTien" },
            danhSachHoaDon: { $addToSet: "$maHD" }
        }
    },
    {
        $project: {
            _id: 0,
            maLK: "$_id.maLK",
            tenLK: "$_id.tenLK",
            tongSoLuongBan: 1,
            tongDoanhThu: 1,
            soHoaDonCoBan: { $size: "$danhSachHoaDon" }
        }
    }
]);

// 3c. Thống  kê theo nhà sản xuất: Hiển thị tenHang, quocGia, tongSoLuongBan, tongDoanhThu và danhSachMaHD.
db.hoadon.aggregate([
    { $unwind: "$chiTiet" },
    {
        $lookup: {
            from: "linhkien",
            localField: "chiTiet.maLK",
            foreignField: "maLK",
            as: "LinhKienInfo"
        }
    },
    { $unwind: "$LinhKienInfo" },
    {
        $group: {
            _id: {
                tenHang: "$LinhKienInfo.nhaSanXuat.tenHang",
                quocGia: "$LinhKienInfo.nhaSanXuat.quocGia"
            },
            tongSoLuongBan: { $sum: "$chiTiet.soLuong" },
            tongDoanhThu: { $sum: "$chiTiet.thanhTien" },
            danhSachMaHD: { $addToSet: "$maHD" }
        }
    },
    {
        $project: {
            _id: 0,
            tenHang: "$_id.tenHang",
            quocGia: "$_id.quocGia",
            tongSoLuongBan: 1,
            tongDoanhThu: 1,
            danhSachMaHD: 1
        }
    }
]);

// Câu 4. Thêm, xóa và cập nhật dữ liệu

// 4a. Thêm linh kiện mới: Dùng insertOne() thêm LK04 – Mainboard Asus B760; loại Mainboard; đơn giá 3.200.000; tồn kho 10; Nhà sản xuất: HSX04 – Asus – Đài Loan; 
// Thông số: Socket LGA1700; Chuẩn RAM DDR4; Kích thước Micro-ATX.
db.linhkien.insertOne({
    maLK: "LK04",
    tenLK: "Mainboard Asus B760",
    loai: "Mainboard",
    donGia: 3200000,
    soLuongTon: 10,
    nhaSanXuat: { maHang: "HSX04", tenHang: "Asus", quocGia: "Đài Loan" },
    thongSoKyThuat: [
        { tenThongSo: "Socket", giaTri: "LGA1700" },
        { tenThongSo: "Chuẩn RAM", giaTri: "DDR4" },
        { tenThongSo: "Kích thước", giaTri: "Micro-ATX" }
    ]
});

// 4b. Cập nhật donGia của LK03 thành 2.500.000.
db.linhkien.updateOne(
    { maLK: "LK03" },
    { $set: { donGia: 2500000 } }
);

// 4c. Cập nhật thanhPho thành Bình Dương cho tất cả hóa đơn của khách hàng KH01.
db.hoadon.updateMany(
    { "khachHang.maKH": "KH01" },
    { $set: { "khachHang.thanhPho": "Bình Dương" } }
);

// 4e. Xóa tất cả hóa đơn có trạng thái Chờ xử lý.
db.hoadon.deleteMany({ trangThai: "Chờ xử lý" });