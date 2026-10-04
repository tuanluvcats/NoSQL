export const meta = {
  name: 'verify-prompt1-analysis',
  description: 'Fact-check the Prompt 1 draft evaluation and project direction (DbSchema + Cassandra ride-hailing) before writing CASSANDRA.MD',
  phases: [
    { title: 'Verify', detail: '6 parallel fact-checkers: draft text, screenshots, Cassandra 4.1, Python driver, DbSchema, rubric consistency' },
    { title: 'Design review', detail: 'query-first review of proposed tables against the real existing schema' },
    { title: 'Critic', detail: 'completeness critic: what Prompt 1 and the checkers missed' },
    { title: 'Skeptic', detail: 'try to refute every finding that changes the answer' },
  ],
}

const X = 'C:/Users/Yameow/AppData/Local/Temp/nosql_extract'
const DOCX = 'D:/Documents/Homework/NoSQL/DoAn/Báo cáo giữa kỳ NoSQL về DbSchema và Apache Cassandra.docx'

const CONTEXT = `CONTEXT. Vietnamese university course project (HUIT, NoSQL course, class 14DH), group of 3 students.
Topic: "Tìm hiểu công cụ DbSchema để quản trị và khai thác CSDL Cassandra – Quản lý dữ liệu đặt xe công nghệ" (ride-hailing booking data) plus a demo application.
In an earlier turn ("Prompt 1") an assistant graded the group's mid-term draft against the official rubric and proposed a direction. That answer is saved verbatim at ${X}/prompt1_answer.md. Your job is to FACT-CHECK it. Do not trust it.
Source files (UTF-8 text, already extracted): ${X}/rubric.txt (official rubric, verbatim), ${X}/YEUCAUDOAN.txt (project requirements), ${X}/chitiet.txt (course syllabus), ${X}/draft.txt (draft dump; paragraphs look like "[idx][StyleName] text", followed by tables and image/section info), ${X}/slide_cassandra.txt (course slides, Cassandra chapter), ${X}/book_datamodel.txt and ${X}/book_backup.txt (Cassandra: The Definitive Guide 3rd ed., data-modeling and maintenance/backup chapters), ${X}/book_toc.txt.
Original draft: ${DOCX} (35 inline images, 3 tables).
Environment: Windows 11, Git Bash, Python 3.12.7 with python-docx installed, cassandra-driver NOT installed, pdftotext available. Docker CLI is installed but the Docker daemon is NOT running: do not start it. D:/Documents/Homework/NoSQL/docker-compose.yml defines service cassandra: image cassandra:4.1, container nosql-cassandra, CASSANDRA_CLUSTER_NAME=NoSQLLab, port 9042, MAX_HEAP_SIZE=1G, single node.
RULES: the project folder D:/Documents/Homework/NoSQL is READ-ONLY (never create or modify files there). Scratch writes only under ${X}. Every verdict needs concrete evidence: file:line, command plus output, or URL plus quoted text. If you cannot verify, use verdict "unverifiable" (never guess). Verdict "missing" = something Prompt 1 should have said but did not. Verdict "correct" = the Prompt 1 statement holds. Write the "correction" field in Vietnamese. Use the id prefix given below for your finding ids (e.g. T1, T2...).
RESUME NOTE: an earlier run of these checks was interrupted before anyone returned results, but it left reusable artifacts under ${X} — list the folder first and REUSE them instead of redoing work: figs/ (images extracted from the .docx, figs/index.txt maps them to captions, figs/crops/ holds enlarged crops), extract_figs.py, docs41/ (Cassandra 4.1 docs as text), cassandra-4.1.yaml, NEWS-4.1.txt, docker-cassandra-4.1-Dockerfile, docker-cassandra-4.1-entrypoint.sh, web/ (downloaded pages; web/drv = DbSchema Cassandra JDBC driver source), changelog_*.rst, install_doc_*.rst, cluster_*.py, *reactor_3.30.1.py, pe_imports.py, probe*.txt, pipinst_*.txt, pypi_*.json, venv_probe/ (delete it when you are done if you use it). Budget: aim to finish in about 40 tool calls; return your structured output even if some checks must stay "unverifiable".`

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

const pCass = agent(`${CONTEXT}

YOUR SCOPE (id prefix "C"): every Cassandra technical statement in prompt1_answer.md, for Apache Cassandra 4.1 as run by the official docker image cassandra:4.1. Use official sources: cassandra.apache.org/doc/4.1/..., conf/cassandra.yaml on GitHub apache/cassandra branch cassandra-4.1, docker-library/cassandra (docker-entrypoint.sh for 4.1), plus the local book/slide extracts.
Check at least:
1. "Materialized View bị tắt mặc định" in 4.1: exact yaml key and default; how to enable it when running the docker image (env var or mounted cassandra.yaml); stability warnings.
2. "chưa có SAI (phải lên 5.0)": first release with SAI; SASI status and flag in 4.1.
3. "UDF cũng tắt mặc định": key and default in 4.1.
4. Aggregates COUNT/SUM/AVG/MIN/MAX with GROUP BY in 4.1 and their restrictions (GROUP BY only on partition key / clustering-column prefix).
5. PER PARTITION LIMIT; paging with token(); ALLOW FILTERING semantics.
6. LWT: INSERT ... IF NOT EXISTS; UPDATE ... IF status='REQUESTED' on a non-key column; serial consistency; cost.
7. Static columns (require clustering columns); set<text>; UDT; TTL; WRITETIME.
8. Counters: the proposed revenue_by_day PRIMARY KEY ((city, yyyymm), day) as a counter table. Rules: all non-PK columns must be counters, no TTL, no INSERT, counter-only batches, not idempotent on retry. Is a counter appropriate for money (VND)?
9. driver_locations ((driver_id), ts DESC) with TTL 1 day: tombstones; should TimeWindowCompactionStrategy and default_time_to_live be recommended?
10. drivers_by_area ((area, status), rating DESC, driver_id): changing status moves the row between partitions (DELETE + INSERT, logged BATCH); rating as a clustering column cannot be UPDATEd.
11. Docker image facts: default datacenter name; env vars supported by the image (CASSANDRA_DC, CASSANDRA_CLUSTER_NAME, CASSANDRA_ENDPOINT_SNITCH, ...); default authenticator (AllowAllAuthenticator?) and how PasswordAuthenticator + CREATE ROLE/GRANT could be enabled in this setup (relevant to rubric "quản trị người dùng").
12. Backup/restore in 4.1: nodetool snapshot / listsnapshots / clearsnapshot; incremental_backups; restore by copying snapshot SSTables + nodetool refresh vs nodetool import (added in 4.0) vs sstableloader; are nodetool, sstableloader and cqlsh present in the cassandra:4.1 image; cqlsh COPY TO/FROM options and limits; DESCRIBE KEYSPACE for schema backup.
13. "Chạy 3 node cần khoảng 4–6 GB RAM": sanity check with MAX_HEAP_SIZE=1G per node.
Report each as a finding. Record each verified fact useful for writing CASSANDRA.MD in facts_for_prompt2 with its source URL.`,
  { label: 'cassandra-41', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

const pPy = agent(`${CONTEXT}

YOUR SCOPE (id prefix "P"): the claim "Python 3.12 cần cassandra-driver ≥ 3.29" and whether the recommended stack "Python FastAPI + Jinja/Bootstrap" works on this Windows machine (Python 3.12.7).
Check: PyPI versions (run: python -m pip index versions cassandra-driver — read-only); the driver changelog (GitHub datastax/python-driver and/or apache/cassandra-python-driver CHANGELOG); the known problem "DependencyException: Unable to load a default connection class" on Python 3.12 (asyncore removed from stdlib; libev not available on Windows) — is the asyncio reactor picked automatically in current versions or must connection_class be set, or is the pyasyncore backport needed; whether Windows cp312 wheels exist.
EMPIRICAL PROBE ALLOWED: create a throwaway venv at ${X}/venv_probe, install cassandra-driver only (no other packages), then run: python -c "import cassandra; print(cassandra.__version__); from cassandra.cluster import Cluster; print(Cluster)" and report the exact output (and the reactor/connection class it would use if you can print it, e.g. from cassandra.cluster import Cluster; print(Cluster.connection_class)). Cassandra is not running: do not try to connect. Delete ${X}/venv_probe afterwards. Never install anything into the global Python or into the project folder.
Also briefly check the Node.js "cassandra-driver" npm package (maintained? latest version?) since it is the mentioned alternative.
Report findings; put install/compatibility facts in facts_for_prompt2 with sources.`,
  { label: 'python-driver', phase: 'Verify', schema: FINDINGS_SCHEMA, agentType: 'general-purpose' })

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

const pDesign = Promise.all([pShots, pCass]).then(([shots, cass]) => agent(`${CONTEXT}

YOUR SCOPE (id prefix "M"): adversarial query-first review of the Cassandra tables PROPOSED in prompt1_answer.md section 2 ("Các bảng thiết kế theo truy vấn") for the ride-hailing app. Use the data-modeling chapter (${X}/book_datamodel.txt: query-first design, Chebotko diagrams, partition size formulas) and the course slides.
Existing schema reconstructed from the draft screenshots by another checker (may be partial):
${JSON.stringify(shots ? { existing_schema: shots.existing_schema, environment: shots.environment } : 'unavailable')}
Verified Cassandra 4.1 facts from another checker:
${JSON.stringify(cass ? cass.facts_for_prompt2 : 'unavailable')}
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
