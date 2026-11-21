"""Tách văn bản CQL thành từng lệnh (tôn trọng chuỗi '...' và chú thích --)."""
from __future__ import annotations


def split_statements(text: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    in_str = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_str:
            buf.append(ch)
            if ch == "'":
                in_str = False  # cặp '' tự tắt rồi bật lại ở ký tự kế tiếp
            i += 1
            continue
        if ch == "'":
            in_str = True
            buf.append(ch)
        elif ch == "-" and text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out
