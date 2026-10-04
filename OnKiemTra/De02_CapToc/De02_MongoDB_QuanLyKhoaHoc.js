// =====================================================================================
// ĐỀ TƯƠNG TỰ #2 (CẤP TỐC) — MONGODB — 6 điểm / 10
// Chủ đề: QUẢN LÝ TRUNG TÂM ĐÀO TẠO (khóa học – đăng ký)
//
// Cách làm:  1) Chạy khối CÂU 1 trước (tạo DB + dữ liệu).
//            2) Tự viết lệnh cho Câu 2 → Câu 6 ngay dưới mỗi yêu cầu.
//            3) Làm xong mới mở file DapAn02_MongoDB.js để đối chiếu (có kết quả mong đợi).
// Lưu ý:     - `use` chạy được trong mongosh / NoSQLBooster. Nếu chạy bằng load() thì đổi thành
//              db = db.getSiblingDB("QuanLyKhoaHoc");
//            - Câu 4 làm thay đổi dữ liệu → làm SAU Câu 2, 3. Muốn làm lại thì chạy lại Câu 1
//              (Câu 1 có drop trước nên chạy lại bao nhiêu lần cũng được).
//            - [NÂNG CAO] = câu khó hơn bài tập trong tài liệu hướng dẫn / slide.
// Thang điểm: Câu 1: 0,5 | Câu 2: 1,5 | Câu 3: 2,0 | Câu 4: 1,0 | Câu 5: 0,5 | Câu 6: 0,5
// =====================================================================================


// =====================================================================================
// Câu 1. (0,5đ) Tạo cơ sở dữ liệu, collection và thêm dữ liệu  — CHẠY KHỐI NÀY TRƯỚC
// =====================================================================================

use QuanLyKhoaHoc;

db.khoahoc.drop();
db.dangky.drop();

db.createCollection("khoahoc");
db.createCollection("dangky");

// Unique index cho khoahoc.maKH và dangky.maDK
db.khoahoc.createIndex({ maKH: 1 }, { unique: true });
db.dangky.createIndex({ maDK: 1 }, { unique: true });

db.khoahoc.insertMany([
    {
        maKH: "KH01", tenKH: "Lap trinh Python co ban", linhVuc: "Lap trinh",
        hocPhi: 2500000, soBuoi: 20, ngayKhaiGiang: ISODate("2026-10-05"), soLuongToiDa: 30,
        giangVien: { maGV: "GV01", tenGV: "Nguyen Van Son", quocGia: "Viet Nam" },
        tags: ["Python", "co ban", "lap trinh"]
    },
    {
        maKH: "KH02", tenKH: "MongoDB va NoSQL", linhVuc: "Co so du lieu",
        hocPhi: 3200000, soBuoi: 24, ngayKhaiGiang: ISODate("2026-10-12"), soLuongToiDa: 25,
        giangVien: { maGV: "GV02", tenGV: "Tran Thi Lan", quocGia: "Viet Nam" },
        tags: ["MongoDB", "NoSQL", "aggregation"]
    },
    {
        maKH: "KH03", tenKH: "Thiet ke UI/UX", linhVuc: "Thiet ke",
        hocPhi: 2800000, soBuoi: 18, ngayKhaiGiang: ISODate("2026-11-02"), soLuongToiDa: 20,
        giangVien: { maGV: "GV03", tenGV: "Michael Brown", quocGia: "My" },
        tags: ["Figma", "UI", "UX"]
    },
    {
        maKH: "KH04", tenKH: "Lap trinh Java nang cao", linhVuc: "Lap trinh",
        hocPhi: 3500000, soBuoi: 30, ngayKhaiGiang: ISODate("2026-10-20"), soLuongToiDa: 30,
        giangVien: { maGV: "GV01", tenGV: "Nguyen Van Son", quocGia: "Viet Nam" },
        tags: ["Java", "OOP", "lap trinh nang cao"]
    },
    {
        maKH: "KH05", tenKH: "Phan tich du lieu voi SQL", linhVuc: "Co so du lieu",
        hocPhi: 2200000, soBuoi: 16, ngayKhaiGiang: ISODate("2026-11-15"), soLuongToiDa: 35,
        giangVien: { maGV: "GV04", tenGV: "Sarah Kim", quocGia: "Han Quoc" },
        tags: ["SQL", "data", "phan tich"]
    }
]);

db.dangky.insertMany([
    {
        maDK: "DK001", ngayDangKy: ISODate("2026-09-01"), trangThai: "Da thanh toan",
        hocVien: { maHV: "HV01", hoTen: "Pham Minh Anh", thanhPho: "TPHCM", email: "anh@mail.com", ngaySinh: ISODate("1999-05-14") },
        chiTiet: [
            { maKH: "KH01", tenKH: "Lap trinh Python co ban", hocPhi: 2500000, giamGia: 0.1, thanhTien: 2250000 },
            { maKH: "KH02", tenKH: "MongoDB va NoSQL", hocPhi: 3200000, giamGia: 0, thanhTien: 3200000 }
        ],
        tongTien: 5450000
    },
    {
        maDK: "DK002", ngayDangKy: ISODate("2026-09-03"), trangThai: "Da thanh toan",
        hocVien: { maHV: "HV02", hoTen: "Le Thi Bich", thanhPho: "Ha Noi", email: "bich@mail.com", ngaySinh: ISODate("2001-11-03") },
        chiTiet: [
            { maKH: "KH03", tenKH: "Thiet ke UI/UX", hocPhi: 2800000, giamGia: 0, thanhTien: 2800000 },
            { maKH: "KH05", tenKH: "Phan tich du lieu voi SQL", hocPhi: 2200000, giamGia: 0.1, thanhTien: 1980000 }
        ],
        tongTien: 4780000
    },
    {
        maDK: "DK003", ngayDangKy: ISODate("2026-09-10"), trangThai: "Cho thanh toan",
        hocVien: { maHV: "HV01", hoTen: "Pham Minh Anh", thanhPho: "TPHCM", email: "anh@mail.com", ngaySinh: ISODate("1999-05-14") },
        chiTiet: [
            { maKH: "KH04", tenKH: "Lap trinh Java nang cao", hocPhi: 3500000, giamGia: 0, thanhTien: 3500000 }
        ],
        tongTien: 3500000
    },
    {
        maDK: "DK004", ngayDangKy: ISODate("2026-09-15"), trangThai: "Da huy",
        hocVien: { maHV: "HV03", hoTen: "Tran Quoc Huy", thanhPho: "Da Nang", email: "huy@mail.com", ngaySinh: ISODate("1998-02-20") },
        chiTiet: [
            { maKH: "KH01", tenKH: "Lap trinh Python co ban", hocPhi: 2500000, giamGia: 0, thanhTien: 2500000 },
            { maKH: "KH04", tenKH: "Lap trinh Java nang cao", hocPhi: 3500000, giamGia: 0.2, thanhTien: 2800000 }
        ],
        tongTien: 5300000
    },
    {
        maDK: "DK005", ngayDangKy: ISODate("2026-10-02"), trangThai: "Da thanh toan",
        hocVien: { maHV: "HV04", hoTen: "Vo Thanh Dat", thanhPho: "TPHCM", email: "dat@mail.com", ngaySinh: ISODate("2003-07-08") },
        chiTiet: [
            { maKH: "KH02", tenKH: "MongoDB va NoSQL", hocPhi: 3200000, giamGia: 0.1, thanhTien: 2880000 },
            { maKH: "KH01", tenKH: "Lap trinh Python co ban", hocPhi: 2500000, giamGia: 0.1, thanhTien: 2250000 },
            { maKH: "KH05", tenKH: "Phan tich du lieu voi SQL", hocPhi: 2200000, giamGia: 0, thanhTien: 2200000 }
        ],
        tongTien: 7330000
    }
]);


// =====================================================================================
// Câu 2. (1,5đ) Truy vấn dữ liệu cơ bản — find()
// =====================================================================================

// 2a. Liệt kê khóa học có hocPhi lớn hơn 3.000.000.
//     Chỉ hiển thị maKH, tenKH, hocPhi; không hiển thị _id. Sắp xếp hocPhi giảm dần.


// 2b. Liệt kê khóa học của giảng viên có quốc gia "Viet Nam" và có ngayKhaiGiang từ ngày 10/10/2026 trở đi.
//     Chỉ hiển thị maKH, tenKH, ngayKhaiGiang và giangVien; không hiển thị _id.


// 2c. Liệt kê các đăng ký của học viên có maHV là HV01.
//     Chỉ hiển thị maDK, ngayDangKy, trangThai, tongTien; không hiển thị _id.


// 2d. Liệt kê đăng ký lập từ ngày 01/09/2026 đến 15/09/2026 có trangThai khác "Da huy".
//     Chỉ hiển thị maDK, ngayDangKy, trangThai.


// 2e. Tìm các khóa học có tags chứa cụm "lap trinh" (không phân biệt hoa thường).
//     Chỉ hiển thị maKH, tenKH, tags.


// 2f. Tìm các khóa học có tên bắt đầu bằng "Lap trinh". Chỉ hiển thị maKH, tenKH.


// 2g. Liệt kê đăng ký của học viên ở "TPHCM" hoặc "Da Nang" (dùng $in).
//     Chỉ hiển thị maDK, hocVien.hoTen, hocVien.thanhPho.


// 2h. Tìm các đăng ký có mua khóa "KH01" VỚI giamGia lớn hơn 0 (cả 2 điều kiện phải cùng nằm trong MỘT phần tử của chiTiet).
//     Chỉ hiển thị maDK.


// 2i. Liệt kê các đăng ký có đúng 2 khóa học trong chiTiet. Chỉ hiển thị maDK.


// 2j. Bỏ qua 1 khóa học đầu tiên (sắp theo maKH), lấy 2 khóa học tiếp theo. Chỉ hiển thị maKH, tenKH.


// 2k. Đếm số đăng ký có trangThai "Da thanh toan".


// 2l. Cho biết danh sách các thành phố khác nhau của học viên (không trùng).



// =====================================================================================
// Câu 3. (2,0đ) Truy vấn nâng cao bằng Aggregation Framework
// =====================================================================================

// 3a. Thống kê theo học viên: hiển thị maHV, hoTen, soLuongDangKy, tongTien (tổng tongTien các đăng ký).
//     Sắp xếp theo maHV tăng dần.


// 3b. Thống kê theo khóa học: hiển thị maKH, tenKH, soLuotDangKy (số dòng chiTiet), tongDoanhThu (tổng thanhTien)
//     và soDonDangKy (số đăng ký khác nhau có chứa khóa đó — dùng $addToSet rồi $size).
//     Gợi ý: $unwind chiTiet, $group, $project.


// 3c. [NÂNG CAO] Thống kê theo lĩnh vực: hiển thị linhVuc, tongSoLuot, tongDoanhThu, soDon và danhSachMaDK.
//     Gợi ý: $unwind chiTiet → $lookup sang khoahoc (chiTiet.maKH = maKH) → $unwind → $group theo linhVuc.
//     Cẩn thận: soDon phải là số đăng ký KHÁC NHAU (không phải số dòng chiTiet).


// 3d. Tìm học viên có tổng tiền các đăng ký lớn hơn 6.000.000 (bỏ qua đăng ký "Da huy").
//     Hiển thị maHV, hoTen và tongTien.
//     Gợi ý: $match trước → $group → $match sau.


// 3e. Thống kê doanh thu theo tháng: chỉ tính đăng ký "Da thanh toan"; hiển thị nam, thang, soDon, doanhThu.
//     Sắp xếp theo năm, tháng tăng dần. (Gợi ý: $year, $month)


// 3f. Liệt kê maDK của những đăng ký được lập vào tháng 9 năm 2026.
//     (Gợi ý: $project tạo trường thang, nam bằng $month, $year rồi $match.)


// 3g. Hiển thị 2 khóa học có tongDoanhThu cao nhất (maKH, tenKH, tongDoanhThu). Gợi ý: kết quả 3b + $sort + $limit.


// 3h. Với collection khoahoc: cho biết linhVuc, hocPhiTrungBinh, hocPhiCaoNhat, hocPhiThapNhat.


// 3i. Với mỗi giảng viên: hiển thị maGV, tenGV, soKhoaHoc và danhSachTenKH (đưa vào mảng bằng $push).


// 3j. Hiển thị maHV, hoTen và soLuongDangKy của những học viên có TRÊN 1 đăng ký.


// 3k. Hiển thị maKH, tenKH viết HOA ($toUpper), hocPhiMoiBuoi (= hocPhi / soBuoi, làm tròn 0 chữ số thập phân)
//     và mucHocPhi = "Cao" nếu hocPhi >= 3.000.000, ngược lại "Thap".
//     [NÂNG CAO] Gợi ý: $project + $round + $divide + $cond.


// 3l. [NÂNG CAO] Với mỗi khóa học, hiển thị maKH, tenKH, soLuongToiDa, soDangKy và soChoConLai (= soLuongToiDa - soDangKy).
//     Gợi ý: $lookup từ khoahoc sang dangky với foreignField: "chiTiet.maKH", rồi $size / $subtract.


// 3m. Với mỗi khóa học, cho biết số học viên KHÁC NHAU đã đăng ký (bỏ qua đăng ký "Da huy").
//     Hiển thị maKH, tenKH, soHocVien.


// 3n. Hiển thị maHV, hoTen và tuoi của từng học viên (không trùng). Tuổi = năm hiện tại - năm sinh.
//     Gợi ý: new Date() lấy ngày hiện tại, $year lấy năm, $subtract để trừ.



// =====================================================================================
// Câu 4. (1,0đ) Thêm, cập nhật và xóa dữ liệu   (chạy SAU Câu 2, 3)
// =====================================================================================

// 4a. Thêm khóa học mới bằng insertOne: maKH "KH06", tenKH "DevOps co ban", linhVuc "Ha tang",
//     hocPhi 3.000.000, soBuoi 20, ngayKhaiGiang 01/12/2026, soLuongToiDa 25,
//     giangVien { maGV: "GV05", tenGV: "Do Minh Quan", quocGia: "Viet Nam" }, tags ["Docker", "CI/CD", "DevOps"].


// 4b. Cập nhật hocPhi của khóa KH02 thành 3.000.000.


// 4c. Tăng soLuongToiDa thêm 5 cho tất cả khóa thuộc linhVuc "Lap trinh".
//     [NÂNG CAO] Giảm 10% hocPhi cho tất cả khóa thuộc linhVuc "Co so du lieu" (gợi ý: $mul).


// 4d. Cập nhật hocVien.thanhPho thành "Binh Duong" cho học viên HV01 trong TẤT CẢ đăng ký.


// 4e. Với khóa KH02: (i) thêm tag "big data" bằng $push; (ii) thêm tag "NoSQL" bằng $addToSet (quan sát: có bị trùng không?);
//     (iii) xóa tag "aggregation" bằng $pull.


// 4f. Trong đăng ký DK001, đổi giamGia của khóa KH02 thành 0.05 và thanhTien thành 3.040.000;
//     đồng thời giảm tongTien tương ứng (dùng toán tử vị trí $ hoặc chỉ số "chiTiet.1.").


// 4g. Xóa khóa KH05 ra khỏi mảng chiTiet của đăng ký DK002 (dùng $pull), rồi cập nhật lại tongTien cho đúng.


// 4h. Xóa tất cả đăng ký có trangThai "Da huy". Xóa 1 đăng ký có maDK "DK003".


// 4i. [NÂNG CAO] Dùng updateOne với { upsert: true } để thêm/cập nhật khóa học maKH "KH07" (tenKH "Data Science co ban", hocPhi 4.000.000).
//     Sau đó dùng replaceOne thay thế toàn bộ document KH07 bằng document mới có thêm trường soBuoi: 28.


// 4j. [NÂNG CAO] Đổi tên trường soLuongToiDa thành siSoToiDa ($rename) cho khóa KH01; sau đó xóa trường soBuoi khỏi KH01 ($unset).
//     Rồi khôi phục lại như cũ.



// =====================================================================================
// Câu 5. (0,5đ) Chỉ mục (Index) — xem bài tập 9 của tài liệu hướng dẫn
// =====================================================================================

// 5a. Hiển thị tất cả index hiện có của collection khoahoc.


// 5b. Tạo index cho giangVien.maGV (tăng dần). Dùng explain("executionStats") chạy truy vấn
//     find({ "giangVien.maGV": "GV01" }) TRƯỚC và SAU khi tạo index; ghi lại: stage (COLLSCAN/IXSCAN),
//     totalKeysExamined, totalDocsExamined.


// 5c. Tạo index kết hợp cho linhVuc (tăng) và hocPhi (giảm), đặt tên "idx_linhvuc_hocphi".
//     Sau đó xóa index này.


// 5d. Tạo index duy nhất (unique) + thưa (sparse) cho trường hocVien.email của dangky. Giải thích: index unique khác gì so với chỉ mục thường?
//     Chạy được không? Vì sao? (Gợi ý: xem dữ liệu, cùng 1 học viên có nhiều đăng ký.)
//     LƯU Ý: câu này chỉ cho kết quả như đề dự kiến khi dữ liệu còn nguyên — hãy chạy lại Câu 1 trước khi làm Câu 5.



// =====================================================================================
// Câu 6. (0,5đ) Import / Export, Sao lưu / Phục hồi — xem mục 1.3 tài liệu hướng dẫn
//         (viết lệnh chạy trong cmd / PowerShell, KHÔNG phải trong mongosh)
// =====================================================================================

// 6a. Export collection khoahoc ra file JSON  D:\MONGO\EXPORT\khoahoc.json.
// 6b. Export collection dangky ra file CSV chỉ với các trường maDK, ngayDangKy, trangThai, tongTien.
// 6c. Import file khoahoc.json vào collection mới tên khoahoc_copy.
// 6d. Sao lưu toàn bộ database QuanLyKhoaHoc vào thư mục D:\MONGO\EXPORT\fulldb.
// 6e. Phục hồi bản sao lưu đó vào database mới tên QuanLyKhoaHoc_restore.
