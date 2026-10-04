export const meta = {
  name: 'verify-prompt1-analysis',
  description: 'Fact-check the Prompt 1 draft evaluation and project direction (DbSchema + Cassandra ride-hailing) before writing CASSANDRA.MD',
  phases: [
    { title: 'Verify', detail: '4 parallel fact-checkers (draft text, screenshots, DbSchema, rubric consistency) + local checks of the precomputed Cassandra 4.1 and Python driver results' },
    { title: 'Design review', detail: 'query-first review of proposed tables against the real existing schema' },
    { title: 'Critic', detail: 'completeness critic: what Prompt 1 and the checkers missed' },
    { title: 'Skeptic', detail: 'try to refute every finding that changes the answer' },
  ],
}

const X = 'C:/Users/Yameow/AppData/Local/Temp/nosql_extract'
const DOCX = 'D:/Documents/Homework/NoSQL/DoAn/Báo cáo giữa kỳ NoSQL về DbSchema và Apache Cassandra.docx'
const RES = 'D:/Documents/Homework/NoSQL/.claude/workflows/results'

const CONTEXT = `CONTEXT. Vietnamese university course project (HUIT, NoSQL course, class 14DH), group of 3 students.
Topic: "Tìm hiểu công cụ DbSchema để quản trị và khai thác CSDL Cassandra – Quản lý dữ liệu đặt xe công nghệ" (ride-hailing booking data) plus a demo application.
In an earlier turn ("Prompt 1") an assistant graded the group's mid-term draft against the official rubric and proposed a direction. That answer is saved verbatim at ${X}/prompt1_answer.md. Your job is to FACT-CHECK it. Do not trust it.
Source files (UTF-8 text, already extracted): ${X}/rubric.txt (official rubric, verbatim), ${X}/YEUCAUDOAN.txt (project requirements), ${X}/chitiet.txt (course syllabus), ${X}/draft.txt (draft dump; paragraphs look like "[idx][StyleName] text", followed by tables and image/section info), ${X}/slide_cassandra.txt (course slides, Cassandra chapter), ${X}/book_datamodel.txt and ${X}/book_backup.txt (Cassandra: The Definitive Guide 3rd ed., data-modeling and maintenance/backup chapters), ${X}/book_toc.txt.
Original draft: ${DOCX} (35 inline images, 3 tables).
Environment: Windows 11, Git Bash, Python 3.12.7 with python-docx installed, cassandra-driver NOT installed, pdftotext available. Docker CLI is installed but the Docker daemon is NOT running: do not start it. D:/Documents/Homework/NoSQL/docker-compose.yml defines service cassandra: image cassandra:4.1, container nosql-cassandra, CASSANDRA_CLUSTER_NAME=NoSQLLab, port 9042, MAX_HEAP_SIZE=1G, single node.
RULES: the project folder D:/Documents/Homework/NoSQL is READ-ONLY (never create or modify files there). Scratch writes only under ${X}. Every verdict needs concrete evidence: file:line, command plus output, or URL plus quoted text. If you cannot verify, use verdict "unverifiable" (never guess). Verdict "missing" = something Prompt 1 should have said but did not. Verdict "correct" = the Prompt 1 statement holds. Write the "correction" field in Vietnamese. Use the id prefix given below for your finding ids (e.g. T1, T2...).
RESUME NOTE: an earlier run of these checks was interrupted before anyone returned results, but it left reusable artifacts under ${X} — list the folder first and REUSE them instead of redoing work: figs/ (images extracted from the .docx, figs/index.txt maps them to captions, figs/crops/ holds enlarged crops), extract_figs.py, docs41/ (Cassandra 4.1 docs as text), cassandra-4.1.yaml, NEWS-4.1.txt, docker-cassandra-4.1-Dockerfile, docker-cassandra-4.1-entrypoint.sh, web/ (downloaded pages; web/drv = DbSchema Cassandra JDBC driver source), changelog_*.rst, install_doc_*.rst, cluster_*.py, *reactor_3.30.1.py, pe_imports.py, probe*.txt, pipinst_*.txt, pypi_*.json, venv_probe/ (delete it when you are done if you use it). Budget: aim to finish in about 40 tool calls; return your structured output even if some checks must stay "unverifiable".
PRECOMPUTED: checkers 3 (cassandra-41, ids C*) and 4 (python-driver, ids P*) were completed in a separate cloud run that executed every check on a real Cassandra 4.1.12 node (image cassandra:4.1 with the docker-compose settings) and on Windows CPython 3.12.7 under Wine. Their results, method and raw evidence are in ${RES} (README.md, task3_cassandra-41.json, task4_python-driver.json, evidence/). Evidence paths written as "evidence/..." are relative to that folder, which is part of the read-only project folder.`

const FINDING = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    claim: { type: 'string', description: 'exact Prompt 1 statement checked (quoted), or "(missing)" for omissions' },
    verdict: { type: 'string', enum: ['correct', 'wrong', 'partly_wrong', 'unverifiable', 'missing'] },
    severity: { type: 'string', enum: ['high', 'medium', 'low'] },
    evidence: { type: 'string', description: 'file:line, command + output, or URL + quoted text' },
    correction: { type: 'string', description: 'Vietnamese: corrected statement or what to add' },
  },
  required: ['id', 'claim', 'verdict', 'severity', 'evidence', 'correction'],
}
const FACTS = { type: 'array', items: { type: 'string' }, description: 'verified facts useful for writing CASSANDRA.MD / the report, each with its source' }
const FINDINGS_SCHEMA = {
  type: 'object',
  properties: { findings: { type: 'array', items: FINDING }, facts_for_prompt2: FACTS },
  required: ['findings', 'facts_for_prompt2'],
}
const SHOTS_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: FINDING },
    facts_for_prompt2: FACTS,
    figures: {
      type: 'array',
      items: {
        type: 'object',
        properties: { file: { type: 'string' }, caption: { type: 'string' }, what_it_shows: { type: 'string' } },
        required: ['file', 'caption', 'what_it_shows'],
      },
    },
    existing_schema: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          table: { type: 'string' },
          columns: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                cql_type: { type: 'string' },
                role: { type: 'string', description: 'partition_key | clustering_asc | clustering_desc | static | regular | unknown' },
              },
              required: ['name', 'cql_type', 'role'],
            },
          },
          primary_key_cql: { type: 'string', description: 'reconstructed PRIMARY KEY clause, or "unknown"' },
          evidence_figures: { type: 'string' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['table', 'columns', 'primary_key_cql', 'evidence_figures', 'confidence'],
      },
    },
    environment: {
      type: 'object',
      properties: {
        cassandra_version: { type: 'string' },
        datacenter: { type: 'string' },
        host_port: { type: 'string' },
        runs_in: { type: 'string', description: 'docker | native | unknown, with evidence' },
        dbschema_version_edition: { type: 'string' },
      },
      required: ['cassandra_version', 'datacenter', 'host_port', 'runs_in', 'dbschema_version_edition'],
    },
  },
  required: ['findings', 'facts_for_prompt2', 'figures', 'existing_schema', 'environment'],
}
const VERDICTS_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          upheld: { type: 'boolean' },
          reason: { type: 'string' },
          adjusted_correction: { type: 'string', description: 'Vietnamese; empty string if the correction stands' },
        },
        required: ['id', 'upheld', 'reason', 'adjusted_correction'],
      },
    },
  },
  required: ['verdicts'],
}

// ==== PRECOMPUTED RESULTS: BEGIN (generated by results/sync_precomputed.py from results/task3_cassandra-41.json and results/task4_python-driver.json; do not edit by hand) ====
const PRE3 = {
  findings: [
    {"id": "C1", "claim": "\"Materialized View bị tắt mặc định\" (Cassandra 4.1)", "verdict": "correct", "severity": "medium", "evidence": "conf/cassandra.yaml 4.1 line 1732-1733: \"# Materialized views are considered experimental and are not recommended for production use.\" / \"materialized_views_enabled: false\" (https://github.com/apache/cassandra/blob/cassandra-4.1/conf/cassandra.yaml#L1732-L1733). Run: CREATE MATERIALIZED VIEW ... -> evidence/t3_probe.out:1 \"Materialized views are disabled. Enable in cassandra.yaml to use.\" NEWS.txt (4.0 section) line 591-594: flags \"have been set as false by default\" (CASSANDRA-14866). docker-entrypoint.sh 4.1 lines 66-91 only rewrite broadcast_address, broadcast_rpc_address, cluster_name, endpoint_snitch, listen_address, num_tokens, rpc_address, start_rpc and dc/rack -> no env var for MV. Mounting a cassandra.yaml with materialized_views_enabled: true works: evidence/t3_auth_check.out:25 view rides_by_status exists; cqlsh printed \"Materialized views are experimental and are not recommended for production use.\"", "correction": "Đúng. Khóa cấu hình ở 4.1 là materialized_views_enabled (ở 4.0 tên là enable_materialized_views), mặc định false. Image Docker không có biến môi trường để bật MV: muốn bật phải mount file cassandra.yaml đã sửa vào /etc/cassandra/cassandra.yaml (đã thử, chạy được). Khi tạo MV, Cassandra cảnh báo đây là tính năng thử nghiệm, không khuyến nghị cho production. Với đồ án nên dùng bảng phi chuẩn hóa + BATCH làm giải pháp chính; MV chỉ nên nêu như một tính năng có hạn chế."},
    {"id": "C2", "claim": "\"chưa có SAI (phải lên 5.0)\"", "verdict": "correct", "severity": "low", "evidence": "NEWS.txt cassandra-5.0 line 185-186: \"Added a new secondary index implementation, Storage-Attached Indexes (SAI).\" (https://github.com/apache/cassandra/blob/cassandra-5.0/NEWS.txt#L185). On 4.1.12: evidence/t3_index_gcgrace.out \"Unable to find custom indexer class 'org.apache.cassandra.index.sai.StorageAttachedIndex'\". SASI: cassandra.yaml line 1736-1737 \"SASI indexes are considered experimental\" / \"sasi_indexes_enabled: false\"; run -> \"SASI indexes are disabled. Enable in cassandra.yaml to use.\" (evidence/t3_probe.out:3). Ordinary secondary index works: CREATE INDEX rides_status_2i succeeded, system_schema.indexes kind COMPOSITES (evidence/t3_index_gcgrace.out).", "correction": "Đúng: SAI chỉ có từ Cassandra 5.0. Bổ sung: 4.1 có sẵn secondary index thường (CREATE INDEX ... ON bảng(cột)) dùng được ngay để minh họa truy vấn theo cột không phải khóa; SASI có trong 4.1 nhưng là tính năng thử nghiệm và bị tắt mặc định (sasi_indexes_enabled: false)."},
    {"id": "C3", "claim": "\"UDF cũng tắt mặc định\"", "verdict": "correct", "severity": "low", "evidence": "cassandra.yaml 4.1 line 1514 \"user_defined_functions_enabled: false\", line 1520 \"scripted_user_defined_functions_enabled: false\". Run CREATE FUNCTION ... LANGUAGE java -> evidence/t3_probe.out:4 \"User-defined functions are disabled in cassandra.yaml - set user_defined_functions_enabled=true to enable\".", "correction": "Đúng. Khóa là user_defined_functions_enabled (UDF Java) và scripted_user_defined_functions_enabled (UDF JavaScript), cả hai mặc định false; bật cũng phải mount cassandra.yaml. Các hàm tổng hợp có sẵn COUNT/SUM/AVG/MIN/MAX không cần UDF."},
    {"id": "C4", "claim": "[theo workflow] Dùng hàm tổng hợp COUNT/SUM/AVG/MIN/MAX với GROUP BY cho truy vấn nâng cao trên 4.1", "verdict": "correct", "severity": "medium", "evidence": "evidence/t3_probe.out:6-11 GROUP BY customer_id returns COUNT/SUM/AVG/MIN/MAX per partition, with warning line 13-14 \"Aggregation query used without partition key\". Restrictions: line 24 \"Group by is currently only supported on the columns of the PRIMARY KEY, got status\"; line 25 \"Group by currently only support groups of columns following their declared order in the PRIMARY KEY\". doc cql/dml.adoc (4.1) line 187-189: \"the GROUP BY option only accepts primary key columns in defined order\". Time buckets: NEWS.txt 4.1 section line 171-172 \"Add floor functions that can be use to group by time range\"; run GROUP BY customer_id, floor(booked_at, 1d) works (t3_probe.out:27-32). AVG on bigint is integer division: t3_probe.out:34-36 avg(fare)=46333 vs avg(cast(fare as double))=46333.33333.", "correction": "Đúng, nhưng cần ghi rõ ràng buộc: GROUP BY chỉ nhận cột khóa chính theo đúng thứ tự khai báo (partition key trước, rồi tiền tố clustering); không GROUP BY được theo cột thường như status. Từ 4.1 có thể nhóm theo khoảng thời gian bằng floor(cột_timestamp, 1d) ở cột cuối của GROUP BY. AVG trên cột số nguyên (int/bigint) chia lấy phần nguyên, muốn có số lẻ phải CAST sang double/decimal. Truy vấn tổng hợp không chỉ định partition key sẽ quét toàn bảng (Cassandra cảnh báo) — trong đồ án nên luôn lọc theo partition key."},
    {"id": "C5", "claim": "[theo workflow] PER PARTITION LIMIT; phân trang bằng token(); ALLOW FILTERING", "verdict": "correct", "severity": "low", "evidence": "evidence/t3_probe.out:40-45 PER PARTITION LIMIT 1 returns the newest ride of each customer (clustering booked_at DESC). Line 47-52 token(customer_id): CUST002=3949864281515454340 < CUST001=4430528727449596840, so WHERE token(customer_id) > token('CUST001') returns 0 rows (line 54-58): order follows the token, not the key text. Line 59: query on regular column without ALLOW FILTERING rejected (\"Cannot execute this query as it might involve data filtering...\"); with ALLOW FILTERING it runs (61-67). doc cql/dml.adoc line 222: \"The ALLOW FILTERING option explicitly executes a full scan.\"", "correction": "Đúng. Khi viết báo cáo cần giải thích: thứ tự duyệt theo token() là thứ tự giá trị băm Murmur3, không phải thứ tự chữ cái của khóa; ALLOW FILTERING là quét toàn bộ (hoặc toàn partition), chỉ chấp nhận khi đã giới hạn trong một partition hoặc dữ liệu nhỏ."},
    {"id": "C6", "claim": "[theo workflow] LWT: INSERT ... IF NOT EXISTS; UPDATE ... IF status='REQUESTED' (nhận cuốc); serial consistency", "verdict": "correct", "severity": "medium", "evidence": "evidence/t3_probe.out:76-82 INSERT IF NOT EXISTS -> [applied] True, second insert -> False and returns the existing row. Line 84-90: UPDATE rides SET driver_id='DRV01', status='ACCEPTED' ... IF status='REQUESTED' -> True; the same update by DRV02 -> False, status ACCEPTED (race for accepting a ride handled). Line 91 SERIAL CONSISTENCY LOCAL_SERIAL accepted; line 93-95 condition on two regular columns works. Line 96: \"Batch with conditions cannot span multiple partitions\". Line 117: \"Conditional updates are not supported on counter tables\". Cost: cql/dml.adoc (4.1) line 292-293 \"IF NOT EXISTS will incur a non-negligible performance cost, because Paxos is used\"; Cassandra: The Definitive Guide 3rd ed. (TaiLieuThamKhao/[4]), section \"Lightweight Transactions and Paxos\": \"a successful transaction requires four round-trips between the coordinator node and replicas\".", "correction": "Đúng. Bổ sung: điều kiện IF được đặt trên cột thường (status) là hợp lệ và chính là cách chống hai tài xế cùng nhận một cuốc; BATCH có điều kiện IF chỉ được nằm trong một partition; không dùng LWT trên bảng counter; mỗi LWT tốn 4 vòng trao đổi Paxos nên chỉ dùng cho bước cần tranh chấp (đăng ký tài khoản, nhận cuốc), không dùng cho mọi ghi."},
    {"id": "C7", "claim": "[theo workflow] Cột static, set<text>, UDT, TTL, WRITETIME", "verdict": "correct", "severity": "low", "evidence": "evidence/t3_probe.out:97 \"Static columns are only useful (and thus allowed) if the table has at least one clustering column\". Line 99-104: static driver_name/vehicle_plate shared by every row of partition DRV01 after one UPDATE. Line 106-108: set<text> append, frozen UDT field access home.city, TTL(full_name)=3600, WRITETIME(full_name). Line 111: \"Cannot use selection function writeTime on non-frozen collection phones\"; cql/dml.adoc (4.1) line 88-89 \"The WRITETIME and TTL functions can't be used on multi-cell columns such as non-frozen collections\". This is only lifted in 5.0 (NEWS.txt cassandra-5.0 line 214-216).", "correction": "Đúng. Lưu ý khi minh họa: cột static bắt buộc bảng có clustering column; WRITETIME/TTL trong 4.1 không áp dụng được cho collection/UDT không frozen (chỉ 5.0 mới hỗ trợ), nên minh họa WRITETIME/TTL trên cột đơn (text, int...)."},
    {"id": "C8", "claim": "[theo workflow] Bảng counter revenue_by_day PRIMARY KEY ((city, yyyymm), day) để thống kê doanh thu (VND)", "verdict": "partly_wrong", "severity": "medium", "evidence": "Rules confirmed on 4.1.12 (evidence/t3_probe.out): line 112 \"Cannot mix counter and non counter columns in the same table\"; 113 \"INSERT statements are not allowed on counter tables, use UPDATE instead\"; 114 \"Cannot provide custom TTL for counter updates\"; 115 \"counters can only be incremented/decremented, not set\"; 116 \"Counter and non-counter mutations cannot exist in the same batch\"; 117 no LWT; 119-125 BEGIN COUNTER BATCH works. cql/types.adoc (4.1) line 58-60: counter is \"a 64-bit signed integer\"; line 74-77: deletion \"is only guaranteed to work the first time ... you should not re-update a counter that you have deleted\"; line 78-83: \"Counter updates are, by nature, not idempotent ... replaying the update may or may not lead to an over count.\"", "correction": "Bảng counter tạo được đúng như đề xuất, nhưng không nên dùng counter làm nguồn số liệu tiền: cập nhật counter không idempotent (timeout rồi thử lại có thể cộng trùng), không đặt lại được giá trị, không có TTL, không dùng chung BATCH với bảng thường nên không thể ghi nguyên tử cùng bản ghi chuyến đi. Đề xuất: dùng counter cho số chuyến (ride_count) để minh họa kiểu counter; doanh thu lấy từ bảng thanh toán thường (ví dụ payments_by_city_day với cột amount bigint) bằng SUM(...) GROUP BY trong một partition, hoặc lưu bigint thường do ứng dụng tính lại. VND là số nguyên nên bigint đủ, không cần decimal. Nếu giữ counter cho doanh thu thì phải nêu hạn chế này trong báo cáo."},
    {"id": "C9", "claim": "[theo workflow] Bảng driver_locations PRIMARY KEY ((driver_id), ts DESC) với TTL 1 ngày", "verdict": "partly_wrong", "severity": "medium", "evidence": "compaction/index.adoc (4.1) line 178-187: \"Once the TTL has expired the data is converted to a tombstone which stays around for at least gc_grace_seconds ... if you mix data with TTL and data without TTL ... Cassandra will have a hard time dropping the tombstones\". Default gc_grace_seconds = 864000 (10 days) on 4.1.12 (evidence/t3_index_gcgrace.out). cassandra.yaml line 1563-1564 tombstone_warn_threshold 1000 / tombstone_failure_threshold 100000. compaction/twcs.adoc line 4-11: TWCS \"is designed specifically for workloads ... time-series in nature or when all data is written with a TTL\"; line 36-37 choose \"approximately 20-30 windows\" per TTL period. Tested alternative: PRIMARY KEY ((driver_id, day), ts) WITH CLUSTERING ORDER BY (ts DESC) AND default_time_to_live = 86400 AND compaction = TWCS HOURS/1 -> created, TTL(lat)=86400 applied automatically (t3_probe.out:127-129; t3_index_gcgrace.out shows the stored options).", "correction": "Khóa ((driver_id), ts DESC) làm partition của mỗi tài xế phình mãi (ví dụ gửi GPS 5 giây/lần = 17.280 dòng/ngày) và dòng hết hạn TTL thành tombstone, còn tồn tại ít nhất gc_grace_seconds (mặc định 10 ngày) trước khi bị dọn. Nên: (1) chia bucket theo ngày: PRIMARY KEY ((driver_id, day), ts) với CLUSTERING ORDER BY (ts DESC); (2) đặt default_time_to_live = 86400 ở mức bảng thay vì USING TTL từng câu, và không trộn dữ liệu có/không TTL; (3) dùng compaction TimeWindowCompactionStrategy (compaction_window_unit 'HOURS', compaction_window_size 1). Vị trí hiện tại của tài xế nên để ở bảng riêng khóa driver_id (ghi đè), không đọc từ lịch sử."},
    {"id": "C10", "claim": "[theo workflow] Bảng drivers_by_area PRIMARY KEY ((area, status), rating DESC, driver_id)", "verdict": "partly_wrong", "severity": "medium", "evidence": "evidence/t3_probe.out:132 UPDATE ... SET status -> \"PRIMARY KEY part status found in SET part\"; line 133 UPDATE ... SET rating -> \"PRIMARY KEY part rating found in SET part\". Moving a driver requires DELETE (old key, which needs the old rating value) + INSERT (new key) in a logged BATCH; tested: line 135-145 row moved from AVAILABLE to BUSY. cql/dml.adoc (4.1) line 452-453: \"There is a performance penalty for batch atomicity when a batch spans multiple partitions\".", "correction": "Thiết kế chạy được nhưng mỗi lần đổi trạng thái (rảnh/bận) hoặc đổi điểm đánh giá đều không UPDATE được mà phải DELETE dòng cũ + INSERT dòng mới trong BATCH có log, và phải đọc trước giá trị rating cũ để xóa đúng khóa. Partition (area, 'AVAILABLE') còn có thể thành điểm nóng. Đề xuất: bỏ rating khỏi clustering key (sắp xếp theo rating ở tầng ứng dụng vì số tài xế mỗi khu nhỏ), giữ status trong partition key chỉ khi chấp nhận DELETE+INSERT bằng BATCH và trình bày rõ đây là cái giá của thiết kế query-first; hoặc dùng ((area), driver_id) với status là cột thường."},
    {"id": "C11", "claim": "(missing) Datacenter mặc định, biến môi trường của image cassandra:4.1 và cấu hình xác thực để làm mục 'quản trị người dùng'", "verdict": "missing", "severity": "high", "evidence": "Default DC: SELECT data_center FROM system.local -> datacenter1; nodetool status \"Datacenter: datacenter1\" (container started from docker-compose settings). docker-entrypoint.sh 4.1 lines 66-91 (identical to https://github.com/docker-library/cassandra/blob/master/4.1/docker-entrypoint.sh). CASSANDRA_DC alone has no effect: container with CASSANDRA_DC=HCM and default SimpleSnitch -> cassandra-rackdc.properties \"dc= HCM\" but nodetool \"Datacenter: datacenter1\" (evidence/t3_auth_check.out:43,51-52); docker-library/docs cassandra/content.md line 89: \"You must set CASSANDRA_ENDPOINT_SNITCH to use the GossipingPropertyFileSnitch ... otherwise this variable will have no effect\". With CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch + CASSANDRA_DC=HCM -> \"Datacenter: HCM\" (t3_auth_check.out:35). Auth: cassandra.yaml line 169 \"authenticator: AllowAllAuthenticator\", line 178 \"authorizer: AllowAllAuthorizer\"; on the default setup CREATE ROLE ... WITH PASSWORD -> \"CassandraRoleManager doesn't support PASSWORD\", CREATE ROLE/GRANT/LIST ROLES -> \"You have to be logged in and not anonymous\" (t3_probe.out:146-149). With a mounted yaml (authenticator: PasswordAuthenticator, authorizer: CassandraAuthorizer): anonymous login refused (t3_auth_check.out:2), superuser cassandra/cassandra creates roles app_admin/app_reader, GRANT SELECT works, app_reader INSERT -> \"User app_reader has no MODIFY permission\" (t3_auth_check.out:12,19,33). HUONG_DAN_CHAY.md line 126 states the lab runs without authentication.", "correction": "Cần bổ sung: (1) Với docker-compose hiện tại, tên datacenter là datacenter1 — đây là giá trị phải nhập vào ô DataCenter/local datacenter khi kết nối DbSchema và driver; CASSANDRA_DC chỉ có tác dụng khi đặt thêm CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch. (2) Image chỉ hỗ trợ các biến CASSANDRA_LISTEN_ADDRESS, BROADCAST_ADDRESS, BROADCAST_RPC_ADDRESS, RPC_ADDRESS, START_RPC, SEEDS, CLUSTER_NAME, NUM_TOKENS, ENDPOINT_SNITCH, DC, RACK; không có biến cho xác thực, MV, UDF. (3) Mặc định Cassandra không bật xác thực (AllowAllAuthenticator) nên CREATE ROLE ... WITH PASSWORD và GRANT đều lỗi. Muốn trình bày 'quản trị người dùng' bằng role/quyền của Cassandra phải mount cassandra.yaml đặt authenticator: PasswordAuthenticator và authorizer: CassandraAuthorizer, đăng nhập lần đầu bằng cassandra/cassandra rồi tạo role riêng; khi đó DbSchema và ứng dụng cũng phải khai báo user/password. Nếu không bật, phần người dùng chỉ có thể là tài khoản ở tầng ứng dụng."},
    {"id": "C12", "claim": "[theo workflow] Backup/Restore trên 4.1 bằng nodetool snapshot rồi khôi phục (snapshot + nodetool refresh / nodetool import / sstableloader; incremental_backups; clearsnapshot)", "verdict": "correct", "severity": "medium", "evidence": "All four restore paths executed on 4.1.12. (a) Snapshot -> import: evidence/t3_backup_restore.out: nodetool snapshot -t bk_drivers -kt probe.rides_by_driver (L14), listsnapshots (L15-19), TRUNCATE -> count 0 (L26) and automatic snapshot truncated-...-rides_by_driver (L42; cassandra.yaml L972 auto_snapshot: true), snapshot folder holds SSTables + manifest.json + schema.cql (L43-52), nodetool import -cd restores 2 rows (L53-61). (b) Incremental backup: evidence/t3_backup_restore2.out: nodetool statusbackup 'not running' (L3) -> enablebackup -> 'running' (L6); after INSERT + flush the table's backups/ folder holds hard links of the flushed SSTable (L16-24); TRUNCATE then nodetool import of those files restores all 5 rows (L25-38); disablebackup. (c) nodetool refresh: snapshot SSTables copied into the live table folder, `nodetool refresh` prints \"nodetool refresh is deprecated, use nodetool import instead\" (L63) but still loads them: count 0 -> 2 (L54, L68). (d) sstableloader -d <node ip> /tmp/loader/probe/customers (folder must end in <keyspace>/<table>): \"Total files transferred : 7\" (L115), customer row back with its set<text> (L125). (e) nodetool clearsnapshot -t bk_loader / --all -- probe, then listsnapshots \"There are no snapshots\" (L139-145). Docs: NEWS.txt (4.0 section) L390 \"nodetool refresh has been deprecated in favour of nodetool import\"; operating/bulk_loading.adoc L384-385; operating/backups.adoc L345-350 (schema.cql in every snapshot), L505-511 (restore tools: sstableloader, nodetool import); cassandra.yaml L960 incremental_backups: false. Tools present: /opt/cassandra/bin has cqlsh, nodetool, sstableloader (t3_backup_restore.out tail); /opt/cassandra/tools/bin (sstabledump, ...) exists but is not on PATH.", "correction": "Đúng hướng, và cả 4 cách khôi phục đều chạy được trên 4.1.12. Quy trình nên trình bày: DESCRIBE KEYSPACE ride_booking (sao lưu lược đồ) → nodetool flush → nodetool snapshot -t <tên> ride_booking → nodetool listsnapshots → (sự cố/TRUNCATE) → nodetool import ride_booking <bảng> <thư_mục_snapshot> (thêm -cd để copy thay vì move) → nodetool clearsnapshot -t <tên> -- ride_booking. Bổ sung: (1) incremental backup bật ngay bằng nodetool enablebackup (không cần sửa yaml), mỗi lần flush sẽ tạo hard link SSTable trong thư mục backups/ của bảng, khôi phục cũng bằng nodetool import; (2) nodetool refresh vẫn chạy nhưng đã deprecated từ 4.0, nên dùng nodetool import; (3) sstableloader stream SSTable qua cổng 7000 tới node, thư mục nguồn phải có dạng .../<keyspace>/<bảng>/; dùng khi khôi phục sang cụm khác. Lưu ý: TRUNCATE/DROP tự tạo snapshot 'truncated-...'/'dropped-...' do auto_snapshot: true. Trên Windows chạy qua docker exec nosql-cassandra nodetool ...; trong Git Bash cần MSYS_NO_PATHCONV=1 khi có đường dẫn."},
    {"id": "C13", "claim": "(missing) Giới hạn của cqlsh COPY TO/FROM khi dùng cho Import/Export", "verdict": "missing", "severity": "medium", "evidence": "evidence/t3_copy_ttl.out: row inserted USING TTL 86400 (line 5 TTL 86400) -> COPY TO csv -> TRUNCATE -> COPY FROM -> TTL null (line 26): TTL (and WRITETIME) are not preserved. COPY works for collections/UDT (customers round trip in evidence/t3_backup_restore.out L62-78, which also shows TTL(full_name) null after the round trip) and for counter tables (evidence/t3_copy_counter_help.out L11-17). operating/bulk_loading.adoc (4.1) line 7-8: \"Although the cqlsh COPY command can load CSV data, it is not a good option for amounts of data.\" HELP COPY (evidence/t3_copy_counter_help.out) lists options HEADER, DELIMITER, NULL, DATETIMEFORMAT, MAXATTEMPTS, CHUNKSIZE, INGESTRATE, MAXBATCHSIZE, MAXROWS, MAXPARSEERRORS, ERRFILE, TTL, PAGESIZE. COPY is a cqlsh shell command, not a CQL statement: tools/cqlsh.adoc (4.1) L126-129 \"Special Commands ... special commands that are not part of CQL\", COPY TO at L385.", "correction": "Cần bổ sung khi trình bày Import/Export: COPY là lệnh của cqlsh, không phải câu CQL, nên không chạy được qua driver Python hay trình soạn CQL của công cụ GUI; COPY không giữ TTL/WRITETIME (đã thử: TTL 86400 thành null sau khi nhập lại) — với bảng có TTL như khuyến mãi phải dùng tùy chọn WITH TTL=... khi COPY FROM; COPY phù hợp dữ liệu nhỏ/vừa của đồ án, dữ liệu lớn dùng sstableloader/nodetool import. Các tùy chọn nên minh họa: HEADER=true, DELIMITER, NULL, DATETIMEFORMAT, MAXROWS."},
    {"id": "C14", "claim": "\"Chạy 3 node cần khoảng 4–6 GB RAM\"", "verdict": "correct", "severity": "low", "evidence": "evidence/t3_memory.out: three cassandra:4.1 containers with MAX_HEAP_SIZE=1G use 1.223 GiB, 1.275 GiB, 1.274 GiB each when idle; JVM started with -Xms1G -Xmx1G -Xmn256M (heap is fully pre-allocated). operating/hardware.adoc (4.1) line 22-28: off-heap memory is used in addition to the heap; line 36: production heap \"no less than 2GB\".", "correction": "Hợp lý: mỗi node heap 1G chiếm khoảng 1,2–1,3 GB khi rảnh, 3 node ≈ 3,7–3,9 GB, cộng phần ảo hóa của Docker Desktop/WSL2 và tải thực tế thì 4–6 GB là ước lượng đúng. Ghi chú thêm: heap 1G chỉ dành cho môi trường học tập (tài liệu khuyến nghị tối thiểu 2 GB cho production), và mỗi node cần container riêng với CASSANDRA_SEEDS trỏ tới node đầu."},
    {"id": "C15", "claim": "(missing) Tag cassandra:4.1 là tag trôi (floating) — phiên bản vá thực tế thay đổi theo thời gian", "verdict": "missing", "severity": "low", "evidence": "docker image inspect cassandra:4.1 -> CASSANDRA_VERSION=4.1.12, Created 2026-10-02; cqlsh banner \"[cqlsh 6.1.0 | Cassandra 4.1.12 | CQL spec 3.4.6 | Native protocol v5]\". NEWS.txt cassandra-4.1 already lists a 4.1.13 section (line 54).", "correction": "Khi ghi phiên bản trong báo cáo nên ghi đúng bản vá đang chạy (lấy bằng SHOW VERSION hoặc SELECT release_version FROM system.local), và nếu muốn ảnh chụp và báo cáo khớp nhau lâu dài thì ghim tag cụ thể trong docker-compose (ví dụ cassandra:4.1.12) thay vì cassandra:4.1."},
  ],
  facts_for_prompt2: [
    "Image cassandra:4.1 hiện là Cassandra 4.1.12 (cqlsh 6.1.0, CQL spec 3.4.6, native protocol v5), chạy trên Temurin Java 11; tag 4.1 là tag trôi. Nguồn: evidence/t3_version.out.",
    "Với docker-compose.yml của repo (không đặt CASSANDRA_DC), datacenter là 'datacenter1', rack 'rack1', cluster_name 'NoSQLLab', snitch SimpleSnitch, num_tokens 16. Driver và DbSchema phải dùng local datacenter = datacenter1. Nguồn: evidence/t3_version.out; cassandra.yaml 4.1 L27, L1332.",
    "CASSANDRA_DC/CASSANDRA_RACK chỉ có hiệu lực khi đặt CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch. Nguồn: https://github.com/docker-library/docs/blob/master/cassandra/content.md L89; thử nghiệm evidence/t3_auth_check.out L35, L43, L51-52.",
    "Biến môi trường image hỗ trợ: CASSANDRA_LISTEN_ADDRESS, CASSANDRA_BROADCAST_ADDRESS, CASSANDRA_BROADCAST_RPC_ADDRESS, CASSANDRA_RPC_ADDRESS, CASSANDRA_START_RPC, CASSANDRA_SEEDS, CASSANDRA_CLUSTER_NAME, CASSANDRA_NUM_TOKENS, CASSANDRA_ENDPOINT_SNITCH, CASSANDRA_DC, CASSANDRA_RACK (+ MAX_HEAP_SIZE/HEAP_NEWSIZE qua cassandra-env.sh). Cấu hình khác phải mount /etc/cassandra/cassandra.yaml. Nguồn: https://github.com/docker-library/cassandra/blob/master/4.1/docker-entrypoint.sh L44-91; content.md L69-91.",
    "Mặc định 4.1: materialized_views_enabled false (L1733), sasi_indexes_enabled false (L1737), user_defined_functions_enabled false (L1514), authenticator AllowAllAuthenticator (L169), authorizer AllowAllAuthorizer (L178), incremental_backups false (L960), auto_snapshot true (L972). Nguồn: https://github.com/apache/cassandra/blob/cassandra-4.1/conf/cassandra.yaml",
    "Bật MV/xác thực trong Docker: mount cassandra.yaml đã sửa (đã thử: 3 dòng authenticator: PasswordAuthenticator, authorizer: CassandraAuthorizer, materialized_views_enabled: true). Đăng nhập đầu tiên: cqlsh -u cassandra -p cassandra. Nguồn: evidence/t3_auth_check.sh, t3_auth_check.out.",
    "Quản trị người dùng (khi bật PasswordAuthenticator): CREATE ROLE app_admin WITH PASSWORD = '...' AND LOGIN = true; GRANT ALL PERMISSIONS ON KEYSPACE ride_booking TO app_admin; GRANT SELECT ON KEYSPACE ride_booking TO app_reader; LIST ROLES; LIST ALL PERMISSIONS OF app_reader; user chỉ có SELECT ghi dữ liệu bị từ chối 'no MODIFY permission'. Nguồn: evidence/t3_auth.cql, t3_auth_check.out L12-33.",
    "Lỗi nguyên văn khi chưa bật xác thực: CREATE ROLE ... WITH PASSWORD -> \"org.apache.cassandra.auth.CassandraRoleManager doesn't support PASSWORD\"; GRANT -> \"You have to be logged in and not anonymous to perform this request\". Nguồn: evidence/t3_probe.out L146-149.",
    "SAI chỉ có từ Cassandra 5.0 (NEWS.txt cassandra-5.0 L185); 4.1 dùng được secondary index thường (CREATE INDEX ... ON rides(status)), SASI bị tắt. Nguồn: evidence/t3_index_gcgrace.out, t3_probe.out L3.",
    "GROUP BY 4.1: chỉ trên cột khóa chính theo thứ tự khai báo; có floor(ts, 1d) để nhóm theo ngày (mới ở 4.1, NEWS.txt 4.1 L171-172); AVG trên bigint chia nguyên -> dùng CAST(x AS double). Ví dụ chạy được: SELECT customer_id, floor(booked_at, 1d), COUNT(*) FROM rides_by_customer WHERE customer_id='CUST001' GROUP BY customer_id, floor(booked_at, 1d). Nguồn: evidence/t3_probe.out L6-37.",
    "LWT nhận cuốc chạy được: UPDATE rides SET driver_id='DRV01', status='ACCEPTED' WHERE ride_id=... IF status='REQUESTED'; tài xế thứ hai nhận [applied]=False kèm status hiện tại. BATCH có IF chỉ trong 1 partition. Chi phí: Paxos 4 vòng (Cassandra TDG 3rd ed., mục Lightweight Transactions and Paxos; cql/dml.adoc L292-293). Nguồn: evidence/t3_probe.out L76-96.",
    "Counter: 64-bit signed; bảng chỉ chứa counter ngoài khóa; không INSERT, không TTL, không SET, không LWT, BATCH riêng (BEGIN COUNTER BATCH); không idempotent khi retry. Nguồn: cql/types.adoc 4.1 L56-83 (https://github.com/apache/cassandra/blob/cassandra-4.1/doc/modules/cassandra/pages/cql/types.adoc); evidence/t3_probe.out L112-125.",
    "Static column bắt buộc có clustering column; WRITETIME/TTL không dùng được trên collection/UDT không frozen ở 4.1 (chỉ 5.0). Nguồn: evidence/t3_probe.out L97-111; cql/dml.adoc 4.1 L88-89; NEWS.txt 5.0 L214-216.",
    "Không UPDATE được cột thuộc PRIMARY KEY ('PRIMARY KEY part status found in SET part'); đổi khóa = DELETE + INSERT trong BATCH (logged, có chi phí batchlog khi nhiều partition: cql/dml.adoc L452-453). Nguồn: evidence/t3_probe.out L132-145.",
    "Bảng chuỗi thời gian có TTL: PRIMARY KEY ((driver_id, day), ts) WITH CLUSTERING ORDER BY (ts DESC) AND default_time_to_live = 86400 AND compaction = {'class':'TimeWindowCompactionStrategy','compaction_window_unit':'HOURS','compaction_window_size':1} tạo được; gc_grace_seconds mặc định 864000. TWCS dành cho dữ liệu time-series/TTL (compaction/twcs.adoc L4-11, chọn ~20-30 cửa sổ L36-37); TTL hết hạn thành tombstone tồn tại ít nhất gc_grace_seconds (compaction/index.adoc L178-187). Nguồn: evidence/t3_index_gcgrace.out.",
    "Backup/restore đã chạy thật trên 4.1.12: nodetool flush; nodetool snapshot -t bk ride_booking (hoặc -kt ks.table); nodetool listsnapshots; snapshot nằm ở /var/lib/cassandra/data/<ks>/<table>-<id>/snapshots/<tên>/ kèm schema.cql. Khôi phục: nodetool import [-cd] <ks> <table> <thư_mục> (khuyến nghị); nodetool refresh <ks> <table> sau khi chép SSTable vào thư mục bảng (chạy được nhưng in 'nodetool refresh is deprecated, use nodetool import instead'); sstableloader -d <ip> /đường/dẫn/<ks>/<table>/ (stream qua cổng 7000). Incremental backup: nodetool enablebackup / statusbackup / disablebackup, file nằm trong thư mục backups/ của bảng. Dọn: nodetool clearsnapshot -t <tên> -- <ks> hoặc --all. TRUNCATE/DROP tự tạo snapshot (auto_snapshot: true). Nguồn: evidence/t3_backup_restore.sh/.out, t3_backup_restore2.sh/.out; NEWS.txt 4.0 L390; operating/backups.adoc L345-350, L505-516.",
    "cqlsh, nodetool, sstableloader có sẵn trong /opt/cassandra/bin của image; sstabledump, sstablemetadata... ở /opt/cassandra/tools/bin (không có trong PATH). Chạy từ Windows: docker exec nosql-cassandra nodetool ... Nguồn: evidence/t3_backup_restore.out (cuối file).",
    "COPY TO/FROM: là lệnh cqlsh (không phải CQL); làm mất TTL/WRITETIME (TTL 86400 -> null); chạy được với collection, UDT, counter; không phù hợp dữ liệu lớn (operating/bulk_loading.adoc L7-8). Tùy chọn: HEADER, DELIMITER, NULL, DATETIMEFORMAT, MAXROWS, PAGESIZE, CHUNKSIZE, INGESTRATE, MAXBATCHSIZE, MAXATTEMPTS, MAXPARSEERRORS, ERRFILE, TTL. Nguồn: evidence/t3_copy_ttl.out, evidence/t3_copy_counter_help.out; tools/cqlsh.adoc L126-129.",
    "DESCRIBE KEYSPACE <ks> xuất toàn bộ DDL (keyspace, type, table, index) để sao lưu lược đồ. Nguồn: evidence/t3_describe_keyspace_probe.cql (11 câu CREATE).",
    "RAM: node cassandra:4.1 với MAX_HEAP_SIZE=1G dùng ~1,22–1,28 GiB khi rảnh (-Xms1G -Xmx1G); 3 node ≈ 3,7–3,9 GiB + overhead Docker Desktop. Tài liệu khuyến nghị heap production ≥ 2 GB (operating/hardware.adoc L36). Nguồn: evidence/t3_memory.out.",
    "Thư mục dữ liệu của bảng có dạng <bảng>-<id không dấu gạch>; sau DROP KEYSPACE thư mục cũ vẫn còn, nên script tìm thư mục theo id: SELECT id FROM system_schema.tables WHERE keyspace_name=... AND table_name=... Nguồn: evidence/t3_backup_restore2.sh (hàm tdir).",
  ],
}
const PRE4 = {
  findings: [
    {"id": "P1", "claim": "\"Python 3.12 cần cassandra-driver ≥ 3.29\"", "verdict": "partly_wrong", "severity": "high", "evidence": "Lower bound is right: CHANGELOG 3.29.0 (Dec 19, 2023): \"Add support for Python 3.9 through 3.12\" (https://github.com/apache/cassandra-python-driver/blob/trunk/CHANGELOG.rst L97-103); PyPI files: 3.28.0 has no cp312 wheel (sdist only for 3.12), 3.29.0+ have cp312-win_amd64 wheels, win32 dropped from 3.30.0 (evidence/p4_pypi.out, from https://pypi.org/pypi/cassandra-driver/json). But it is not sufficient on Windows: with Windows CPython 3.12.7, `from cassandra.cluster import Cluster` raises \"DependencyException: Unable to load a default connection class\" for 3.29.1 and for the latest 3.30.1 (evidence/p4_windows_py312.out L15-32). Cause: cluster.py 3.30.1 L145-175 tries gevent -> eventlet -> libev -> asyncore and raises at import time if none loads (asyncio is not in the chain); asyncorereactor.py L35-42 raises \"Unable to import asyncore module. Note that this module has been removed in Python 3.12\"; the Windows wheels 3.29.0/3.29.1 contain no libevwrapper (p4_windows_py312.out L3-4) and 3.29.2-3.30.1 contain libevwrapper.cp312-win_amd64.pyd that imports ev-4.dll, which no wheel bundles (L5-13) -> \"DLL load failed while importing libevwrapper\" (L32). Fix verified: same 3.30.1 + `pyasyncore` -> AsyncoreConnection, connects to Cassandra 4.1.12, GROUP BY and LWT run (L33-39). Official docs: installation.rst 3.30.1 L192-194 \"Python 3.12 removed asyncore from the runtime but this event loop can still be used in newer versions of Python via the pyasyncore package\". Contrast: on Linux CPython 3.12.15 the manylinux wheel of 3.30.1 picks LibevConnection and connects without pyasyncore (evidence/p4_linux_py312.out), so the failure is specific to Windows.", "correction": "Mốc 3.29 đúng là bản đầu tiên hỗ trợ Python 3.12, nhưng trên Windows như vậy chưa đủ: mọi bản từ 3.29.0 đến 3.30.1 (mới nhất, phát hành 06/2026) đều lỗi DependencyException \"Unable to load a default connection class\" ngay khi import nếu chỉ cài cassandra-driver. Câu lệnh đúng cho máy Windows + Python 3.12: pip install \"cassandra-driver==3.30.1\" pyasyncore (ghi vào requirements.txt). Cách khác: dùng Python 3.11 (asyncore vẫn còn trong thư viện chuẩn), hoặc tự cài libev qua vcpkg cho bản ≥ 3.29.2 (phức tạp, không khuyến nghị cho đồ án)."},
    {"id": "P2", "claim": "(missing) Reactor asyncio không được tự chọn; không thể sửa lỗi bằng cách đặt connection_class sau khi import", "verdict": "missing", "severity": "medium", "evidence": "cluster.py 3.30.1 L171-175: conn_fns = (_try_gevent_import, _try_eventlet_import, _try_libev_import, _try_asyncore_import); if none -> raise DependencyException at module import, so Cluster(connection_class=AsyncioConnection) cannot be reached when the import itself fails (evidence/p4_windows_py312.out L18, L27). installation.rst 3.30.1 L196-198: \"The asyncio event loop is generally functional but still somewhat experimental and not recommended for production systems.\" With pyasyncore installed, explicit AsyncioConnection also works (p4_windows_py312.out L40-41).", "correction": "Cần nói rõ: driver không tự chuyển sang asyncio; lỗi xảy ra ngay lúc import cassandra.cluster nên không thể tránh bằng cách truyền connection_class=AsyncioConnection. Hướng xử lý chuẩn theo tài liệu chính thức là cài pyasyncore (asyncore/libev được coi là đạt chuẩn production, asyncio vẫn là thử nghiệm). Khi đã có pyasyncore thì có thể chọn AsyncioConnection nếu muốn, nhưng không cần cho đồ án."},
    {"id": "P3", "claim": "\"Python FastAPI + Jinja/Bootstrap\" chạy được trên máy Windows (Python 3.12.7)", "verdict": "correct", "severity": "medium", "evidence": "Windows CPython 3.12.7: cassandra-driver 3.30.1 + pyasyncore + fastapi 0.142.2 + uvicorn 0.54.0 + jinja2 3.1.6 (all have Windows-compatible wheels; pydantic_core 2.46.5 cp312 win_amd64) served /customers/CUST001/rides rendered by a Jinja2 template with Bootstrap 5.3.3 CSS, rows read from Cassandra 4.1.12 via a prepared statement (evidence/p4_windows_py312.out L42-46; app in evidence/p4_fastapi_app/). PyPI: fastapi requires_python >=3.10, uvicorn >=3.10, Jinja2 >=3.7.", "correction": "Đúng, với điều kiện cài thêm pyasyncore (xem P1). Lưu ý khi viết code: các hàm của driver (session.execute) là đồng bộ, nên khai báo route FastAPI bằng def (FastAPI tự chạy trong threadpool) hoặc dùng session.execute_async; không gọi session.execute trong async def vì sẽ chặn event loop. Tạo Cluster/Session một lần khi khởi động ứng dụng và dùng prepared statement cho các truy vấn lặp lại."},
    {"id": "P4", "claim": "(missing) Cấu hình kết nối driver: load-balancing policy với local_dc và protocol_version", "verdict": "missing", "severity": "low", "evidence": "evidence/p4_probe_lbp.out L3: \"Cluster.__init__ called with contact_points specified, but no load_balancing_policy. In the next major version, this will raise an error; please specify a load-balancing policy.\" L4-5 and L8-9: \"Downgrading core protocol version from 66 to 65 ... from 65 to 5 ... it is best practice to explicitly set Cluster(protocol_version)\"; negotiated protocol_version 5 (L6, L10). Local DC of this setup is datacenter1 (L37 of p4_windows_py312.out).", "correction": "Nên khởi tạo kết nối rõ ràng để tránh cảnh báo và lỗi ở bản driver sau: Cluster(['127.0.0.1'], port=9042, protocol_version=5, execution_profiles={EXEC_PROFILE_DEFAULT: ExecutionProfile(load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc='datacenter1')))}). Nếu bật PasswordAuthenticator thì thêm auth_provider=PlainTextAuthProvider(username=..., password=...)."},
    {"id": "P5", "claim": "Phương án thay thế Node.js với gói npm \"cassandra-driver\"", "verdict": "correct", "severity": "low", "evidence": "npm registry: cassandra-driver latest 4.10.0 (2026-09-23), previous 4.9.0 (2026-05-06), 4.8.0 (2025-02-20); repository git+https://github.com/apache/cassandra-nodejs-driver.git; engines node >=20 (evidence/p4_node_driver.out L2-5). Probe with Node v22.22.0: Client({contactPoints:['127.0.0.1:9042'], localDataCenter:'datacenter1'}) -> Row { release_version: '4.1.12', data_center: 'datacenter1' } (L7-8). The package is pure JavaScript (dependencies long, adm-zip), so it has no native-extension issue on Windows.", "correction": "Đúng: driver Node.js vẫn được duy trì (đã chuyển về Apache, bản 4.10.0 tháng 9/2026), yêu cầu Node.js ≥ 20 và bắt buộc khai báo localDataCenter ('datacenter1' với cấu hình hiện tại). Đây là phương án dự phòng không vướng lỗi asyncore/libev; tuy vậy Python + pyasyncore đã chạy được nên không bắt buộc đổi."},
  ],
  facts_for_prompt2: [
    "cassandra-driver (Python) mới nhất: 3.30.1 (PyPI upload 2026-07-06; CHANGELOG ghi June 19, 2026), Requires-Python >=3.10, phụ thuộc geomet>=1.1, Deprecated>=1.3.1. Dự án đã chuyển sang Apache: https://github.com/apache/cassandra-python-driver (CHANGELOG 3.30.0 'Update DRIVER_NAME after donation to ASF'). Nguồn: https://pypi.org/pypi/cassandra-driver/json; wheel METADATA.",
    "Mốc hỗ trợ Python 3.12: 3.29.0 (19/12/2023, 'Add support for Python 3.9 through 3.12'); 3.29.1 sửa bản Linux 3.12 thiếu libev (PYTHON-1378); 3.29.2 thêm libev cho bản Windows 3.12 (PYTHON-1386); 3.30.0 bỏ wheel win32, đánh dấu deprecated reactor eventlet/gevent/Twisted. Nguồn: https://github.com/apache/cassandra-python-driver/blob/trunk/CHANGELOG.rst L1-112.",
    "Wheel Windows cp312: 3.29.0/3.29.1 không có libevwrapper; 3.29.2–3.30.1 có libevwrapper.cp312-win_amd64.pyd nhưng phụ thuộc ev-4.dll không được đóng gói. Nguồn: evidence/p4_windows_py312.out L3-13 (đọc trực tiếp các file .whl từ PyPI và bảng import PE).",
    "Trên Windows + Python 3.12.7, chỉ cài cassandra-driver (kể cả 3.30.1) -> import lỗi 'DependencyException: Unable to load a default connection class'. Cài thêm pyasyncore -> dùng AsyncoreConnection, kết nối Cassandra 4.1.12 thành công. Lệnh: pip install \"cassandra-driver==3.30.1\" pyasyncore. Nguồn: evidence/p4_windows_py312.out; installation.rst 3.30.1 L192-198 (https://github.com/apache/cassandra-python-driver/blob/3.30.1/docs/installation.rst).",
    "Chuỗi chọn reactor mặc định (cluster.py 3.30.1 L145-175): gevent (nếu đã monkey-patch) -> eventlet (nếu đã monkey-patch) -> libev -> asyncore; asyncio không nằm trong chuỗi và là thử nghiệm. Nguồn: https://github.com/apache/cassandra-python-driver/blob/3.30.1/cassandra/cluster.py",
    "Stack FastAPI 0.142.2 + uvicorn 0.54.0 + Jinja2 3.1.6 + Bootstrap 5.3.3 (CDN) + cassandra-driver 3.30.1 + pyasyncore chạy trên Python Windows 3.12.7 và đọc dữ liệu từ Cassandra 4.1.12. Mã thử: evidence/p4_fastapi_app/main.py, templates/rides.html. Nguồn: evidence/p4_windows_py312.out L42-46.",
    "Khung kết nối khuyến nghị: Cluster(['127.0.0.1'], port=9042, protocol_version=5, execution_profiles={EXEC_PROFILE_DEFAULT: ExecutionProfile(load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc='datacenter1')))}); thiếu policy sẽ có cảnh báo 'In the next major version, this will raise an error'. Nguồn: evidence/p4_probe_lbp.py/.out.",
    "Kết quả LWT từ Python đọc bằng ResultSet.was_applied (đã thử UPDATE ... IF status='ONGOING'). Nguồn: evidence/p4_probe.py, p4_windows_py312.out L39.",
    "Node.js: npm cassandra-driver 4.10.0 (2026-09-23), repo apache/cassandra-nodejs-driver, engines node >=20, thuần JavaScript; kết nối cần localDataCenter: 'datacenter1'. Đã kết nối thành công tới 4.1.12 bằng Node v22. Nguồn: evidence/p4_node_driver.out.",
    "Trên Linux (Python 3.12.15, wheel manylinux) driver 3.30.1 tự dùng LibevConnection và kết nối được mà không cần pyasyncore; lỗi DependencyException chỉ xảy ra trên Windows vì wheel Windows thiếu ev-4.dll. Nguồn: evidence/p4_linux_py312.out.",
    "Danh sách phiên bản PyPI (pip index versions): 3.30.1 mới nhất; 3.28.0 không có wheel cp312. Nguồn: evidence/p4_pypi.out.",
  ],
}
// ==== PRECOMPUTED RESULTS: END ====

phase('Verify')

const pText = agent(`${CONTEXT}

YOUR SCOPE (id prefix "T"): every Prompt 1 statement about the DRAFT's text, structure and formatting. Use draft.txt AND the .docx itself (python-docx, or unzip and read word/document.xml, word/styles.xml, docProps/app.xml).
Check at least:
1. Page count. Prompt 1 says "Mới khoảng 25–30 trang (yêu cầu 50–60)". docProps/app.xml reports Pages=36, Words=5431. Determine the actual formatting (body font, size, line spacing from styles.xml docDefaults / Normal style / direct run formatting; sz is half-points so 26 = 13pt; spacing line=360 lineRule=auto means 1.5 lines), page size and margins, then state the most defensible page count and whether it already follows Times New Roman 13 / 1.5.
2. Front matter: Table of Contents field (w:instrText containing TOC, or w:sdt with docPartGallery "Table of Contents"), list of figures, list of tables, abbreviations list, Lời cảm ơn, Lời cam đoan.
3. The references section after "TÀI LIỆU THAM KHẢO": number of entries and their content. Prompt 1 says "tài liệu tham khảo chỉ 1 dòng".
4. Chapters 3.4 and 3.7: did the group APPLY a model-to-database change (e.g. the gmail/email rename pushed to Cassandra) or only DB-to-model import / difference detection? Prompt 1 lists "đồng bộ chiều Model sang DB" as missing.
5. Count the distinct CQL queries shown or executed anywhere in the draft (3.1 Query Builder, 4.3 CQL Editor, elsewhere). Prompt 1 says "Mới có 1 câu WHERE customer_id='CUST001'".
6. Data Explorer / Data Editor and Import/Export: demonstrated (steps + figure) or only mentioned?
7. Any DbSchema version number; any Cassandra version; any mention of Docker or of how Cassandra was installed.
8. The comparison table: how many criteria rows (is row 1 a header?). Prompt 1 says "13 tiêu chí".
9. Cover page lecturer ("Giảng viên hướng dẫn") vs the lecturer list in chitiet.txt. Prompt 1 warned: "Bản nháp ghi GVHD là ThS. Trần Thị Vân Anh, nhưng thang điểm do cô Nguyễn Thị Định ký. Bạn xem lại cho đúng người." Is this warning justified?
10. Any Cassandra architecture content (gossip, token ring, replication, consistency, commit log / memtable / SSTable).
Also report any OTHER statement in prompt1_answer.md about the draft that is wrong, and confirm the ones that are right (verdict "correct").`,
  { label: 'draft-text', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

const pShots = agent(`${CONTEXT}

YOUR SCOPE (id prefix "S"): the draft's SCREENSHOTS.
Step 1. Extract all inline images from the .docx in document order and map each to its caption. Suggested method (python-docx): iterate doc.element.body paragraphs in order; for each paragraph find every a:blip element, read its r:embed id, resolve doc.part.related_parts[rId] (blob + partname extension); the caption is usually the next paragraph whose style name is "Caption VN" (text "Hình x.y. ..."). Save as ${X}/figs/NN.ext and write ${X}/figs/index.txt mapping NN to caption.
Step 2. LOOK at the images with the Read tool (it renders images). View every figure that can reveal: (a) the existing schema of keyspace ride_booking: exact column names, CQL types, partition keys, clustering keys and order for tables customers, drivers, rides_by_customer, vehicles (diagram figures around Hình 3.5, sync figures, Query Builder Hình 3.4, Data Generator figures, NoSQL Manager figures Hình 4.1–4.4 which may show columns/CQL tabs); (b) Cassandra version (cqlsh banner, NoSQL Manager server info), host/port and the DataCenter value typed in the DbSchema connection dialog (Hình 2.5/2.6), and whether Cassandra ran in Docker or natively (Windows paths, docker hints); (c) DbSchema version/edition (title bar, about box, trial banners); (d) anything else relevant. Viewing all 35 is fine.
Step 3. Verify Prompt 1 statements that depend on screenshots, at least: "Phiên bản Cassandra: đề xuất giữ 4.1 cho khớp ảnh đã chụp"; "Ảnh chụp đang dùng keyspace ride_booking"; "Giữ 4 bảng đã có (customers, drivers, rides_by_customer, vehicles)" together with the newly proposed rides_by_customer PRIMARY KEY ((customer_id), booked_at DESC, ride_id) — would it conflict with the existing table (Cassandra cannot ALTER a primary key; it would need DROP + CREATE and re-taking screenshots)?
Return figures (one entry per image), existing_schema (one entry per table, with confidence), environment, findings, facts_for_prompt2.`,
  { label: 'draft-screenshots', phase: 'Verify', schema: SHOTS_SCHEMA, agentType: 'general-purpose' })

// Checkers 3 (cassandra-41) and 4 (python-driver) were completed in a cloud run; PRE3/PRE4 above hold their results.
// Locally only what needed this machine is left: matching each claim to prompt1_answer.md and, for checker 4,
// a probe on the real Windows Python. If a local check returns nothing, the precomputed result is used unchanged.
const settle = p => Promise.resolve(p).catch(() => null)
const withPrecomputed = (pre, label) => r => {
  if (r && r.findings && r.findings.length) return { findings: r.findings, facts_for_prompt2: pre.facts_for_prompt2.concat(r.facts_for_prompt2 || []) }
  log(`${label}: local check returned no findings, using the precomputed result unchanged`)
  return pre
}
const RECONCILE = `Claim reconciliation (the cloud run had no access to prompt1_answer.md):
a. Open ${X}/prompt1_answer.md. For every finding below, set "claim" to the exact Prompt 1 sentence it checks, quoted. Claims tagged "[theo workflow]" are paraphrases of this workflow's scope, not quotes.
b. If Prompt 1 never says it, use claim "(missing)" and verdict "missing" when the point still matters for the report or the demo app; drop the finding when it no longer matters.
c. If Prompt 1's real wording changes the judgement (for example it already recommends TimeWindowCompactionStrategy, or never proposes a counter table for revenue), update verdict, severity and correction, and append to evidence "LOCAL CHECK: " followed by the quote and the reason. Otherwise keep id, verdict, severity, evidence and correction exactly as given.
d. Look for statements in prompt1_answer.md inside your scope that no finding below covers. Judge each one with the precomputed evidence (${RES}/evidence and the facts_for_prompt2 of the task JSON in ${RES}) or the local extracts under ${X}; number them after the last existing id. Use "unverifiable" when that evidence does not settle the statement.
Return every finding, changed or not. Return facts_for_prompt2 as [] unless you verified a new fact: the precomputed facts are merged automatically.`

const pCass = settle(agent(`${CONTEXT}

YOUR SCOPE (id prefix "C"): LOCAL CHECK of checker 3 (cassandra-41): every Cassandra technical statement in prompt1_answer.md, for Apache Cassandra 4.1 as run by the docker image cassandra:4.1. The verification itself is DONE (see PRECOMPUTED above, details in ${RES}/README.md): do not repeat it, do no web research, and do not start Docker.
${RECONCILE}
Budget: about 12 tool calls.
PRECOMPUTED FINDINGS (checker 3):
${JSON.stringify(PRE3.findings)}`,
  { label: 'cassandra-41-localcheck', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' }))
  .then(withPrecomputed(PRE3, 'cassandra-41'))

const pPy = settle(agent(`${CONTEXT}

YOUR SCOPE (id prefix "P"): LOCAL CHECK of checker 4 (python-driver): the claim "Python 3.12 cần cassandra-driver ≥ 3.29", the stack "Python FastAPI + Jinja/Bootstrap" on this Windows machine (Python 3.12.7), and the Node.js "cassandra-driver" alternative. The research is DONE (see PRECOMPUTED above, details in ${RES}/README.md): do not repeat the PyPI, changelog or npm research.
Step 1, real-Windows confirmation. The cloud run used the official Windows CPython 3.12.7 under Wine; confirm it on this machine's Python 3.12.7:
  python -m venv ${X}/venv_probe   and copy ${RES}/evidence/p4_probe.py to ${X}/p4_probe.py
  ${X}/venv_probe/Scripts/python -m pip install "cassandra-driver==3.30.1"
  ${X}/venv_probe/Scripts/python ${X}/p4_probe.py   (no "connect" argument: Cassandra is not running)
     expected: "IMPORT FAILED: DependencyException Unable to load a default connection class" and "libevwrapper cause: ImportError DLL load failed ..."
  ${X}/venv_probe/Scripts/python -m pip install pyasyncore   then run p4_probe.py again
     expected: "connection_class: <class 'cassandra.io.asyncorereactor.AsyncoreConnection'>"
  ${X}/venv_probe/Scripts/python -m pip install fastapi uvicorn jinja2   then print their versions with one python -c command.
  Delete ${X}/venv_probe afterwards. Never install anything into the global Python or into the project folder.
  Append the exact outputs to the evidence of P1 (install and probe runs) and P3 (fastapi line), prefixed "REAL WINDOWS: ". If the real result differs from the expected one, change verdict and correction to match the real machine and say so explicitly. If pip cannot reach PyPI, say that in the evidence and leave the verdicts unchanged.
Step 2.
${RECONCILE}
Budget: about 15 tool calls.
PRECOMPUTED FINDINGS (checker 4):
${JSON.stringify(PRE4.findings)}`,
  { label: 'python-driver-localcheck', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' }))
  .then(withPrecomputed(PRE4, 'python-driver'))

const pDb = agent(`${CONTEXT}

YOUR SCOPE (id prefix "D"): DbSchema facts. Use dbschema.com official pages (documentation, features, pricing/editions, download/changelog) and the DbSchema Cassandra JDBC driver repository on GitHub.
Determine:
1. Current DbSchema major version in 2025–2026; edition model (free/Community vs Pro); trial length.
2. Which features are Pro-only vs free: Data Generator, HTML5/PDF documentation, Schema Synchronization/Compare, Visual Query Builder, Relational Data Explorer / Data Editor, Data Loader (CSV/Excel import), result export, Git integration, Virtual Foreign Keys, Cassandra support.
3. Official names of the data browse/edit feature, the CSV import feature and export; do they work with Cassandra through the DbSchema Cassandra JDBC driver?
4. Cassandra JDBC URL format and the DataCenter / local-datacenter parameter; the driver class name (the draft says com.dbschema.Cassandra.JdbcDriver — verify the exact class name in the GitHub repo).
5. Can the DbSchema SQL/CQL editor run arbitrary CQL (CREATE KEYSPACE/TABLE/INDEX, BATCH, INSERT ... IF NOT EXISTS, GROUP BY, USING TTL) so rubric item 7 ("Triển khai truy vấn dữ liệu cơ bản/nâng cao trên GUI Tool") can be evidenced with DbSchema screenshots? Known limitations?
6. Any DbSchema backup/restore or data export features usable for rubric item 6 ("Import/export dữ liệu; Backup và Restore dữ liệu").
Map each to Prompt 1 statements (e.g. "Thiếu Data Explorer/Editor, Import/Export", "Import/Export (COPY, DbSchema)", "Chức năng DbSchema: giữ 7 nhóm, thêm Data Explorer/Editor, Import/Export, đồng bộ Model sang DB, 3 ảnh Git") and report findings. Put each verified feature fact in facts_for_prompt2 with source URL.`,
  { label: 'dbschema', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

const pRubric = agent(`${CONTEXT}

YOUR SCOPE (id prefix "R"): internal consistency of prompt1_answer.md and its mapping to the rubric and syllabus.
Check:
1. Arithmetic: per-item scores sum to the stated "2,3/10"; "Phần tìm hiểu Tool đã làm khoảng 65%".
2. Table count: Prompt 1 says "Giữ 4 bảng đã có (customers, drivers, rides_by_customer, vehicles) và thêm khoảng 9 bảng" and later "khoảng 13 bảng". Count the rows of its own table (rides_by_customer is one of the 4 existing ones) and compute the real numbers.
3. Page plan: sum the chapter page numbers in the outline table vs the claim "khoảng 55 trang" vs the rubric's 50–60 pages (does front matter count?).
4. Naming consistency among proposed tables (e.g. "area" vs "city", rides_by_area_date keyed by city).
5. Does every rubric line (items 1–10 including all sub-items) have a concrete home in the proposed outline/app? Is the rubric note about GUI tools (items 1–4 replaced by +2 points if no new GUI tool is studied) correctly understood/applied for a DbSchema topic?
6. Scoring fairness using draft.txt: item 10 sub-items 2–4 (defense, on-time submission with Word/PowerPoint/source, teamwork) happen later — is scoring them now (~0,6/2,0 overall for item 10) meaningful, and how should the percentage be reported instead? Item 1 is "Tìm hiểu lý thuyết và cài đặt Tool theo yêu cầu đề tài" — is deducting for missing Cassandra architecture justified, or does item 1 concern the Tool (DbSchema)? Re-estimate each item if you disagree, with reasons.
7. Syllabus chitiet.txt: assessment weights, deadlines, CLOs, required deliverables, lecturer list — anything Prompt 1 missed or got wrong.
8. Gendered terms used for people whose gender is not stated (e.g. "cô Nguyễn Thị Định") — flag; the neutral form is "giảng viên"/academic title.
9. The six closing questions: any based on a false premise, missing a decision that blocks Prompt 2, or asked in a way that is hard to answer?`,
  { label: 'rubric-consistency', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

const pDesign = Promise.all([pShots]).then(([shots]) => agent(`${CONTEXT}

YOUR SCOPE (id prefix "M"): adversarial query-first review of the Cassandra tables PROPOSED in prompt1_answer.md section 2 ("Các bảng thiết kế theo truy vấn") for the ride-hailing app. Use the data-modeling chapter (${X}/book_datamodel.txt: query-first design, Chebotko diagrams, partition size formulas) and the course slides.
Existing schema reconstructed from the draft screenshots by another checker (may be partial):
${JSON.stringify(shots ? { existing_schema: shots.existing_schema, environment: shots.environment } : 'unavailable')}
Verified Cassandra 4.1 facts from checker 3 (precomputed, executed on a real 4.1.12 node):
${JSON.stringify(PRE3.facts_for_prompt2)}
Checker 3 already reviewed these proposed tables (build on these findings, do not repeat them):
${JSON.stringify(PRE3.findings.filter(f => ['C8', 'C9', 'C10'].includes(f.id)))}
Check at least:
1. List the application queries implied by the app features in Prompt 1 (login/roles, booking, driver matching, accepting a ride, status changes, payments, ratings, revenue dashboard, promotions, GPS, CRUD, backup). For each, is there a table whose partition key is fully specified by the query? Which queries are missing (e.g. ride detail, a driver's current active ride, payment of one ride, ratings a customer gave, vehicle by plate)?
2. Partition sizing with realistic numbers (state assumptions; use the book's Nv = Nr(Nc − Npk − Ns) + Ns and size formulas): rides_by_customer unbounded?, rides_by_area_date per city per day, drivers_by_area ((area, status) ...) hot partition.
3. Update anomalies: status inside the partition key (moving rows = DELETE + INSERT), rating as a clustering column (every rating change = delete + insert), how one ride status change fans out to every denormalized table (rides, rides_by_customer, rides_by_driver_month, rides_by_area_date, ...) and whether a logged BATCH is appropriate.
4. Naming/semantics: "area" vs "city" inconsistency; "Tìm tài xế rảnh gần khách" when the table is per area, not geo distance.
5. Compatibility with the existing 4 tables: Prompt 1 says "Giữ 4 bảng đã có" yet proposes rides_by_customer PRIMARY KEY ((customer_id), booked_at DESC, ride_id). Primary keys cannot be altered in Cassandra.
6. Is the count right ("thêm khoảng 9 bảng", "khoảng 13 bảng")? Is that number appropriate for a 3-student project, or should it be trimmed? Which tables give the most rubric value for basic vs advanced queries (LWT, BATCH, TTL, counter, static, collections/UDT, GROUP BY aggregates, secondary index, PER PARTITION LIMIT)?
Put your recommended corrected table list (name, PRIMARY KEY, query served, one-line reason) into facts_for_prompt2, one table per item. This is for discussion, not final CQL.`,
  { label: 'design-review', phase: 'Design review', schema: FINDINGS_SCHEMA, agentType: 'planner' }))

const LABELS = ['draft-text', 'draft-screenshots', 'cassandra-41', 'python-driver', 'dbschema', 'rubric-consistency', 'design-review']
const results = await Promise.all([pText, pShots, pCass, pPy, pDb, pRubric, pDesign])
const ok = results.map((r, i) => (r ? { ...r, src: LABELS[i] } : null))
ok.forEach((r, i) => { if (!r) log(`checker ${LABELS[i]} returned nothing`) })
const findings = ok.filter(Boolean).flatMap(r => (r.findings || []).map(f => ({ ...f, src: r.src })))
log(`${findings.length} findings from ${ok.filter(Boolean).length}/7 checkers`)

phase('Critic')
const critic = await agent(`${CONTEXT}

YOUR SCOPE (id prefix "K"): completeness critic. Seven checkers already produced the findings listed below. Read prompt1_answer.md, rubric.txt, YEUCAUDOAN.txt and chitiet.txt yourself with fresh eyes and report ONLY NEW findings none of them covered. Consider at least: process (Prompt 1 ended with six questions at once — a good design dialogue asks one decision at a time, most blocking first); risks (DbSchema trial expiry, DbSchema JDBC driver vs Cassandra 4.1, Docker Desktop RAM on Windows/WSL2, the Data Generator TIMESTAMP codec error and how to fix it); deliverables (Word, PowerPoint, source code, .dbs, .cql, CSV); per-member grading and work split; defense preparation; the "không được sao chép" rule (paraphrase + cite); feasibility of an app-level "Backup" button (a web app cannot run nodetool without docker exec or JMX; logical export via the driver is the realistic in-app option); Cassandra roles (CREATE ROLE/GRANT) as part of "quản trị người dùng"; whether rubric item 7 queries must be executed in DbSchema itself (screenshots) rather than cqlsh; mid-term vs final framing of the score. Also flag any finding below that looks wrong.
FINDINGS SO FAR:
${JSON.stringify(findings.map(f => ({ id: f.id, src: f.src, claim: f.claim, verdict: f.verdict, correction: f.correction })))}`,
  { label: 'critic', phase: 'Critic', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

const all = findings.concat(critic ? (critic.findings || []).map(f => ({ ...f, src: 'critic' })) : [])

phase('Skeptic')
const skeptic = await agent(`${CONTEXT}

YOUR SCOPE: adversarial skeptic. Below are findings about Prompt 1 from several checkers. For EVERY finding whose verdict is "wrong", "partly_wrong" or "missing", try hard to REFUTE it: re-open the cited evidence where cheap (files under ${X}, the .docx, ${X}/prompt1_answer.md; the web for external facts), confirm the finding matches what Prompt 1 actually says (quote prompt1_answer.md), and confirm the proposed correction is itself correct. Set upheld=false if the evidence is missing or misread, if Prompt 1 never said it, or if the correction is wrong (then put a fixed correction in adjusted_correction, in Vietnamese). For findings with verdict "correct" or "unverifiable", set upheld=true unless obviously mistaken. Return exactly one verdict per finding id.
FINDINGS:
${JSON.stringify(all)}`,
  { label: 'skeptic', phase: 'Skeptic', schema: VERDICTS_SCHEMA, agentType: 'general-purpose' })

return {
  findings: all,
  verdicts: skeptic ? skeptic.verdicts : null,
  existing_schema: ok[1] ? ok[1].existing_schema : null,
  environment: ok[1] ? ok[1].environment : null,
  figures: ok[1] ? ok[1].figures : null,
  facts_for_prompt2: ok.filter(Boolean).flatMap(r => (r.facts_for_prompt2 || []).map(x => `[${r.src}] ${x}`))
    .concat(critic ? (critic.facts_for_prompt2 || []).map(x => `[critic] ${x}`) : []),
}
