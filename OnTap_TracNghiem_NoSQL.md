# Bộ đề ôn tập thường xuyên — Dữ liệu NoSQL (14DH)

Dùng để tự kiểm tra kiến thức định kỳ, độc lập với đồ án. Bám sát đề cương chi tiết môn học (5 chương) và ánh xạ đúng vào 2 mốc kiểm tra chính thức:

- **KT1 (buổi 6):** Chương 1 + 2 + 3 (Tổng quan NoSQL, MongoDB, Cassandra)
- **KT2 (buổi 9):** Chương 4 + 5 (Neo4j, Redis)

Mỗi chương có 3 phần: **(A) Trắc nghiệm khái niệm** (nhớ đúng thuật ngữ — ứng CLO1.x), **(B) Viết lệnh** (ứng CLO2.x/CLO3.x, phải tự gõ ra được chứ không chỉ chọn đáp án), **(C) Tình huống/logic** (ứng CLO2.1 + CLO3.2 — đây là phần luyện tư duy thiết kế, không có câu trả lời "học thuộc" được). Đáp án để riêng cuối mỗi chương — làm xong mới xem, đúng tinh thần tự kiểm tra.

Cách dùng gợi ý: mỗi tuần làm 1 chương, tuần cuối trước KT1 làm lại trọn chương 1-3, tuần cuối trước KT2 làm lại trọn chương 4-5.

---

## CHƯƠNG 1 — Tổng quan NoSQL

### A. Trắc nghiệm khái niệm

1. CAP theorem phát biểu hệ phân tán chỉ đảm bảo được tối đa mấy trong ba tính chất Consistency, Availability, Partition Tolerance?
 a) Cả 3 cùng lúc b) Tối đa 2 trong 3 c) Chỉ 1 d) Không đảm bảo cái nào

2. Trong CAP, "Partition Tolerance" nghĩa là gì?
 a) Hệ thống chia dữ liệu thành nhiều phần bằng nhau
 b) Hệ thống vẫn hoạt động dù mất kết nối/liên lạc giữa các node
 c) Hệ thống không cho phép ghi đồng thời
 d) Hệ thống tự động backup định kỳ

3. Cassandra và MongoDB thường được xếp vào nhóm nào của CAP (ưu tiên gì hơn Consistency mạnh)?
 a) CA b) CP c) AP d) Không thuộc CAP

4. BASE (đối lập ACID) là viết tắt của?
 a) Basically Available, Soft state, Eventually consistent
 b) Batch Async Sync Engine
 c) Base Availability System Extension
 d) Backup Available System Environment

5. 4 họ NoSQL chính theo đề cương môn là?
 a) SQL, NoSQL, NewSQL, GraphQL
 b) Document, Column-family, Key-value, Graph
 c) Relational, Non-relational, Hybrid, Cloud
 d) OLTP, OLAP, ETL, ELT

6. MongoDB thuộc họ nào?
 a) Key-value b) Document c) Column-family d) Graph

7. Cassandra thuộc họ nào?
 a) Key-value b) Document c) Column-family (wide-column) d) Graph

8. Neo4j thuộc họ nào?
 a) Key-value b) Document c) Column-family d) Graph

9. Redis thuộc họ nào (chính)?
 a) Key-value b) Document c) Column-family d) Graph

10. Nhược điểm chung lớn nhất của NoSQL so với RDBMS là gì?
 a) Không scale ngang được
 b) Thiếu chuẩn hoá mạnh, hạn chế ràng buộc toàn vẹn (không JOIN/FK mạnh như SQL)
 c) Không lưu được dữ liệu lớn
 d) Không hỗ trợ phân tán

11. Vì sao NoSQL "sinh ra" — động lực lịch sử chính là gì?
 a) Thay hoàn toàn RDBMS ở mọi bài toán
 b) Đáp ứng scale ngang, dữ liệu lớn, tốc độ ghi cao mà RDBMS truyền thống khó đạt
 c) Chuẩn hoá dữ liệu tốt hơn SQL
 d) Giảm chi phí license phần cứng

12. Scale ngang (horizontal scaling) khác scale dọc (vertical scaling) ở điểm nào?
 a) Scale ngang thêm node mới; scale dọc nâng cấp phần cứng 1 node
 b) Scale ngang nâng cấp phần cứng; scale dọc thêm node mới
 c) Hai khái niệm giống nhau
 d) Scale ngang chỉ áp dụng cho RDBMS

13. Ứng dụng nào sau đây KHÔNG phải ví dụ điển hình dùng NoSQL?
 a) Session/cache tốc độ cao (Redis)
 b) Mạng xã hội, quan hệ bạn bè (Graph DB)
 c) Sổ cái kế toán doanh nghiệp cần ACID nghiêm ngặt xuyên bảng
 d) Log/telemetry ghi liên tục, khối lượng lớn (Column-family)

14. Eventual consistency nghĩa là gì?
 a) Dữ liệu không bao giờ nhất quán
 b) Nếu ngừng ghi đủ lâu, tất cả bản sao cuối cùng sẽ hội tụ về cùng giá trị
 c) Chỉ node chính mới có dữ liệu đúng
 d) Hệ thống từ chối mọi request khi có xung đột

15. "Denormalization" (phi chuẩn hoá, cố ý trùng lặp dữ liệu) phổ biến trong thiết kế NoSQL vì lý do gì?
 a) Tiết kiệm ổ cứng b) Không hỗ trợ JOIN/join tốn kém → tối ưu đọc theo truy vấn, chấp nhận trùng lặp khi ghi c) Bắt buộc theo chuẩn ISO d) Không có lý do kỹ thuật, chỉ là thói quen

### C. Tình huống/logic

16. Một hệ thống ngân hàng lõi (core banking) cần đảm bảo số dư tài khoản tuyệt đối chính xác sau mọi giao dịch, kể cả khi 1 node lỗi. Bạn sẽ khuyên chọn CP hay AP? Giải thích bằng chính định nghĩa Consistency/Availability.

17. Một hệ thống ghi log truy cập web, khối lượng hàng tỷ dòng/ngày, chấp nhận đôi khi đọc dữ liệu vài giây trước (chưa mới nhất) miễn hệ thống luôn ghi được. Đây nên thiên CP hay AP? Vì sao?

18. Giải thích tại sao "NoSQL" không có nghĩa "không dùng SQL nào cả" — nêu ví dụ 1 hệ NoSQL vẫn có ngôn ngữ truy vấn giống SQL.

### D. Nâng cao

19. Cassandra consistency level QUORUM tính theo công thức nào? Với Replication Factor = 3, QUORUM = mấy node phải phản hồi?

20. Giải thích vì sao hệ "AP" như Cassandra vẫn có thể đạt strong consistency tại một truy vấn cụ thể mà không đổi kiến trúc nền (gợi ý: tunable consistency, W + R > RF).

21. So sánh CA, CP, AP: vì sao trong hệ phân tán thật (nhiều node/nhiều vùng), lựa chọn "CA" gần như không tồn tại bền vững?

### Đáp án chương 1

A: 1b 2b 3c 4a 5b 6b 7c 8d 9a 10b 11b 12a 13c 14b 15b

C16: Chọn **CP**. Consistency = mọi node thấy cùng dữ liệu tại cùng thời điểm; hệ ngân hàng không chấp nhận đọc số dư sai dù chỉ 1 khắc — nên khi partition xảy ra, hệ thống thà từ chối request (giảm Availability) còn hơn trả về số dư không nhất quán.

C17: Chọn **AP**. Availability = luôn nhận phản hồi. Hệ thống log chấp nhận đọc dữ liệu cũ vài giây (eventual consistency) để đổi lấy việc không bao giờ từ chối ghi/đọc, kể cả khi mạng chập chờn.

C18: Cassandra dùng **CQL** (Cassandra Query Language) — cú pháp gần giống SQL (`SELECT`, `INSERT`, `WHERE`) nhưng không hỗ trợ JOIN/subquery và bắt buộc `WHERE` có partition key. "NoSQL" đúng nghĩa hơn là "Not only SQL".

D19: QUORUM = floor(RF/2) + 1. Với RF = 3 → QUORUM = 2 node phải phản hồi.

D20: Cassandra cho chỉnh consistency level theo từng truy vấn (ONE, QUORUM, ALL...). Nếu W (write consistency) + R (read consistency) > RF, chắc chắn tập node được ghi và tập node được đọc giao nhau ít nhất 1 node → lần đọc luôn thấy được giá trị mới nhất, đạt strong consistency cho truy vấn đó dù kiến trúc nền vẫn AP.

D21: Partition Tolerance không phải lựa chọn tuỳ ý — mạng thật luôn có khả năng đứt kết nối giữa các node (lỗi cáp, timeout, sự cố vùng). Hệ CA giả định mạng không bao giờ đứt, chỉ đúng khi chạy trên 1 node đơn hoặc cụm rất nhỏ cùng datacenter cực ổn định; hễ mở rộng ra nhiều node/nhiều vùng thật sự thì buộc phải ngả về CP hoặc AP.

---

## CHƯƠNG 2 — MongoDB

### A. Trắc nghiệm khái niệm

1. Đơn vị lưu trữ nhỏ nhất trong MongoDB tương đương 1 "row" trong SQL gọi là gì?
 a) Collection b) Document c) Field d) Database

2. Một nhóm các Document tương đương 1 "table" trong SQL gọi là gì?
 a) Schema b) Collection c) Index d) Namespace

3. MongoDB lưu Document ở định dạng nhị phân nào?
 a) XML b) YAML c) BSON d) CSV

4. Mô hình dữ liệu "Embedded" trong MongoDB nghĩa là gì?
 a) Nhúng document con vào bên trong document cha (1 lần đọc lấy hết)
 b) Lưu tham chiếu ID sang collection khác
 c) Không lưu quan hệ nào cả
 d) Lưu dữ liệu ở file ngoài

5. Mô hình "Reference" khác "Embedded" ở điểm cốt lõi nào?
 a) Reference lưu `_id` trỏ sang document/collection khác, phải query thêm lần 2 (giống JOIN thủ công)
 b) Reference nhanh hơn Embedded trong mọi trường hợp
 c) Reference không dùng được với `_id`
 d) Không có khác biệt

6. Khi nào nên dùng Embedded thay vì Reference?
 a) Khi dữ liệu con luôn được đọc cùng dữ liệu cha, quan hệ 1-nhiều "chặt", ít khi truy vấn con độc lập
 b) Khi dữ liệu con rất lớn, tăng trưởng không giới hạn (unbounded array)
 c) Khi nhiều document cha cùng dùng chung 1 document con (many-to-many)
 d) Luôn luôn nên dùng Embedded

7. "Atomic Operations" trong MongoDB đảm bảo điều gì?
 a) Nhiều document được cập nhật cùng lúc không thể tách rời (all-or-nothing) ở cấp 1 document
 b) Toàn bộ database luôn nhất quán tuyệt đối
 c) Không cho phép cập nhật dữ liệu
 d) Tự động backup sau mỗi thao tác

8. Lệnh nào chèn nhiều document cùng lúc?
 a) `insertOne()` b) `insertMany()` c) `insertAll()` d) `bulkInsert()`

9. `updateOne()` với toán tử `$set` dùng để làm gì?
 a) Thay hoàn toàn document b) Chỉ cập nhật field chỉ định, giữ nguyên field khác, trên document đầu tiên khớp filter c) Xoá field d) Tạo index

10. Toán tử nào dùng để tăng giá trị số của 1 field?
 a) `$inc` b) `$add` c) `$plus` d) `$sum`

11. `db.collection.find({ field: { $exists: false } })` trả về gì?
 a) Document có field đó bằng null b) Document KHÔNG có field đó c) Lỗi cú pháp d) Toàn bộ collection

12. `findOneAndUpdate()` khác `updateOne()` ở điểm nào?
 a) Không khác gì b) `findOneAndUpdate` trả về document (trước hoặc sau update) trong 1 lần gọi, `updateOne` chỉ trả kết quả thao tác c) `findOneAndUpdate` cập nhật nhiều document d) `updateOne` nhanh hơn tuyệt đối

13. Aggregation Pipeline trong MongoDB dùng để làm gì?
 a) Chỉ để insert dữ liệu b) Xử lý dữ liệu qua nhiều giai đoạn (`$match`, `$group`, `$sort`...) để tổng hợp/biến đổi, tương đương GROUP BY/JOIN phức tạp trong SQL c) Backup dữ liệu d) Tạo user

14. Trong C#/Java, để kết nối MongoDB cần thành phần nào đầu tiên?
 a) Connection string + Driver (MongoDB.Driver cho C#, mongodb-driver-sync cho Java) b) Chỉ cần IP server c) Không cần driver, gọi HTTP trực tiếp d) Phải cài ODBC

### B. Viết lệnh

15. Viết lệnh MongoDB tạo collection `drivers` và insert 1 document có `name`, `phone`, `rating`.

16. Viết lệnh tìm tất cả document trong collection `trips` có `status = "completed"` và `fare > 50000`.

17. Viết lệnh cập nhật rating trung bình (`avg_rating`) của 1 driver có `_id` cho trước bằng `$set`.

18. Viết lệnh xoá toàn bộ document trong collection `trips` có `status = "cancelled"`.

### C. Tình huống/logic

19. Bài toán đặt xe: 1 chuyến đi (trip) có nhiều điểm GPS ping (có thể hàng trăm điểm/chuyến, nhưng cố định sau khi chuyến kết thúc). Bạn dùng Embedded hay Reference cho quan hệ trip → GPS ping? Giải thích dựa vào tiêu chí ở câu A6.

20. Nếu 1 khách hàng có thể có hàng chục nghìn chuyến đi trong lịch sử (unbounded, tăng vô hạn theo thời gian), bạn dùng Embedded hay Reference cho quan hệ customer → trips? Vì sao Embedded ở đây sẽ gây vấn đề (gợi ý: giới hạn 16MB/document của MongoDB).

### D. Nâng cao

21. MongoDB từ bản 4.0 hỗ trợ multi-document ACID transaction. Trước đó, vì sao thiết kế Embedded lại quan trọng hơn hẳn để đảm bảo tính atomic?

22. Sharding trong MongoDB: chọn shard key là 1 field tăng dần đơn điệu (vd `created_at`) gây hậu quả gì cho việc phân tải?

23. Viết 1 aggregation pipeline tính tổng doanh thu (`fare`) theo từng ngày từ collection `trips` (chỉ tính chuyến `status = "completed"`).

### Đáp án chương 2

A: 1b 2b 3c 4a 5a 6a 7a 8b 9b 10a 11b 12b 13b 14a

B15:
```js
db.createCollection("drivers")
db.drivers.insertOne({ name: "Nguyen Van A", phone: "0900000000", rating: 4.8 })
```
B16: `db.trips.find({ status: "completed", fare: { $gt: 50000 } })`
B17: `db.drivers.updateOne({ _id: driverId }, { $set: { avg_rating: 4.7 } })`
B18: `db.trips.deleteMany({ status: "cancelled" })`

C19: **Embedded** — GPS ping của 1 chuyến luôn đọc cùng chuyến đó, quan hệ 1-nhiều chặt, dữ liệu con không đổi sau khi chuyến kết thúc (bounded, biết trước kích thước tối đa). Đúng tiêu chí A6.

C20: **Reference**. Nếu Embedded, mảng `trips` trong document customer sẽ phình vô hạn theo thời gian, có ngày vượt giới hạn 16MB/document của MongoDB và làm chậm mọi lần đọc profile khách hàng (phải load hết lịch sử chỉ để xem tên khách). Reference: lưu `customer_id` trong mỗi document trip, query riêng khi cần lịch sử.

D21: Trước bản 4.0, MongoDB chỉ đảm bảo atomic ở cấp **1 document**, không xuyên nhiều document/collection. Embedded gom dữ liệu liên quan vào cùng 1 document là cách duy nhất khi đó để đảm bảo cập nhật cha-con atomic trong 1 lệnh, không sợ dừng nửa chừng.

D22: Shard key tăng dần đơn điệu khiến mọi ghi mới luôn rơi vào đúng 1 chunk/shard "mới nhất" tại mọi thời điểm — tạo "hot shard", các shard còn lại rảnh rỗi, mất hoàn toàn lợi ích scale ngang.

D23:
```js
db.trips.aggregate([
  { $match: { status: "completed" } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$completed_at" } },
      total_fare: { $sum: "$fare" }
  }},
  { $sort: { _id: 1 } }
])
```

---

## CHƯƠNG 3 — Cassandra

### A. Trắc nghiệm khái niệm

1. Đơn vị tương đương "database" trong Cassandra gọi là gì?
 a) Schema b) Keyspace c) Namespace d) Catalog

2. Đơn vị tương đương "table" trong Cassandra (tên cũ) gọi là gì?
 a) Document b) Column family c) Node d) Partition

3. Replication Factor (RF) trong Cassandra xác định điều gì?
 a) Số lần 1 dòng dữ liệu được sao chép sang các node khác trong cluster
 b) Số lượng keyspace tối đa
 c) Tốc độ ghi dữ liệu
 d) Số cột tối đa trong 1 bảng

4. Partition Key dùng để làm gì?
 a) Sắp xếp dữ liệu trong 1 partition
 b) Băm (hash) để xác định dữ liệu được lưu ở node nào trong cluster
 c) Chỉ để hiển thị đẹp trên UI
 d) Không có tác dụng kỹ thuật, chỉ là quy ước đặt tên

5. Clustering Column dùng để làm gì?
 a) Xác định node lưu trữ b) Sắp xếp thứ tự các dòng dữ liệu BÊN TRONG cùng 1 partition c) Mã hoá dữ liệu d) Tạo thêm keyspace

6. Trong CQL, mệnh đề `WHERE` bắt buộc phải có gì (trừ khi dùng ALLOW FILTERING)?
 a) Ít nhất Partition Key b) Bất kỳ cột nào c) Clustering column trước d) Không bắt buộc gì

7. Vì sao Cassandra KHÔNG hỗ trợ JOIN?
 a) Vì lỗi thiết kế chưa fix
 b) Kiến trúc phân tán không master, JOIN xuyên node cực tốn — nên bắt thiết kế phi chuẩn hoá (denormalize), 1 bảng ứng 1 truy vấn (query-first)
 c) Vì Cassandra không hỗ trợ nhiều bảng
 d) Vì lý do license

8. Chiến lược thiết kế dữ liệu Cassandra chuẩn (Chebotko method) đi theo thứ tự nào?
 a) Vẽ ER trước, viết truy vấn sau
 b) Liệt kê Application Workflow/Query trước → rồi mới thiết kế bảng theo từng truy vấn (query-first)
 c) Chuẩn hoá 3NF trước, denormalize sau
 d) Không có phương pháp chuẩn nào

9. Tombstone trong Cassandra là gì?
 a) Bản ghi bị lỗi cú pháp
 b) Đánh dấu "đã xoá" tạm thời (do kiến trúc ghi log/append, xoá thật diễn ra khi compaction)
 c) Một loại index
 d) Tên gọi khác của partition key

10. TTL (Time To Live) trong Cassandra dùng để làm gì?
 a) Giới hạn thời gian kết nối b) Tự động hết hạn (xoá) 1 dòng/cột sau khoảng thời gian định trước c) Giới hạn số node d) Đặt thời gian chờ query

11. Compaction trong Cassandra là gì?
 a) Nén ảnh trong database b) Gộp nhiều SSTable thành ít file hơn, dọn tombstone, tối ưu đọc c) Mã hoá dữ liệu d) Tạo bản backup

12. Cơ chế ghi dữ liệu Cassandra theo thứ tự nào?
 a) Ghi thẳng vào SSTable trên đĩa
 b) Commit log (đĩa, để phục hồi) → Memtable (RAM) → flush xuống SSTable (đĩa)
 c) Ghi vào cache trước, không cần log
 d) Ghi trực tiếp qua network tới node khác trước

13. Vì sao "wide partition" (1 partition chứa quá nhiều dữ liệu, ví dụ Discord từng gặp) là vấn đề?
 a) Không có vấn đề gì
 b) Toàn bộ partition nằm trên node cố định → hot node, đọc/ghi chậm, dễ timeout, GC pause
 c) Chỉ ảnh hưởng tốc độ ghi, không ảnh hưởng đọc
 d) Cassandra tự động chia nhỏ nên không cần lo

14. TWCS (TimeWindowCompactionStrategy) phù hợp nhất cho loại dữ liệu nào?
 a) Dữ liệu tĩnh, ít thay đổi b) Dữ liệu time-series có TTL, ghi liên tục theo thời gian (vd log, GPS ping) c) Dữ liệu quan hệ nhiều chiều d) Dữ liệu nhị phân lớn (blob)

15. Trong C#/Java/Python, kết nối Cassandra dùng driver nào phổ biến?
 a) ODBC chuẩn chung mọi hệ b) DataStax driver riêng cho từng ngôn ngữ (giao tiếp qua CQL native protocol, cổng mặc định 9042) c) JDBC-ODBC bridge duy nhất d) Không cần driver, dùng REST có sẵn

### B. Viết lệnh

16. Viết CQL tạo keyspace `ridehailing` với `SimpleStrategy`, replication_factor = 3.

17. Viết CQL tạo bảng `trips_by_driver` với partition key `driver_id`, clustering column `trip_time` (giảm dần), các cột `trip_id`, `fare`, `status`.

18. Viết CQL SELECT lấy 10 chuyến gần nhất của 1 driver cụ thể, sắp theo `trip_time` giảm dần.

19. Viết CQL tạo bảng lưu GPS ping có TTL 30 ngày cho mỗi dòng (dùng `USING TTL` hoặc `default_time_to_live`).

### C. Tình huống/logic

20. Bài toán: cần truy vấn "lấy toàn bộ chuyến đi của 1 khách hàng, sắp theo thời gian mới nhất". Bạn thiết kế partition key và clustering column nào cho bảng `trips_by_customer`? Giải thích vì sao không dùng `trip_id` làm partition key.

21. Nếu 1 tài xế chạy liên tục nhiều năm, bảng `trips_by_driver` chỉ partition theo `driver_id` sẽ gặp vấn đề gì (liên hệ câu A13)? Nêu 1 cách khắc phục (gợi ý: bucket theo tháng/năm, giống Discord bucket 10 ngày).

### D. Nâng cao

22. `ALLOW FILTERING` trong CQL là gì, vì sao dùng nó ở production thường là dấu hiệu thiết kế bảng sai?

23. Secondary Index khác Materialized View trong Cassandra ở điểm nào? Khi nào nên dùng cái nào?

24. Lightweight Transaction (LWT, mệnh đề `IF NOT EXISTS`) đánh đổi gì so với ghi thường? Viết CQL tạo bảng + câu lệnh LWT đảm bảo 1 chuyến đi (`trip_id`) chỉ được đúng 1 tài xế nhận (claim), tránh 2 tài xế cùng nhận 1 chuyến.

### Đáp án chương 3

A: 1b 2b 3a 4b 5b 6a 7b 8b 9b 10b 11b 12b 13b 14b 15b

B16:
```sql
CREATE KEYSPACE ridehailing
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};
```
B17:
```sql
CREATE TABLE ridehailing.trips_by_driver (
  driver_id UUID,
  trip_time TIMESTAMP,
  trip_id UUID,
  fare DECIMAL,
  status TEXT,
  PRIMARY KEY (driver_id, trip_time)
) WITH CLUSTERING ORDER BY (trip_time DESC);
```
B18:
```sql
SELECT * FROM ridehailing.trips_by_driver
WHERE driver_id = <id>
ORDER BY trip_time DESC
LIMIT 10;
```
B19:
```sql
CREATE TABLE ridehailing.gps_ping (
  driver_id UUID,
  ping_time TIMESTAMP,
  lat DOUBLE,
  lon DOUBLE,
  PRIMARY KEY (driver_id, ping_time)
) WITH CLUSTERING ORDER BY (ping_time DESC)
  AND default_time_to_live = 2592000;
```

C20: Partition key = `customer_id`, clustering column = `trip_time DESC`. KHÔNG dùng `trip_id` làm partition key vì `trip_id` là khoá duy nhất từng dòng — mỗi partition sẽ chỉ có 1 dòng, không thể "lấy toàn bộ chuyến của 1 khách" bằng 1 lần đọc partition duy nhất (phải quét toàn cluster, vi phạm nguyên tắc bắt buộc WHERE có partition key hiệu quả).

C21: Vấn đề: partition `driver_id` phình to vô hạn theo năm tháng → wide partition, hot node, chậm dần. Khắc phục: thêm bucket vào partition key, ví dụ `PRIMARY KEY ((driver_id, year_month), trip_time)` — mỗi tháng 1 partition riêng, partition không bao giờ phình quá giới hạn.

D22: `ALLOW FILTERING` cho phép query không cần đúng partition key — Cassandra quét toàn bộ (hoặc nhiều) partition để lọc thủ công, mất hoàn toàn lợi thế phân tán theo hash, dễ timeout khi bảng lớn. Xuất hiện ở production nghĩa là mô hình bảng không khớp truy vấn thực tế — phải tạo bảng mới đúng theo truy vấn (query-first), không vá bằng `ALLOW FILTERING`.

D23: Secondary Index: Cassandra tự quản lý index phụ trên 1 cột non-key, tiện nhưng chỉ hiệu quả khi cardinality thấp và dữ liệu phân bố đều. Materialized View: Cassandra tự động duy trì 1 bảng phụ đã denormalize sẵn theo key khác, đọc nhanh như bảng gốc nhưng tốn ghi kép và có độ trễ đồng bộ. Dùng Secondary Index cho lọc phụ ít quan trọng; dùng Materialized View khi cần 1 access pattern đọc nhanh, ổn định, đã biết trước.

D24: LWT dùng giao thức Paxos (4 round-trip thay vì 1) để đảm bảo chỉ 1 trong nhiều ghi đồng thời thành công — đổi lại latency cao hơn nhiều lần ghi thường, chỉ nên dùng cho thao tác thật sự cần tính duy nhất.
```sql
CREATE TABLE ridehailing.trip_claim (
  trip_id UUID PRIMARY KEY,
  driver_id UUID,
  claimed_at TIMESTAMP
);

INSERT INTO ridehailing.trip_claim (trip_id, driver_id, claimed_at)
VALUES (<trip_id>, <driver_id>, toTimestamp(now()))
IF NOT EXISTS;
```
Nếu trip đã bị driver khác claim trước, lệnh trả `[applied] = false` — ứng dụng biết ngay chuyến đã có người nhận, không cần khoá riêng ở tầng ứng dụng.

---

## CHƯƠNG 4 — Neo4j

### A. Trắc nghiệm khái niệm

1. 3 thành phần cốt lõi mô hình dữ liệu Neo4j là gì?
 a) Table, Row, Column b) Node, Relationship, Property c) Document, Field, Index d) Key, Value, TTL

2. "Label" trong Neo4j tương đương khái niệm gì ở RDBMS?
 a) Primary key b) Tên bảng/kiểu thực thể (gắn nhãn phân loại cho node, 1 node có thể nhiều label) c) Foreign key d) Index

3. Relationship trong Neo4j có đặc điểm gì khác Node?
 a) Không thể có property b) Luôn có hướng (directed) và có thể mang property riêng c) Không thể tự liên kết 1 node với chính nó d) Bắt buộc phải vô hướng

4. "Index-free adjacency" nghĩa là gì?
 a) Neo4j không hỗ trợ index b) Mỗi node lưu con trỏ trực tiếp tới các quan hệ liên quan, duyệt đồ thị không cần tra index trung gian → traversal rất nhanh c) Không có ý nghĩa kỹ thuật d) Chỉ áp dụng cho node gốc

5. Ngôn ngữ truy vấn của Neo4j gọi là gì?
 a) GraphQL b) Cypher c) Gremlin d) SPARQL

6. Cypher là loại ngôn ngữ gì?
 a) Thủ tục (procedural), phải khai báo từng bước duyệt b) Khai báo (declarative) theo mẫu hình (pattern matching), giống SQL ở tinh thần "khai báo cái muốn lấy" c) Chỉ dùng để tạo dữ liệu, không truy vấn được d) Không phải ngôn ngữ truy vấn thật

7. Mệnh đề nào dùng để tìm mẫu hình (pattern) trong Cypher?
 a) `SEARCH` b) `MATCH` c) `FIND` d) `SCAN`

8. `MERGE` trong Cypher khác `CREATE` ở điểm nào?
 a) Giống hệt nhau b) `MERGE` tạo mới nếu chưa tồn tại, khớp nếu đã tồn tại (tránh trùng lặp); `CREATE` luôn tạo mới dù đã tồn tại c) `CREATE` mới tránh trùng lặp d) `MERGE` chỉ dùng cho relationship

9. Cổng giao tiếp mặc định (Bolt protocol) của Neo4j là?
 a) 7474 b) 7687 c) 5432 d) 27017

10. Trong bài toán đặt xe, quan hệ nào sau đây hợp lý biểu diễn bằng Graph DB (Neo4j) hơn hẳn so với Cassandra?
 a) Lưu GPS ping tần suất cao
 b) Mạng lưới giới thiệu (referral) khách hàng, hoặc gợi ý tài xế/điểm đến qua nhiều bước quan hệ
 c) Lưu log không đổi theo thời gian
 d) Lưu cấu hình hệ thống

### B. Viết lệnh (Cypher)

11. Viết Cypher tạo 1 node Person có label `Driver`, property `name = "Binh"`, `rating = 4.9`.

12. Viết Cypher tạo quan hệ `:COMPLETED` có property `fare = 45000` từ node `Driver` tới node `Trip`.

13. Viết Cypher tìm tất cả `Trip` mà 1 `Driver` tên "Binh" đã hoàn thành, trả về `trip_id` và `fare`.

14. Viết Cypher xoá 1 node `Trip` cùng toàn bộ quan hệ gắn với nó (dùng `DETACH DELETE`).

### C. Tình huống/logic

15. Bài toán: hệ thống muốn gợi ý "khách hàng A và khách hàng B có thể quen nhau" dựa trên việc họ từng đi chung nhiều chuyến xe ghép (car-pooling) với nhau qua nhiều lớp trung gian. Vì sao Cassandra (column-family) rất khó làm truy vấn này, còn Neo4j lại tự nhiên phù hợp? Trả lời dựa trên bản chất JOIN nhiều tầng vs traversal đồ thị.

### D. Nâng cao

16. Viết Cypher tìm đường đi ngắn nhất (shortest path) giữa 2 tài xế qua các chuyến ghép chung, giới hạn tối đa 6 bước.

17. Vì sao truy vấn traversal không giới hạn độ sâu (ví dụ `[*]` không chặn số bước) là nguy hiểm trên đồ thị lớn?

18. APOC là gì? Vì sao gần như bắt buộc dùng cho bài toán đồ thị thực tế (gợi ý: PageRank, community detection không có sẵn trong Cypher thuần)?

### Đáp án chương 4

A: 1b 2b 3b 4b 5b 6b 7b 8b 9b 10b

B11: `CREATE (d:Driver {name: "Binh", rating: 4.9})`
B12: `MATCH (d:Driver {name:"Binh"}), (t:Trip {trip_id: "T1"}) CREATE (d)-[:COMPLETED {fare: 45000}]->(t)`
B13:
```cypher
MATCH (d:Driver {name: "Binh"})-[:COMPLETED]->(t:Trip)
RETURN t.trip_id, t.fare
```
B14: `MATCH (t:Trip {trip_id: "T1"}) DETACH DELETE t`

C15: Truy vấn này là bài toán **duyệt nhiều bước quan hệ (multi-hop traversal)** — "bạn của bạn của bạn". Trong Cassandra, mỗi bước quan hệ là 1 bảng phi chuẩn hoá riêng, muốn đi qua N bước phải tự JOIN thủ công ở tầng ứng dụng N lần, chi phí tăng theo cấp số nhân và không có cách CQL nào biểu diễn trực tiếp. Neo4j nhờ index-free adjacency, mỗi node giữ sẵn con trỏ tới quan hệ lân cận — Cypher `MATCH (a)-[*1..3]-(b)` duyệt thẳng nhiều bước trong 1 câu lệnh, chi phí gần như không phụ thuộc kích thước toàn đồ thị mà chỉ phụ thuộc số quan hệ cục bộ.

D16:
```cypher
MATCH p = shortestPath((a:Driver {name:"Binh"})-[*..6]-(b:Driver {name:"An"}))
RETURN p
```
Giới hạn `*..6` bắt buộc phải có, không thì Cypher cố duyệt hết mọi đường đi có thể.

D17: Không giới hạn độ sâu khiến Cypher duyệt bùng nổ tổ hợp (combinatorial explosion) trên đồ thị dày đặc — số đường đi tăng theo cấp số nhân với độ sâu, dễ treo query hoặc hết RAM chỉ với vài chục nghìn node.

D18: APOC (Awesome Procedures on Cypher) là thư viện plugin bổ sung hàng trăm procedure — đường đi có trọng số, PageRank, community detection, xử lý JSON/CSV... — mà Cypher thuần không có sẵn. Hầu hết bài toán đồ thị thực tế (gợi ý bạn bè, phát hiện cụm, xếp hạng ảnh hưởng) đều cần cài APOC mới đủ công cụ phân tích.

---

## CHƯƠNG 5 — Redis

### A. Trắc nghiệm khái niệm

*(Nguồn: tổng hợp có chọn lọc từ bộ 50 MCQ Redis — javaguides.net, đối chiếu lại đúng chuẩn Redis chính thức)*

1. Redis là loại database gì?
 a) Relational b) NoSQL, mô hình chính là Key-Value (in-memory) c) Graph d) Document

2. Redis lưu dữ liệu chủ yếu ở đâu, khác Cassandra/MongoDB/Neo4j ở điểm nào?
 a) Trên đĩa hoàn toàn giống các DB khác
 b) Chủ yếu trong RAM (in-memory), có tuỳ chọn ghi xuống đĩa để bền vững (persistence) — nên cực nhanh nhưng giới hạn bởi dung lượng RAM
 c) Chỉ lưu tạm, luôn mất dữ liệu khi tắt máy, không có cách nào lưu bền
 d) Redis không lưu dữ liệu, chỉ forward request

3. Cổng mặc định của Redis là?
 a) 6379 b) 6380 c) 8080 d) 27017

4. Redis hỗ trợ những kiểu dữ liệu chính nào?
 a) Chỉ String b) String, List, Hash, Set, Sorted Set c) Chỉ Key-Value đơn giản không có kiểu con d) Document, Array, Object

5. Lệnh `EXPIRE key 60` làm gì?
 a) Xoá key ngay lập tức b) Đặt key tự hết hạn (bị xoá) sau 60 giây c) Giới hạn key chỉ đọc được 60 lần d) Đổi tên key

6. Lệnh nào lấy phần tử ra khỏi đầu 1 List?
 a) `RPOP` b) `LPOP` c) `HPOP` d) `SPOP`

7. `SADD` thao tác trên kiểu dữ liệu nào?
 a) List b) Hash c) Set d) String

8. `HSET`/`HGETALL` thao tác trên kiểu dữ liệu nào, phù hợp biểu diễn cái gì?
 a) List, biểu diễn hàng đợi b) Hash, biểu diễn 1 object có nhiều field (giống 1 document nhỏ) c) Set, biểu diễn phần tử duy nhất d) Sorted Set, biểu diễn bảng xếp hạng

9. Sorted Set (`ZADD`, `ZRANGE`) khác Set thường ở điểm nào, dùng tốt cho bài toán nào?
 a) Không khác gì Set thường
 b) Mỗi phần tử có thêm 1 "score" để sắp xếp — hợp cho bảng xếp hạng tài xế gần nhất theo khoảng cách/ETA
 c) Chỉ lưu được số nguyên
 d) Không hỗ trợ trùng lặp giá trị

10. 2 cơ chế persistence (lưu bền) chính của Redis là gì?
 a) Chỉ có RDB b) RDB (snapshot định kỳ) và AOF (append-only log mọi lệnh ghi) c) Chỉ có AOF d) Redis không có persistence

11. Redis Pub/Sub dùng để làm gì?
 a) Backup dữ liệu b) Cơ chế publish/subscribe — gửi message realtime tới các client đang subscribe kênh, hợp cho thông báo tức thời (vd. thông báo tài xế được ghép chuyến) c) Mã hoá dữ liệu d) Tạo index

12. Trong bài toán đặt xe, use-case nào Redis phù hợp NHẤT (so với Cassandra)?
 a) Lưu vĩnh viễn lịch sử toàn bộ chuyến đi nhiều năm
 b) Cache vị trí tài xế realtime (cập nhật liên tục, cần đọc/ghi cực nhanh, có thể mất khi restart không nghiêm trọng)
 c) Lưu quan hệ đồ thị nhiều tầng
 d) Lưu file ảnh giấy tờ tài xế

### B. Viết lệnh

13. Viết lệnh Redis lưu vị trí hiện tại của tài xế `driver:123` dạng Hash gồm `lat`, `lon`, `updated_at`.

14. Viết lệnh Redis đặt TTL 30 giây cho key vị trí tài xế ở câu 13 (vị trí quá cũ tự động coi như offline).

15. Viết lệnh Redis dùng Sorted Set `nearby_drivers` để thêm tài xế `123` với score là khoảng cách `2.5` (km) tới khách, sau đó lấy 5 tài xế gần nhất.

### C. Tình huống/logic

16. So sánh: vì sao KHÔNG nên dùng Cassandra để lưu vị trí realtime cập nhật mỗi giây của hàng chục nghìn tài xế đang chạy (mà nên dùng Redis cho phần này, Cassandra chỉ lưu lịch sử GPS đã "nguội")? Gợi ý: tốc độ ghi/đọc, có cần bền vững lâu dài không, chi phí xoá dữ liệu cũ liên tục (tombstone) ở Cassandra.

### D. Nâng cao

17. Redis Cluster chia dữ liệu bằng cơ chế gì? Có tổng cộng bao nhiêu hash slot cố định?

18. Vì sao từng lệnh đơn lẻ trong Redis luôn atomic, nhưng khối `MULTI/EXEC` (transaction) lại KHÔNG rollback được khi 1 lệnh giữa chừng "thành công cú pháp" mà sai logic nghiệp vụ?

19. Nêu 1 tình huống mà Lua script (`EVAL`) trong Redis giải quyết gọn còn `MULTI/EXEC` thường không giải quyết được (gợi ý: đọc-rồi-ghi có điều kiện, kiểu "chỉ trừ tiền nếu đủ số dư").

### Đáp án chương 5

A: 1b 2b 3a 4b 5b 6b 7c 8b 9b 10b 11b 12b

B13: `HSET driver:123 lat 10.7769 lon 106.7009 updated_at 1755000000`
B14: `EXPIRE driver:123 30`
B15:
```
ZADD nearby_drivers 2.5 "123"
ZRANGE nearby_drivers 0 4 WITHSCORES
```

C16: Vị trí tài xế đổi liên tục mỗi giây → nếu ghi vào Cassandra, mỗi lần "cập nhật" thực chất phải ghi dòng mới rồi dòng cũ trở thành rác cần tombstone/compaction dọn liên tục, tốn tài nguyên vô ích cho dữ liệu chỉ cần đúng lúc hiện tại. Redis lưu thẳng trong RAM, `HSET` ghi đè tại chỗ (không tích tombstone), đọc/ghi độ trễ dưới mili-giây, và nếu mất do restart cũng không nghiêm trọng vì vị trí sẽ được tài xế gửi lại ngay giây sau. Cassandra chỉ nên giữ vai trò lưu **lịch sử** GPS ping đã chốt (dùng cho phân tích/heatmap), không phải vị trí sống.

D17: Redis Cluster chia không gian key thành **16384 (2^14) hash slot** cố định, mỗi node phụ trách 1 dải slot; key được gán slot qua `CRC16(key) mod 16384`.

D18: Redis thực thi từng lệnh đơn lẻ atomic nhờ kiến trúc single-thread (không lệnh nào chen ngang lệnh khác). Nhưng `MULTI/EXEC` chỉ đảm bảo cả khối lệnh chạy liền mạch không bị chen ngang — nó không hiểu và không kiểm tra logic nghiệp vụ giữa các lệnh, cũng không có cơ chế rollback tự động nếu 1 lệnh chạy đúng cú pháp nhưng kết quả sai ý muốn (Redis không phải RDBMS, không có khái niệm "transaction thất bại thì huỷ toàn bộ").

D19: Ví dụ "chỉ trừ số dư ví nếu số dư hiện tại đủ" — cần đọc giá trị, so sánh điều kiện, rồi mới ghi, tất cả phải atomic. `MULTI/EXEC` không đọc được giá trị giữa chừng để quyết định có nên EXEC hay không (phải dùng thêm `WATCH` phức tạp, vẫn có thể retry). Lua script (`EVAL`) chạy nguyên khối trên server — đọc, tính điều kiện rẽ nhánh, ghi — tất cả trong 1 lần round-trip, atomic hoàn toàn kể cả logic có điều kiện.

---

## Nguồn tham khảo mở rộng đã dùng để xây bộ đề này

**Nguồn quốc tế (có nội dung câu hỏi/khái niệm cụ thể, đã đối chiếu):**
- Redis 50 MCQ: [javaguides.net – Redis Quiz 50 MCQ](https://www.javaguides.net/2024/08/redis-quiz-50-mcq-questions-and-answers.html)
- CAP Theorem 15 câu hỏi phỏng vấn: [Devinterview-io/cap-theorem-interview-questions](https://github.com/Devinterview-io/cap-theorem-interview-questions)
- MongoDB CRUD quiz: [GeeksforGeeks – MongoDB CRUD Operations Quiz](https://www.geeksforgeeks.org/quizzes/mongodb-crud-operations-quiz-questions/)
- MongoDB MCQ tổng hợp (1000+ câu): [Sanfoundry MongoDB Q&A](https://www.sanfoundry.com/1000-mongodb-questions-answers/)
- Cassandra partition/clustering key: [Baeldung – Cassandra Keys](https://www.baeldung.com/cassandra-keys), [ScyllaDB Glossary – Partition Key](https://www.scylladb.com/glossary/cassandra-partition-key/), [ScyllaDB Glossary – Clustering Key](https://www.scylladb.com/glossary/cassandra-clustering-key/)
- Neo4j 80 câu hỏi certification mẫu: [Glitchdata Neo4j Sample Questions 1-5](https://wiki.glitchdata.com/index.php/Neo4J:_Sample_Questions_1) (và Sample_Questions_2/3/4/5)
- Neo4j MCQ: [IncludeHelp Neo4j MCQs](https://www.includehelp.com/mcq/neo4j-mcqs.aspx), [Freshersnow Neo4j MCQs](https://www.freshersnow.com/neo4j-mcqs-and-answers-with-explanation/)
- NoSQL/CAP tổng quan: [ScyllaDB Glossary – CAP Theorem](https://www.scylladb.com/glossary/cap-theorem/), [JavaInUse NoSQL Quiz](https://www.javainuse.com/quiz/nosql)

**Nguồn trường đại học Việt Nam (tìm được, mức độ liên quan khác nhau — đọc thêm để đối chiếu văn phong đề thi thật, KHÔNG chép nguyên):**
- Bách Khoa Hà Nội — trắc nghiệm Big Data/NoSQL: [docx.com.vn – BT trắc nghiệm BigData](https://docx.com.vn/tai-lieu/bt-trac-nghiem-bigdata-va-dap-an-mon-luu-tru-va-xu-ly-du-lieu-lon-truo-118901), [Studocu – Bigdata Exam Hadoop and NoSQL](https://www.studocu.vn/vn/document/truong-dai-hoc-bach-khoa-ha-noi/big-data-storage-and-processing/bigdata-exam-exam/115130488)
- UIT — khoá luận NoSQL/MongoDB: [Studocu – Tìm hiểu NoSQL, MongoDB, UIT](https://www.studocu.vn/vn/document/truong-dai-hoc-cong-nghe-thong-tin-dai-hoc-quoc-gia-thanh-pho-ho-chi-minh/khoa-luan-tot-nghiep/tim-hieu-nosql-mongodb-va-xay-dung-ung-dung-minh-hoa/67734353)
- Học viện Bưu chính Viễn thông — bộ đề trắc nghiệm CSDL SQL/NoSQL (65 câu): [Studocu – Bộ đề trắc nghiệm CSDL](https://www.studocu.vn/vn/document/hoc-vien-cong-nghe-buu-chinh-vien-thong/he-quan-tri-co-so-du-lieu/bo-de-trac-nghiem-co-so-du-lieu-sql-nosql-phan-a-b/147818717)
- HCMUS — kho tài liệu chung các môn CSDL (không tìm thấy đề NoSQL riêng, môn NoSQL độc lập có vẻ không phổ biến ở HCMUS): [cuuduongthancong.com – HCMUS](https://cuuduongthancong.com/u/dhkhtnhcm/dh-khoa-hoc-tu-nhien-hcm/hcmus)

**Lưu ý trung thực:** không tìm được đề thi/ngân hàng câu hỏi NoSQL CHÍNH THỨC công khai riêng của HCMUS/HCMUT/UIT (đa số khoá học NoSQL ở các trường này nằm lồng trong môn Big Data hoặc chỉ có khoá luận, không có đề thi công khai). Các câu hỏi tự soạn ở trên (phần lớn phần B và C của mỗi chương) được viết dựa trên đúng nội dung đề cương chi tiết môn 01201073 + đối chiếu khái niệm với các nguồn quốc tế kể trên, không sao chép nguyên văn từ đâu.
