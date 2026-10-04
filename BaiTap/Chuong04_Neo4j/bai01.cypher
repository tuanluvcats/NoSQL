// Chương 4 - Neo4j - Bài 1
// Chạy: docker exec -it nosql-neo4j cypher-shell -u neo4j -p password123 -f /baitap/Chuong04_Neo4j/bai01.cypher

MATCH (n:SinhVien) DETACH DELETE n;

CREATE (a:SinhVien {mssv: '001', ten: 'An',   diem: 8.5})
CREATE (b:SinhVien {mssv: '002', ten: 'Binh', diem: 6.0})
CREATE (c:SinhVien {mssv: '003', ten: 'Chi',  diem: 9.2})
CREATE (a)-[:BAN_VOI]->(b)
CREATE (b)-[:BAN_VOI]->(c);

MATCH (s:SinhVien)-[:BAN_VOI]->(ban:SinhVien)
RETURN s.ten AS sinhvien, ban.ten AS ban_cua;
