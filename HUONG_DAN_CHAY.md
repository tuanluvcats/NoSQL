# Hướng dẫn chạy môi trường thực hành NoSQL

Môi trường này dựng 4 cơ sở dữ liệu trong giáo án bằng Docker, không cần cài riêng từng phần mềm lên máy.

## Yêu cầu

- Docker Desktop (Windows). Cài xong nhớ bật, biểu tượng cá voi ở khay hệ thống phải xanh.
- RAM: bật cả 4 dịch vụ cần khoảng 6–8 GB. Máy ít RAM thì chỉ bật dịch vụ của chương đang học.

---

## Phần 1 — Khởi động

### Mỗi lần ngồi vào học

1. Mở Docker Desktop, chờ biểu tượng cá voi chuyển xanh.
2. Mở PowerShell, vào thư mục này:

   ```powershell
   cd D:\Documents\Homework\Nam4\NoSQL
   ```

3. Bật cơ sở dữ liệu:

   ```powershell
   docker compose up -d              # bật cả 4
   docker compose up -d mongo        # hoặc chỉ bật 1 cái đang học
   ```

4. Kiểm tra:

   ```powershell
   docker compose ps
   ```

   Cột `STATUS` phải là `Up`. Riêng Cassandra mất khoảng 60–90 giây mới nhận kết nối dù đã hiện `Up` — nếu `cqlsh` báo lỗi kết nối thì chờ thêm rồi thử lại.

### Khi học xong

```powershell
docker compose stop
```

Dữ liệu vẫn còn. Lần sau `docker compose up -d` là học tiếp, không mất gì.

---

## Phần 2 — Làm bài tập ở đâu

Viết bài tập vào thư mục `BaiTap/`, chia theo chương:

```
BaiTap/
├── Chuong02_MongoDB/    bai01.js       ← JavaScript cho mongosh
├── Chuong03_Cassandra/  bai01.cql      ← CQL
├── Chuong04_Neo4j/      bai01.cypher   ← Cypher
└── Chuong05_Redis/      bai01.redis    ← lệnh redis-cli
```

Thư mục `BaiTap/` trên máy được gắn vào cả 4 container ở đường dẫn `/baitap`. Nghĩa là: sửa file bằng VS Code trên máy, chạy ngay trong container, không cần copy.

Mỗi chương đã có sẵn `bai01` làm mẫu. Bài mới thì tạo `bai02.js`, `bai03.js`... trong đúng thư mục chương.

### Chạy file bài tập

| Chương | Lệnh (chạy trong PowerShell tại thư mục này) |
|--------|----------------------------------------------|
| 2 — MongoDB | `docker exec -it nosql-mongo mongosh /baitap/Chuong02_MongoDB/bai01.js` |
| 3 — Cassandra | `docker exec -it nosql-cassandra cqlsh -f /baitap/Chuong03_Cassandra/bai01.cql` |
| 4 — Neo4j | `docker exec -it nosql-neo4j cypher-shell -u neo4j -p password123 -f /baitap/Chuong04_Neo4j/bai01.cypher` |
| 5 — Redis | `docker exec -i nosql-redis sh -c "redis-cli < /baitap/Chuong05_Redis/bai01.redis"` |

Quy trình quen tay: sửa file trong VS Code → lưu → nhấn mũi tên lên trong PowerShell → Enter → xem kết quả. Sai thì sửa file rồi chạy lại.

### Gõ trực tiếp để thử nhanh

Khi muốn thử một câu lệnh chứ chưa cần lưu file, vào shell tương tác:

| Chương | Lệnh vào shell |
|--------|----------------|
| 2 — MongoDB | `docker exec -it nosql-mongo mongosh` |
| 3 — Cassandra | `docker exec -it nosql-cassandra cqlsh` |
| 4 — Neo4j | `docker exec -it nosql-neo4j cypher-shell -u neo4j -p password123` |
| 5 — Redis | `docker exec -it nosql-redis redis-cli` |

Thoát shell: gõ `exit` (Redis và Cassandra dùng `quit`), hoặc `Ctrl+D`.

Lưu ý: lệnh gõ trong shell không được lưu lại. Câu nào chạy đúng thì chép vào file trong `BaiTap/` để còn nộp bài và ôn lại.

### Neo4j có giao diện đồ hoạ

Mở trình duyệt: http://localhost:7474 — đăng nhập `neo4j` / `password123`.

Giao diện này vẽ được đồ thị nên chương 4 dùng nó dễ nhìn hơn shell. Nhưng câu Cypher chạy đúng vẫn nên chép về file `.cypher` trong `BaiTap/Chuong04_Neo4j/`.

---

## Phần 3 — Kết nối từ code

Dùng khi viết Python/Java/Node cho đồ án cuối kỳ:

- MongoDB: `mongodb://localhost:27017`
- Cassandra: `localhost:9042`
- Neo4j: `bolt://localhost:7687` (user `neo4j`, pass `password123`)
- Redis: `localhost:6379`

---

## Phần 4 — Xử lý sự cố

| Triệu chứng | Cách xử lý |
|-------------|-----------|
| `error during connect... docker daemon` | Docker Desktop chưa bật. Mở lên, chờ cá voi xanh. |
| `Ports are not available: 27017` | Máy đã cài sẵn MongoDB/Redis chạy nền. Tắt service đó, hoặc đổi cổng trái trong `docker-compose.yml` (ví dụ `"27018:27017"`). |
| `cqlsh: connection refused` | Cassandra chưa khởi động xong. Chờ thêm 60 giây. Xem tiến độ: `docker compose logs -f cassandra`. |
| Cassandra tự tắt liên tục | Hết RAM. Tắt bớt dịch vụ khác: `docker compose stop neo4j`. |
| Muốn xoá sạch làm lại từ đầu | `docker compose down -v` rồi `docker compose up -d`. Lệnh này xoá toàn bộ dữ liệu trong cơ sở dữ liệu, file trong `BaiTap/` vẫn còn nguyên. |
| Chạy trong Git Bash thì báo `no such file /C:/Program Files/Git/baitap/...` | Git Bash tự đổi đường dẫn. Thêm `MSYS_NO_PATHCONV=1` trước lệnh, hoặc dùng PowerShell. |

---

## Ghi chú

- Mật khẩu `password123` chỉ dùng cho môi trường học tập trên máy cá nhân. Không dùng lại mật khẩu này khi triển khai thật.
- MongoDB, Cassandra, Redis ở đây chạy không bật xác thực để tiện thực hành. Chỉ an toàn vì cổng chỉ mở trên máy cục bộ.
- File mẫu `bai01` của Cassandra và Neo4j có lệnh `DROP TABLE` / `DELETE` ở đầu để chạy lại nhiều lần không bị trùng dữ liệu. File Redis có `FLUSHDB` — lệnh này xoá sạch database Redis hiện tại, nhớ điều này khi tự viết bài mới.
