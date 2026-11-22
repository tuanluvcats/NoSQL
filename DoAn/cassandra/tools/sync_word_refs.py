"""Đồng bộ tài liệu tham khảo vào file Word chính (báo cáo giữa kỳ).

Việc làm:
  1. Sao lưu file Word chính sang "<tên> (trước khi đồng bộ TLTK).docx" (nếu chưa có).
  2. Ở Chương 1–4, dòng "Nguồn tham khảo: <URL>" chuyển thành "Nguồn tham khảo: [n]" (n theo thứ tự xuất hiện).
  3. Thay mục TÀI LIỆU THAM KHẢO bằng danh sách đánh số [1]–[N]: nguồn Chương 1–4 trước, nguồn Chương 5 sau.
Chạy: PYTHONUTF8=1 python DoAn\\cassandra\\tools\\sync_word_refs.py   (Word phải đóng file chính)
Chạy lại nhiều lần vẫn an toàn: dòng đã là [n] thì giữ nguyên, danh sách được dựng lại từ đầu.
"""
import copy
import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).parent))
from docx_lib import Builder  # noqa: E402
from refs import REFS, PRE_ORDER  # noqa: E402

DORAN = Path(__file__).resolve().parents[2]
MAIN = DORAN / 'Báo cáo giữa kỳ NoSQL về DbSchema và Apache Cassandra.docx'
BACKUP = DORAN / 'Báo cáo giữa kỳ NoSQL về DbSchema và Apache Cassandra (trước khi đồng bộ TLTK).docx'
ORDER = json.loads((Path(__file__).parent / 'ref_order.json').read_text(encoding='utf8'))
assert ORDER[:len(PRE_ORDER)] == PRE_ORDER, 'ref_order.json không khớp: chạy lại build_chuong5.py'

# URL trong Chương 1–4 -> khóa nguồn
URL_KEY = {
    'documentation/installation.html': 'c_install',
    'databases/cassandra': 'c_cassandra',
    'documentation/diagram.html': 'c_diagram',
    'documentation/schema-documentation.html': 'c_sdoc',
    'documentation/synchronize-database.html': 'c_syncdb',
    'documentation/random-data-generator.html': 'c_gen',
    'documentation/foreign-keys.html': 'c_fk',
    'documentation/schema-synchronization.html': 'c_sync',
    'documentation/git.html': 'c_git',
    'nosqlmanager.com/cassandra': 'c_nosqlm',
}

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)
    print('Đã sao lưu ->', BACKUP.name)

doc = Document(str(MAIN))
body = doc.element.body
paras = list(doc.paragraphs)

# ---- 2. dòng "Nguồn tham khảo" ----
changed = 0
for p in paras:
    t = p.text.strip()
    if not t.startswith('Nguồn tham khảo:'):
        continue
    if re.search(r'\[\d+\]\s*$', t):
        continue                      # đã chuyển rồi
    key = next((k for u, k in URL_KEY.items() if u in t), None)
    if key is None:
        print('BỎ QUA (không nhận ra nguồn):', t[:90])
        continue
    n = ORDER.index(key) + 1
    el = p._p
    runs = el.findall(qn('w:r'))
    label = runs[0]
    for child in list(el):
        if child.tag != qn('w:pPr') and child is not label:
            el.remove(child)
    new = copy.deepcopy(label)
    rpr = new.find(qn('w:rPr'))
    if rpr is not None:
        for tag in ('w:b', 'w:bCs'):
            for x in rpr.findall(qn(tag)):
                rpr.remove(x)
    for tnode in new.findall(qn('w:t')):
        new.remove(tnode)
    for tag in ('w:lastRenderedPageBreak',):
        for x in new.findall(qn(tag)):
            new.remove(x)
    from docx.oxml import OxmlElement
    tn = OxmlElement('w:t')
    tn.text = '[%d]' % n
    new.append(tn)
    el.append(new)
    changed += 1
print('Đã đổi %d dòng "Nguồn tham khảo" thành [n].' % changed)

# ---- 3. mục TÀI LIỆU THAM KHẢO ----
head = next(p for p in paras if p.text.strip().upper() == 'TÀI LIỆU THAM KHẢO')
sect = body.find(qn('w:sectPr'))
node = head._p.getnext()
while node is not None and node is not sect:
    nxt = node.getnext()
    body.remove(node)
    node = nxt
b = Builder(REFS)
for i, key in enumerate(ORDER, 1):
    b.raw_paragraph('<w:spacing w:after="80" w:line="360" w:lineRule="auto"/><w:ind w:left="567" w:hanging="567"/><w:jc w:val="both"/>',
                    b.run('[%d] ' % i) + b.run(REFS[key]))
for el in b.elements():
    sect.addprevious(el)
doc.save(str(MAIN))
print('Đã ghi %d tài liệu tham khảo vào %s' % (len(ORDER), MAIN.name))
