// =====================================================================================
// ĐÁP ÁN ĐỀ TƯƠNG TỰ: QUẢN LÝ THƯ VIỆN — Câu 2, 3, 4
// Đã chạy thử trên mongo:7 (Docker) với đúng dữ liệu Câu 1 trong DeTuongTu_QuanLyThuVien_ChiTruyVan.js.
// Chạy Câu 1 của file đề trước, rồi chạy theo thứ tự Câu 2 → 3 → 4 (Câu 4 làm thay đổi dữ liệu).
// Dòng "→" là kết quả mong đợi.
// =====================================================================================

use QuanLyThuVien;

// ------------------------------------- Câu 2 -------------------------------------

// 2a. → S004 (15), S002 (12), S001 (8)
db.sach.find(
    { soLuongTon: { $gt: 7 } },
    { maSach: 1, tenSach: 1, theLoai: 1, soLuongTon: 1, _id: 0 }
).sort({ soLuongTon: -1 });

// 2b. → S001, S002, S004   (tacGia.quocGia = "Viet Nam" và năm xuất bản >= 2023)
db.sach.find(
    { "tacGia.quocGia": "Viet Nam", namXuatBan: { $gte: 2023 } },
    { maSach: 1, tenSach: 1, namXuatBan: 1, tacGia: 1, _id: 0 }
);

// 2c. → PM001, PM003   (thêm _id: 0 vì đề chỉ yêu cầu 5 trường)
db.phieumuon.find(
    { "docGia.maDG": "DG01" },
    { maPhieu: 1, ngayMuon: 1, trangThai: 1, tongSoSach: 1, tongTienPhat: 1, _id: 0 }
);

// 2d. → PM002, PM003, PM004
//     "khác Da tra" là điều kiện LỌC nên $ne nằm ở tham số 1 (filter), không phải tham số 2 (projection).
db.phieumuon.find({
    ngayMuon: { $gte: ISODate("2026-04-01"), $lte: ISODate("2026-04-08") },
    trangThai: { $ne: "Da tra" }
});

// 2e. → S001 (có "lap trinh co ban"), S004 (có "lap trinh")
//     "chứa từ" = tìm gần đúng → dùng regex (không đặt trong dấu nháy). /i = không phân biệt hoa thường.
//     Regex trên field kiểu mảng chuỗi: khớp nếu BẤT KỲ phần tử nào khớp. Không cần $unwind.
db.sach.find(
    { tuKhoa: /lap trinh/i },
    { maSach: 1, tenSach: 1, tuKhoa: 1, _id: 0 }
);


// ------------------------------------- Câu 3 -------------------------------------

// 3a. Thống kê theo độc giả.
//     → DG01: 2 phiếu, 4 sách, phạt 75000 | DG02: 1, 2, 0 | DG03: 1, 3, 0
//     $group: _id là khóa gom nhóm (có thể là object nhiều trường); $sum: 1 = đếm; $sum: "$trường" = cộng.
db.phieumuon.aggregate([
    {
        $group: {
            _id: { maDG: "$docGia.maDG", hoTen: "$docGia.hoTen" },
            soLuongPhieuMuon: { $sum: 1 },
            tongSoSachMuon: { $sum: "$tongSoSach" },
            tongTienPhat: { $sum: "$tongTienPhat" }
        }
    },
    {
        $project: {
            _id: 0, maDG: "$_id.maDG", hoTen: "$_id.hoTen",
            soLuongPhieuMuon: 1, tongSoSachMuon: 1, tongTienPhat: 1
        }
    },
    { $sort: { maDG: 1 } }
]);

// 3b. Thống kê theo sách. Mỗi phiếu có mảng chiTiet → $unwind tách mỗi sách thành 1 dòng rồi mới gom theo sách.
//     → S001: 2 lượt, phạt 0, 2 phiếu | S002: 2, 30000, 2 | S003: 1, 0, 1 | S004: 2, 0, 2 | S005: 2, 45000, 2
db.phieumuon.aggregate([
    { $unwind: "$chiTiet" },
    {
        $group: {
            _id: { maSach: "$chiTiet.maSach", tenSach: "$chiTiet.tenSach" },
            tongSoLanMuon: { $sum: "$chiTiet.soLuong" },
            tongTienPhatLienQuan: { $sum: "$chiTiet.tienPhat" },
            dsMaPhieu: { $addToSet: "$maPhieu" }          // $addToSet: gom vào mảng, KHÔNG trùng
        }
    },
    {
        $project: {
            _id: 0, maSach: "$_id.maSach", tenSach: "$_id.tenSach",
            tongSoLanMuon: 1, tongTienPhatLienQuan: 1,
            soPhieuCoMuon: { $size: "$dsMaPhieu" }          // $size dùng trong $project, không dùng trong $group
        }
    },
    { $sort: { maSach: 1 } }
]);

// 3c. Thống kê theo thể loại. Trong phiếu chỉ có maSach, KHÔNG có theLoai → phải $lookup sang collection sach.
//     → Lap trinh: 4 sách, 3 phiếu [PM001, PM002, PM004] | Co so du lieu: 2, 2 [PM001, PM003]
//       Ky thuat phan mem: 1, 1 [PM002] | Cong nghe thong tin: 2, 2 [PM003, PM004]
db.phieumuon.aggregate([
    { $unwind: "$chiTiet" },
    { $lookup: { from: "sach", localField: "chiTiet.maSach", foreignField: "maSach", as: "sachInfo" } },
    { $unwind: "$sachInfo" },
    {
        $group: {
            _id: "$sachInfo.theLoai",
            tongSoSachMuon: { $sum: "$chiTiet.soLuong" },
            danhSachMaPhieu: { $addToSet: "$maPhieu" }
        }
    },
    {
        $project: {
            _id: 0, theLoai: "$_id", tongSoSachMuon: 1,
            soPhieuMuon: { $size: "$danhSachMaPhieu" },
            danhSachMaPhieu: 1
        }
    },
    { $sort: { theLoai: 1 } }
]);
//     BẪY: soPhieuMuon KHÔNG được tính bằng $sum: 1. Thể loại "Lap trinh": PM004 mượn cả S001 lẫn S004 (cùng thể loại)
//     → $sum: 1 đếm ra 4 phiếu (sai), đúng là 3. Vì vậy gom mã phiếu bằng $addToSet rồi lấy $size.

// 3d. Độc giả có tổng tiền phạt > 0.  → DG01 (75000)
//     Điều kiện trên kết quả đã gom nhóm → $match phải đặt SAU $group (giống ví dụ 5 trong hướng dẫn).
db.phieumuon.aggregate([
    { $group: { _id: { maDG: "$docGia.maDG", hoTen: "$docGia.hoTen" }, tongTienPhat: { $sum: "$tongTienPhat" } } },
    { $match: { tongTienPhat: { $gt: 0 } } },
    { $project: { _id: 0, maDG: "$_id.maDG", hoTen: "$_id.hoTen", tongTienPhat: 1 } }
]);


// ------------------------------------- Câu 4 (thay đổi dữ liệu) -------------------------------------

// 4a. Thêm sách mới S006 (maSach là unique index nên không được trùng)
db.sach.insertOne({
    maSach: "S006",
    tenSach: "He dieu hanh",
    theLoai: "Cong nghe thong tin",
    namXuatBan: 2023,
    giaSach: 195000,
    soLuongTon: 7,
    tacGia: { maTG: "TG06", tenTG: "Silberschatz", quocGia: "My" },
    tuKhoa: ["he dieu hanh", "Linux", "Windows"]
});

// 4b. Cập nhật giá S002 thành 260000. $set gán giá trị mới cho 1 field.
db.sach.updateOne({ maSach: "S002" }, { $set: { giaSach: 260000 } });

// 4c. Tăng soLuongTon thêm 5 cho MỌI sách thể loại "Lap trinh" → S001: 8 → 13, S004: 15 → 20
//     Nhiều document → updateMany (hướng dẫn dùng update kèm {multi: true}, tương đương). $inc = cộng thêm.
db.sach.updateMany({ theLoai: "Lap trinh" }, { $inc: { soLuongTon: 5 } });

// 4d. Đổi thành phố của độc giả DG01 trong TẤT CẢ phiếu mượn → PM001, PM003 (updateMany).
//     Field trong document nhúng: dùng "docGia.thanhPho".
db.phieumuon.updateMany({ "docGia.maDG": "DG01" }, { $set: { "docGia.thanhPho": "Binh Duong" } });

// 4e. Xóa mọi phiếu mượn trạng thái "Da tra" → xóa PM001 (deletedCount: 1).
db.phieumuon.deleteMany({ trangThai: "Da tra" });

// Kiểm tra sau Câu 4:
// db.sach.find({}, { maSach: 1, soLuongTon: 1, giaSach: 1, _id: 0 });
//   → S001 13 | S002 (giá 260000) | S004 20 | S006 7 ...
// db.phieumuon.find({}, { maPhieu: 1, "docGia.thanhPho": 1, _id: 0 });
//   → PM002 (Ha Noi), PM003 (Binh Duong), PM004 (Da Nang)
