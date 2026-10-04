# Bài tập buổi 1 — MongoDB — Bài tập 1 (trên lớp)

## Cách học trên lớp: gõ trong mongosh

Mở shell:

```powershell
cd D:\Documents\Homework\Nam4\NoSQL
docker compose up -d mongo
docker exec -it nosql-mongo mongosh
```

Trong mongosh, chọn database rồi gõ lệnh:

```javascript
use QLSinhVien
db.sinhvien.countDocuments()
```

Mỗi câu trong đề là một lệnh. Chép lệnh từ `BaiTap01_TrenLop.js` vào shell, gõ Enter, xem kết quả trả về.

MongoDB trả về dạng `{ acknowledged: true, matchedCount: 1, modifiedCount: 1 }`. Nhìn hai số cuối để biết lệnh có ăn hay không:

- `matchedCount: 0` — filter sai, không tìm thấy document nào. Kiểm tra lại mã sinh viên hoặc đường dẫn field.
- `matchedCount: 1, modifiedCount: 0` — tìm thấy nhưng dữ liệu đã đúng sẵn, không có gì để sửa.
- `modifiedCount: 1` — sửa thành công.

Thoát shell: `exit`.

## Câu 1 — Import dữ liệu

Đề yêu cầu import từ file thầy cung cấp. Nếu chưa có file đó, dùng `data/sinhvien.json` — file này dựng lại đúng theo bảng phụ lục trang 4–5 của đề.

`mongoimport` không chạy được bên trong mongosh vì nó là chương trình riêng. Chạy ở PowerShell:

```powershell
docker exec -it nosql-mongo mongoimport --db QLSinhVien --collection sinhvien --drop --jsonArray --file /baitap/Chuong02_MongoDB/data/sinhvien.json
```

Cờ `--drop` xóa collection cũ trước khi nạp, nên chạy lại nhiều lần vẫn ra đúng 10 sinh viên. Khi làm sai câu nào đó và muốn làm lại từ đầu, chạy đúng lệnh này.

Khi nhận được file của thầy, chỉ cần đổi phần `--file` thành đường dẫn file đó. Nhớ chép file vào thư mục `BaiTap/` trước, vì container chỉ nhìn thấy thư mục này.

## Cấu trúc document

Hiểu cấu trúc thì mới viết đúng đường dẫn field:

```javascript
{
  Masv: "SV011",
  Hoten: "Nguyễn Văn Nam",
  Ngaysinh: "2003-06-15",
  Phai: "Nam",
  Email: [ "nam.nguyen@gmail.com", "nam.nguyen@stu.edu.vn" ],   // mảng chuỗi
  Lop: { Malop: "CTK45A", Tenlop: "Công nghệ Thông tin K45A" }, // sub-document
  Monhoc: [                                                     // mảng sub-document
    { Mamh: "MH001", Tenmh: "Cơ sở dữ liệu", Sotc: 3, Diem: 8.0 },
    { Mamh: "MH002", Tenmh: "Lập trình Java", Sotc: 3, Diem: 7.5 }
  ]
}
```

Bảng phụ lục in mỗi môn học một dòng, nhưng đó là cách trình bày của bảng. Trong MongoDB gom lại thành một document cho mỗi sinh viên, môn học nằm trong mảng `Monhoc`. Đây chính là điểm khác biệt với mô hình quan hệ mà môn học nhấn mạnh.

## Câu 2–21 — các lệnh

Toàn bộ nằm trong `BaiTap01_TrenLop.js`, có chú thích từng câu.

Bốn nhóm kỹ thuật cần nắm:

**Sửa field thường** — `$set` để thêm hoặc sửa, `$unset` để xóa hẳn field.

```javascript
db.sinhvien.updateOne({ Masv: "SV011" }, { $set: { Diachi: "..." } })
db.sinhvien.updateOne({ Masv: "SV013" }, { $unset: { Phai: "" } })
```

**Đi vào sub-document** — dùng dấu chấm, và bắt buộc đặt trong dấu nháy:

```javascript
db.sinhvien.updateMany({ "Lop.Malop": "CTK45A" }, { $set: { "Lop.Tenlop": "..." } })
```

Không có nháy thì JavaScript báo lỗi cú pháp.

**Thao tác trên mảng** — `$push` thêm, `$pull` xóa, `$each` thêm nhiều phần tử:

```javascript
{ $push: { Email: "a@b.com" } }                              // thêm 1
{ $push: { Email: { $each: ["a@b.com", "c@d.com"] } } }      // thêm nhiều
{ $pull: { Email: "a@b.com" } }                              // xóa theo giá trị
{ $pull: { Monhoc: { Mamh: "MH003" } } }                     // xóa theo điều kiện
{ $set:  { "Email.1": "..." } }                              // sửa phần tử thứ 2 (đếm từ 0)
{ $set:  { Email: [] } }                                     // xóa sạch mảng
```

**Sửa một phần tử trong mảng sub-document** — toán tử vị trí `$`:

```javascript
db.sinhvien.updateOne(
  { Masv: "SV012", "Monhoc.Mamh": "MH001" },   // điều kiện này bắt buộc phải có
  { $set: { "Monhoc.$.Diem": 9.5 } }           // $ trỏ tới phần tử vừa khớp
)
```

Thiếu điều kiện `"Monhoc.Mamh"` trong filter thì MongoDB báo lỗi vì `$` không biết trỏ vào phần tử nào.

`updateOne` sửa 1 document đầu tiên khớp, `updateMany` sửa tất cả. Đề nói "cho tất cả sinh viên" thì dùng `updateMany`.

## Câu 22 — Export

```powershell
docker exec -it nosql-mongo mongoexport --db QLSinhVien --collection sinhvien --jsonArray --pretty --out /baitap/Chuong02_MongoDB/data/sinhvien_export.json
```

File hiện ra ngay trong `BaiTap/Chuong02_MongoDB/data/` trên máy, mở bằng VS Code xem được.

## Chạy cả file một lượt

Khi muốn kiểm tra lại toàn bộ bài, hoặc sau khi import lại dữ liệu:

```powershell
docker exec -it nosql-mongo mongosh QLSinhVien /baitap/Chuong02_MongoDB/BaiTap01_TrenLop.js
```

## Lưu ý về thứ tự

Các câu phụ thuộc nhau, phải chạy theo đúng thứ tự đề bài:

- Câu 19 xóa môn MH003 của SV013. Sau đó câu 20 sửa số tín chỉ môn "Mạng máy tính" cho lớp CTK45A — lúc này chỉ còn SV014 có môn đó, nên chỉ SV014 bị sửa. Đây là kết quả đúng.
- Câu 13 xóa email duy nhất của SV012, nên mảng `Email` của SV012 thành rỗng.

Làm rối thứ tự thì chạy lại lệnh import ở câu 1 để về trạng thái ban đầu.
