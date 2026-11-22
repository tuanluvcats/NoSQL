"""Thư viện dựng Chương 5 (Word) giữ đúng định dạng của báo cáo giữa kỳ.

Mẫu định dạng lấy từ chương 3 của file Word giữa kỳ (cùng styles.xml, numbering, header/footer):
  - tiêu đề chương: căn giữa, đậm, 16 pt, ngắt trang trước;
  - tiêu đề mục: đậm, spacing before=120 after=60;
  - "Bước N.": thụt trái 180, chữ "Bước N." đậm;
  - ảnh: đoạn căn giữa rồi chú thích bằng style "Caption VN" (nghiêng, căn giữa);
  - bảng: TableGrid, căn giữa, hàng tiêu đề tô D9EAF7, chú thích nằm DƯỚI bảng.
Khác với bản nháp (giãn dòng 1.15) ở chỗ: thân bài dùng 1.5 dòng theo yêu cầu của thang điểm.
"""
import re
from xml.sax.saxutils import escape

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

W = nsdecls('w')
FONT_EA = '<w:rFonts w:eastAsia="Times New Roman"/>'
CODE_FONT = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas" w:eastAsia="Consolas"/>'

INLINE_RE = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\{\{[^}]+\}\})')


class Builder:
    def __init__(self, references, preseed=()):
        self.blocks = []          # danh sách XML (chuỗi)
        self.refs = references    # key -> văn bản tài liệu tham khảo
        self.ref_order = list(preseed)   # key theo thứ tự xuất hiện lần đầu (có thể nạp sẵn nguồn của các chương trước)
        self.fig_n = 0
        self.tab_n = 0
        self.checklist = []       # (số hình, caption, việc cần làm, kết quả, công cụ, ưu tiên)
        self.chapter_no = 5

    # ---------- trích dẫn ----------
    def cite(self, spec):
        key, _, extra = spec.partition('|')
        if key not in self.refs:
            raise KeyError('Chưa khai báo tài liệu tham khảo: ' + key)
        if key not in self.ref_order:
            self.ref_order.append(key)
        n = self.ref_order.index(key) + 1
        return '[%d, %s]' % (n, extra.strip()) if extra.strip() else '[%d]' % n

    # ---------- run ----------
    def run(self, text, bold=False, italic=False, code=False, highlight=False, size=None):
        rpr = ''
        rpr += CODE_FONT if code else FONT_EA
        if bold:
            rpr += '<w:b/>'
        if italic:
            rpr += '<w:i/>'
        if code:
            rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size or 22, size or 22)
        elif size:
            rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size)
        if highlight:
            rpr += '<w:highlight w:val="yellow"/>'
        rpr += '<w:lang w:val="vi-VN"/>'
        return '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))

    def inline(self, text, bold=False, italic=False, size=None, code_size=22):
        out = []
        for part in INLINE_RE.split(text):
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                out.append(self.inline(part[2:-2], bold=True, italic=italic, size=size, code_size=code_size))
            elif part.startswith('`') and part.endswith('`'):
                out.append(self.run(part[1:-1], code=True, bold=bold, size=code_size))
            elif part.startswith('{{') and part.endswith('}}'):
                out.append(self.run(self.cite(part[2:-2]), bold=bold, italic=italic, size=size))
            else:
                out.append(self.run(part, bold=bold, italic=italic, size=size))
        return ''.join(out)

    # ---------- đoạn ----------
    def _p(self, ppr, runs):
        self.blocks.append('<w:p %s><w:pPr>%s</w:pPr>%s</w:p>' % (W, ppr, runs))

    def chapter(self, title):
        self._p('<w:pageBreakBefore/><w:spacing w:after="240"/><w:jc w:val="center"/>',
                self.run(title, bold=True, size=32))

    def h2(self, text):
        self._p('<w:keepNext/><w:spacing w:before="240" w:after="60"/>', self.inline(text, bold=True))

    def h3(self, text):
        self._p('<w:keepNext/><w:spacing w:before="120" w:after="60"/>', self.inline(text, bold=True))

    def para(self, text, italic=False):
        self._p('<w:spacing w:after="120" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/>',
                self.inline(text, italic=italic))

    def bullets(self, items):
        for it in items:
            self._p('<w:pStyle w:val="ListBullet"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="11"/></w:numPr>'
                    '<w:spacing w:after="60" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/>',
                    self.inline(it))

    def step(self, n, text):
        self._p('<w:spacing w:after="80" w:line="360" w:lineRule="auto"/><w:ind w:left="180" w:hanging="10"/><w:jc w:val="both"/>',
                self.run('Bước %d. ' % n, bold=True) + self.inline(text))

    def code(self, text, max_lines=None):
        lines = text.strip('\n').split('\n')
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines] + ['...']
        for i, ln in enumerate(lines):
            last = i == len(lines) - 1
            after = '120' if last else '0'
            self._p('<w:keepLines/>%s<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
                    '<w:spacing w:before="0" w:after="%s" w:line="240" w:lineRule="auto"/><w:ind w:left="397"/><w:jc w:val="left"/>'
                    % ('' if last else '<w:keepNext/>', after),
                    self.run(ln if ln else ' ', code=True, size=20))

    # ---------- hình ----------
    def _caption(self, label, seq, n, text):
        runs = self.run('%s %d.' % (label, self.chapter_no), italic=True)
        # trường SEQ để Word tự đánh lại số khi xóa/chèn hình (Ctrl+A, F9)
        fld = ('<w:r><w:rPr>%(f)s<w:i/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
               '<w:r><w:rPr>%(f)s<w:i/></w:rPr><w:instrText xml:space="preserve"> SEQ %(seq)s \\* ARABIC </w:instrText></w:r>'
               '<w:r><w:rPr>%(f)s<w:i/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
               '<w:r><w:rPr>%(f)s<w:i/><w:noProof/></w:rPr><w:t>%(n)d</w:t></w:r>'
               '<w:r><w:rPr>%(f)s<w:i/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>') % {'f': FONT_EA, 'seq': seq, 'n': n}
        runs += fld + self.run('. ' + text, italic=True)
        self._p('<w:pStyle w:val="CaptionVN"/><w:spacing w:after="200"/>', runs)

    def figure(self, caption, do, expect, tool, priority):
        """Chỗ trống để dán ảnh + chú thích. priority: 'Bắt buộc' | 'Nên có' | 'Tùy chọn'."""
        if priority == 'Tùy chọn':   # đã quyết định bỏ ảnh tùy chọn
            return
        self.fig_n += 1
        self._p('<w:keepNext/><w:spacing w:before="80" w:after="60"/><w:jc w:val="center"/>',
                self.run('[CHÈN ẢNH – %s] %s' % (priority, do.replace(chr(96), '')), italic=True, highlight=True, size=22))
        self._caption('Hình', 'HinhChuong5', self.fig_n, caption)
        self.checklist.append((self.fig_n, caption, do, expect, tool, priority))

    # ---------- bảng ----------
    def table(self, headers, rows, widths, caption):
        assert sum(widths) <= 9150, sum(widths)
        self.tab_n += 1

        def cell(text, w, head=False):
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="D9EAF7"/>' if head else ''
            ppr = '<w:spacing w:before="20" w:after="20" w:line="259" w:lineRule="auto"/><w:jc w:val="left"/>'
            body = self.inline(text, bold=head, code_size=18)
            return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s<w:vAlign w:val="%s"/></w:tcPr>'
                    '<w:p><w:pPr>%s</w:pPr>%s</w:p></w:tc>') % (w, shd, 'center' if head else 'top', ppr, body)

        grid = ''.join('<w:gridCol w:w="%d"/>' % w for w in widths)
        trs = ['<w:tr><w:trPr><w:cantSplit/><w:tblHeader/><w:jc w:val="center"/></w:trPr>%s</w:tr>'
               % ''.join(cell(h, w, True) for h, w in zip(headers, widths))]
        for r in rows:
            assert len(r) == len(widths), r
            trs.append('<w:tr><w:trPr><w:cantSplit/><w:jc w:val="center"/></w:trPr>%s</w:tr>'
                       % ''.join(cell(str(c), w) for c, w in zip(r, widths)))
        self.blocks.append(
            '<w:tbl %s><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
            '<w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" '
            'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>%s</w:tblGrid>%s</w:tbl>' % (W, grid, ''.join(trs)))
        self._p('<w:spacing w:before="0" w:after="0"/>', '')   # tách bảng khỏi chú thích
        self._caption('Bảng', 'BangChuong5', self.tab_n, caption)

    def page_break(self):
        self.blocks.append('<w:p %s><w:r><w:br w:type="page"/></w:r></w:p>' % W)

    def raw_paragraph(self, ppr, runs):
        self._p(ppr, runs)

    def elements(self):
        return [parse_xml(x) for x in self.blocks]
