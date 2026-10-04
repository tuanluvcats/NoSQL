// =====================================================================================
// ĐÁP ÁN — ĐỀ #2 MONGODB (QuanLyKhoaHoc)  — ĐÃ chạy thử trên mongo:7 (Docker, mongosh): không lỗi cú pháp, kết quả "→" khớp.
// Làm xong đề rồi mới mở file này. Chạy Câu 1 của đề trước.
// =====================================================================================

use QuanLyKhoaHoc;

// ------------------------------- Câu 2 -------------------------------
// 2a. → KH04 (3500000), KH02 (3200000)
db.khoahoc.find(
    { hocPhi: { $gt: 3000000 } },
    { maKH: 1, tenKH: 1, hocPhi: 1, _id: 0 }
).sort({ hocPhi: -1 });

// 2b. → KH02, KH04   (KH01 khai giảng 05/10 nên loại; KH03/KH05 không phải giảng viên Việt Nam)
db.khoahoc.find(
    { "giangVien.quocGia": "Viet Nam", ngayKhaiGiang: { $gte: ISODate("2026-10-10") } },
    { maKH: 1, tenKH: 1, ngayKhaiGiang: 1, giangVien: 1, _id: 0 }
);

// 2c. → DK001, DK003
db.dangky.find(
    { "hocVien.maHV": "HV01" },
    { maDK: 1, ngayDangKy: 1, trangThai: 1, tongTien: 1, _id: 0 }
);

// 2d. → DK001, DK002, DK003   ($ne phải nằm trong FILTER, không phải projection)
db.dangky.find(
    { ngayDangKy: { $gte: ISODate("2026-09-01"), $lte: ISODate("2026-09-15") }, trangThai: { $ne: "Da huy" } },
    { maDK: 1, ngayDangKy: 1, trangThai: 1, _id: 0 }
);

// 2e. → KH01, KH04   (regex trên mảng chuỗi: khớp nếu BẤT KỲ phần tử nào khớp; /i = bỏ qua hoa thường)
db.khoahoc.find(
    { tags: /lap trinh/i },
    { maKH: 1, tenKH: 1, tags: 1, _id: 0 }
);

// 2f. → KH01, KH04
db.khoahoc.find({ tenKH: /^Lap trinh/ }, { maKH: 1, tenKH: 1, _id: 0 });

// 2g. → DK001, DK003, DK004, DK005
db.dangky.find(
    { "hocVien.thanhPho": { $in: ["TPHCM", "Da Nang"] } },
    { maDK: 1, "hocVien.hoTen": 1, "hocVien.thanhPho": 1, _id: 0 }
);

// 2h. → DK001, DK005   ($elemMatch: cả 2 điều kiện trên CÙNG một phần tử. DK004 có KH01 nhưng giamGia = 0 nên loại)
db.dangky.find(
    { chiTiet: { $elemMatch: { maKH: "KH01", giamGia: { $gt: 0 } } } },
    { maDK: 1, _id: 0 }
);
// BẪY: viết { "chiTiet.maKH": "KH01", "chiTiet.giamGia": { $gt: 0 } } sẽ KHỚP CẢ DK004 (KH01 ở phần tử này, giamGia 0.2 ở phần tử KH04).

// 2i. → DK001, DK002, DK004
db.dangky.find({ chiTiet: { $size: 2 } }, { maDK: 1, _id: 0 });

// 2j. → KH02, KH03
db.khoahoc.find({}, { maKH: 1, tenKH: 1, _id: 0 }).sort({ maKH: 1 }).skip(1).limit(2);

// 2k. → 3
db.dangky.countDocuments({ trangThai: "Da thanh toan" });

// 2l. → ["Da Nang", "Ha Noi", "TPHCM"]
db.dangky.distinct("hocVien.thanhPho");


// ------------------------------- Câu 3 -------------------------------
// 3a. → HV01: 2 đăng ký / 8.950.000 | HV02: 1 / 4.780.000 | HV03: 1 / 5.300.000 | HV04: 1 / 7.330.000
db.dangky.aggregate([
    {
        $group: {
            _id: { maHV: "$hocVien.maHV", hoTen: "$hocVien.hoTen" },
            soLuongDangKy: { $sum: 1 },
            tongTien: { $sum: "$tongTien" }
        }
    },
    { $project: { _id: 0, maHV: "$_id.maHV", hoTen: "$_id.hoTen", soLuongDangKy: 1, tongTien: 1 } },
    { $sort: { maHV: 1 } }
]);

// 3b. → KH01: 3 lượt, 7.000.000, 3 đơn | KH02: 2, 6.080.000, 2 | KH03: 1, 2.800.000, 1 | KH04: 2, 6.300.000, 2 | KH05: 2, 4.180.000, 2
db.dangky.aggregate([
    { $unwind: "$chiTiet" },
    {
        $group: {
            _id: { maKH: "$chiTiet.maKH", tenKH: "$chiTiet.tenKH" },
            soLuotDangKy: { $sum: 1 },
            tongDoanhThu: { $sum: "$chiTiet.thanhTien" },
            dsMaDK: { $addToSet: "$maDK" }
        }
    },
    {
        $project: {
            _id: 0, maKH: "$_id.maKH", tenKH: "$_id.tenKH",
            soLuotDangKy: 1, tongDoanhThu: 1, soDonDangKy: { $size: "$dsMaDK" }   // $size chỉ dùng trong $project, không dùng trong $group
        }
    },
    { $sort: { maKH: 1 } }
]);

// 3c. → Lap trinh: 5 lượt, 13.300.000, 4 đơn (DK001, DK003, DK004, DK005)
//       Co so du lieu: 4 lượt, 10.260.000, 3 đơn (DK001, DK002, DK005)
//       Thiet ke: 1 lượt, 2.800.000, 1 đơn (DK002)
db.dangky.aggregate([
    { $unwind: "$chiTiet" },
    { $lookup: { from: "khoahoc", localField: "chiTiet.maKH", foreignField: "maKH", as: "kh" } },
    { $unwind: "$kh" },
    {
        $group: {
            _id: "$kh.linhVuc",
            tongSoLuot: { $sum: 1 },
            tongDoanhThu: { $sum: "$chiTiet.thanhTien" },
            danhSachMaDK: { $addToSet: "$maDK" }
        }
    },
    { $project: { _id: 0, linhVuc: "$_id", tongSoLuot: 1, tongDoanhThu: 1, soDon: { $size: "$danhSachMaDK" }, danhSachMaDK: 1 } }
]);
// BẪY: soDon = $sum:1 sẽ ĐẾM SAI (DK005 có 2 khóa "Co so du lieu" → tính 2 lần). Phải $addToSet rồi $size.

// 3d. → HV01 (8.950.000), HV04 (7.330.000)
db.dangky.aggregate([
    { $match: { trangThai: { $ne: "Da huy" } } },
    { $group: { _id: { maHV: "$hocVien.maHV", hoTen: "$hocVien.hoTen" }, tongTien: { $sum: "$tongTien" } } },
    { $match: { tongTien: { $gt: 6000000 } } },
    { $project: { _id: 0, maHV: "$_id.maHV", hoTen: "$_id.hoTen", tongTien: 1 } }
]);

// 3e. → 2026/9: 2 đơn, 10.230.000 | 2026/10: 1 đơn, 7.330.000
db.dangky.aggregate([
    { $match: { trangThai: "Da thanh toan" } },
    {
        $group: {
            _id: { nam: { $year: "$ngayDangKy" }, thang: { $month: "$ngayDangKy" } },
            soDon: { $sum: 1 },
            doanhThu: { $sum: "$tongTien" }
        }
    },
    { $project: { _id: 0, nam: "$_id.nam", thang: "$_id.thang", soDon: 1, doanhThu: 1 } },
    { $sort: { nam: 1, thang: 1 } }
]);

// 3f. → DK001, DK002, DK003, DK004
db.dangky.aggregate([
    { $project: { maDK: 1, thang: { $month: "$ngayDangKy" }, nam: { $year: "$ngayDangKy" } } },
    { $match: { thang: 9, nam: 2026 } },
    { $project: { _id: 0, maDK: 1 } }
]);

// 3g. → KH01 (7.000.000), KH04 (6.300.000)
db.dangky.aggregate([
    { $unwind: "$chiTiet" },
    { $group: { _id: { maKH: "$chiTiet.maKH", tenKH: "$chiTiet.tenKH" }, tongDoanhThu: { $sum: "$chiTiet.thanhTien" } } },
    { $sort: { tongDoanhThu: -1 } },
    { $limit: 2 },
    { $project: { _id: 0, maKH: "$_id.maKH", tenKH: "$_id.tenKH", tongDoanhThu: 1 } }
]);

// 3h. → Lap trinh: TB 3.000.000, max 3.500.000, min 2.500.000 | Co so du lieu: TB 2.700.000, 3.200.000, 2.200.000 | Thiet ke: 2.800.000 (cả 3)
db.khoahoc.aggregate([
    {
        $group: {
            _id: "$linhVuc",
            hocPhiTrungBinh: { $avg: "$hocPhi" },
            hocPhiCaoNhat: { $max: "$hocPhi" },
            hocPhiThapNhat: { $min: "$hocPhi" }
        }
    },
    { $project: { _id: 0, linhVuc: "$_id", hocPhiTrungBinh: 1, hocPhiCaoNhat: 1, hocPhiThapNhat: 1 } }
]);

// 3i. → GV01 Nguyen Van Son: 2 khóa [Python, Java] | GV02: 1 | GV03: 1 | GV04: 1
db.khoahoc.aggregate([
    {
        $group: {
            _id: { maGV: "$giangVien.maGV", tenGV: "$giangVien.tenGV" },
            soKhoaHoc: { $sum: 1 },
            danhSachTenKH: { $push: "$tenKH" }
        }
    },
    { $project: { _id: 0, maGV: "$_id.maGV", tenGV: "$_id.tenGV", soKhoaHoc: 1, danhSachTenKH: 1 } }
]);

// 3j. → chỉ HV01 (2 đăng ký)
db.dangky.aggregate([
    { $group: { _id: { maHV: "$hocVien.maHV", hoTen: "$hocVien.hoTen" }, soLuongDangKy: { $sum: 1 } } },
    { $match: { soLuongDangKy: { $gt: 1 } } },
    { $project: { _id: 0, maHV: "$_id.maHV", hoTen: "$_id.hoTen", soLuongDangKy: 1 } }
]);

// 3k. → KH01: 125000, "Thap" | KH02: 133333, "Cao" | KH03: 155556, "Thap" | KH04: 116667, "Cao" | KH05: 137500, "Thap"
db.khoahoc.aggregate([
    {
        $project: {
            _id: 0, maKH: 1,
            tenKHHoa: { $toUpper: "$tenKH" },
            hocPhiMoiBuoi: { $round: [{ $divide: ["$hocPhi", "$soBuoi"] }, 0] },
            mucHocPhi: { $cond: [{ $gte: ["$hocPhi", 3000000] }, "Cao", "Thap"] }
        }
    }
]);

// 3l. → soDangKy (tính cả đơn đã hủy): KH01 3 → còn 27 | KH02 2 → 23 | KH03 1 → 19 | KH04 2 → 28 | KH05 2 → 33
db.khoahoc.aggregate([
    { $lookup: { from: "dangky", localField: "maKH", foreignField: "chiTiet.maKH", as: "dsDangKy" } },
    {
        $project: {
            _id: 0, maKH: 1, tenKH: 1, soLuongToiDa: 1,
            soDangKy: { $size: "$dsDangKy" },
            soChoConLai: { $subtract: ["$soLuongToiDa", { $size: "$dsDangKy" }] }
        }
    }
]);

// 3m. → KH01: 2 (HV01, HV04) | KH02: 2 (HV01, HV04) | KH03: 1 | KH04: 1 (HV01) | KH05: 2 (HV02, HV04)
db.dangky.aggregate([
    { $match: { trangThai: { $ne: "Da huy" } } },
    { $unwind: "$chiTiet" },
    { $group: { _id: { maKH: "$chiTiet.maKH", tenKH: "$chiTiet.tenKH" }, dsHV: { $addToSet: "$hocVien.maHV" } } },
    { $project: { _id: 0, maKH: "$_id.maKH", tenKH: "$_id.tenKH", soHocVien: { $size: "$dsHV" } } },
    { $sort: { maKH: 1 } }
]);

// 3n. → tuổi phụ thuộc năm hiện tại: HV01 = năm nay - 1999, HV02 = - 2001, HV03 = - 1998, HV04 = - 2003
db.dangky.aggregate([
    {
        $group: {
            _id: { maHV: "$hocVien.maHV", hoTen: "$hocVien.hoTen" },
            namSinh: { $first: { $year: "$hocVien.ngaySinh" } }
        }
    },
    {
        $project: {
            _id: 0, maHV: "$_id.maHV", hoTen: "$_id.hoTen",
            tuoi: { $subtract: [{ $year: new Date() }, "$namSinh"] }
        }
    }
]);


// ------------------------------- Câu 4 (thay đổi dữ liệu) -------------------------------
// 4a.
db.khoahoc.insertOne({
    maKH: "KH06", tenKH: "DevOps co ban", linhVuc: "Ha tang", hocPhi: 3000000, soBuoi: 20,
    ngayKhaiGiang: ISODate("2026-12-01"), soLuongToiDa: 25,
    giangVien: { maGV: "GV05", tenGV: "Do Minh Quan", quocGia: "Viet Nam" },
    tags: ["Docker", "CI/CD", "DevOps"]
});

// 4b.
db.khoahoc.updateOne({ maKH: "KH02" }, { $set: { hocPhi: 3000000 } });

// 4c. $inc cộng thêm; $mul nhân. updateMany vì cập nhật NHIỀU document (guide dùng update + {multi:true} — tương đương).
db.khoahoc.updateMany({ linhVuc: "Lap trinh" }, { $inc: { soLuongToiDa: 5 } });
db.khoahoc.updateMany({ linhVuc: "Co so du lieu" }, { $mul: { hocPhi: 0.9 } });

// 4d. Sửa field trong document nhúng: dùng "field.subfield"
db.dangky.updateMany({ "hocVien.maHV": "HV01" }, { $set: { "hocVien.thanhPho": "Binh Duong" } });

// 4e. $push: thêm KHÔNG kiểm tra trùng | $addToSet: có kiểm tra trùng (tag "NoSQL" đã có → không thêm) | $pull: xóa theo giá trị
db.khoahoc.updateOne({ maKH: "KH02" }, { $push: { tags: "big data" } });
db.khoahoc.updateOne({ maKH: "KH02" }, { $addToSet: { tags: "NoSQL" } });    // matchedCount 1, modifiedCount 0
db.khoahoc.updateOne({ maKH: "KH02" }, { $pull: { tags: "aggregation" } });

// 4f. Toán tử vị trí $ = phần tử ĐẦU TIÊN khớp điều kiện trong filter ("chiTiet.maKH": "KH02").
//     tongTien: 5.450.000 - (3.200.000 - 3.040.000) = 5.290.000
db.dangky.updateOne(
    { maDK: "DK001", "chiTiet.maKH": "KH02" },
    { $set: { "chiTiet.$.giamGia": 0.05, "chiTiet.$.thanhTien": 3040000 }, $inc: { tongTien: -160000 } }
);
// Cách theo tài liệu hướng dẫn (dùng chỉ số mảng, KH02 đang ở vị trí 1):
// db.dangky.updateOne({ maDK: "DK001" }, { $set: { "chiTiet.1.giamGia": 0.05, "chiTiet.1.thanhTien": 3040000 } });

// 4g. $pull với điều kiện trên subfield. tongTien mới = 4.780.000 - 1.980.000 = 2.800.000
db.dangky.updateOne(
    { maDK: "DK002" },
    { $pull: { chiTiet: { maKH: "KH05" } }, $inc: { tongTien: -1980000 } }
);

// 4h.
db.dangky.deleteMany({ trangThai: "Da huy" });
db.dangky.deleteOne({ maDK: "DK003" });

// 4i. upsert: không có KH07 thì tạo mới, có rồi thì cập nhật.
db.khoahoc.updateOne(
    { maKH: "KH07" },
    { $set: { tenKH: "Data Science co ban", hocPhi: 4000000 } },
    { upsert: true }
);
db.khoahoc.replaceOne(
    { maKH: "KH07" },
    { maKH: "KH07", tenKH: "Data Science co ban", linhVuc: "Du lieu", hocPhi: 4000000, soBuoi: 28 }
);   // replaceOne thay TOÀN BỘ document (giữ _id) — các field không viết lại sẽ mất. Thay cho db.collection.save() cũ trong tài liệu.

// 4j.
db.khoahoc.updateOne({ maKH: "KH01" }, { $rename: { soLuongToiDa: "siSoToiDa" } });
db.khoahoc.updateOne({ maKH: "KH01" }, { $unset: { soBuoi: "" } });
db.khoahoc.updateOne({ maKH: "KH01" }, { $rename: { siSoToiDa: "soLuongToiDa" }, $set: { soBuoi: 20 } });


// ------------------------------- Câu 5 -------------------------------
// 5a.
db.khoahoc.getIndexes();

// 5b. Trước: stage COLLSCAN (quét cả collection, docsExamined = số document). Sau: IXSCAN, keysExamined = docsExamined = 2 (GV01 có 2 khóa).
db.khoahoc.find({ "giangVien.maGV": "GV01" }).explain("executionStats");
db.khoahoc.createIndex({ "giangVien.maGV": 1 });
db.khoahoc.find({ "giangVien.maGV": "GV01" }).explain("executionStats");
// Dữ liệu mẫu chỉ 5 dòng nên executionTimeMillis gần như bằng nhau; điểm khác nằm ở stage và số document đã quét.

// 5c.
db.khoahoc.createIndex({ linhVuc: 1, hocPhi: -1 }, { name: "idx_linhvuc_hocphi" });
db.khoahoc.dropIndex("idx_linhvuc_hocphi");

// 5d. Trên DỮ LIỆU GỐC sẽ LỖI E11000 duplicate key: HV01 có 2 đăng ký (DK001, DK003) cùng email "anh@mail.com" → không thể tạo unique.
//     (Đã chạy thử: DuplicateKey 11000.) Nếu bạn đã làm Câu 4h (xóa DK003) thì HV01 chỉ còn 1 đăng ký → index tạo được, không lỗi.
//     Muốn thấy lỗi: chạy lại Câu 1 rồi làm Câu 5 TRƯỚC Câu 4.
//     unique = không cho phép 2 document có cùng giá trị; sparse = bỏ qua document không có field đó.
db.dangky.createIndex({ "hocVien.email": 1 }, { unique: true, sparse: true });


// ------------------------------- Câu 6 (chạy trong cmd / PowerShell) -------------------------------
// 6a. mongoexport -d QuanLyKhoaHoc -c khoahoc -o "D:\MONGO\EXPORT\khoahoc.json"
// 6b. mongoexport -d QuanLyKhoaHoc -c dangky --type=csv --fields maDK,ngayDangKy,trangThai,tongTien -o "D:\MONGO\EXPORT\dangky.csv"
// 6c. mongoimport -d QuanLyKhoaHoc -c khoahoc_copy --file "D:\MONGO\EXPORT\khoahoc.json"      // --file KHÔNG viết tắt được
// 6d. mongodump -d QuanLyKhoaHoc -o "D:\MONGO\EXPORT\fulldb"
// 6e. mongorestore -d QuanLyKhoaHoc_restore "D:\MONGO\EXPORT\fulldb\QuanLyKhoaHoc"
// Nếu chạy trong Docker của bạn: docker exec nosql-mongo mongoexport -d QuanLyKhoaHoc -c khoahoc -o /baitap/khoahoc.json


// ------------------------------- Lý thuyết hay hỏi kèm -------------------------------
// Embedded (nhúng) vs Reference (tham chiếu) — mục 1.2 tài liệu:
//  - giangVien nhúng trong khoahoc, hocVien nhúng trong dangky: dữ liệu luôn đọc cùng nhau, 1 truy vấn là đủ, không cần join;
//    đổi lại bị lặp dữ liệu (tenGV lặp ở nhiều khóa → sửa phải updateMany).
//  - Reference (chỉ lưu maKH rồi $lookup): tránh lặp, dễ sửa 1 nơi, nhưng đọc phải $lookup (chậm hơn).
//  - Dấu hiệu chọn: quan hệ 1–ít, đọc cùng nhau → nhúng. Quan hệ nhiều–nhiều, dữ liệu đổi thường xuyên → tham chiếu.
