#!/usr/bin/env python3
"""Build a CUMCM-standard .docx paper from paper.md (see references/format-spec.md).

Fully offline: math is rendered with matplotlib mathtext to embedded PNGs
(\tag{n} is stripped and re-attached as a right-aligned equation number);
figures are embedded from local paths; tables become 3-line tables.

Usage:
    python build_docx.py <paper.md> [--out paper.docx]

Markdown subset supported: #..#### headings, paragraphs, **bold**, - and 1.
lists, | tables |, ![caption](path), $$..$$ display math, $..$ inline math.
"""
import argparse
import io
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# ---------------- format spec (references/format-spec.md) -------------------
SPEC = {
    "title":   {"ea": "黑体", "ascii": "Times New Roman", "size": 16, "bold": True},
    "h1":      {"ea": "黑体", "ascii": "Times New Roman", "size": 14, "bold": True},
    "h2":      {"ea": "黑体", "ascii": "Times New Roman", "size": 12, "bold": True},
    "h3":      {"ea": "黑体", "ascii": "Times New Roman", "size": 12, "bold": True},
    "body":    {"ea": "宋体", "ascii": "Times New Roman", "size": 12, "bold": False},
    "caption": {"ea": "宋体", "ascii": "Times New Roman", "size": 10.5, "bold": False},
    "table":   {"ea": "宋体", "ascii": "Times New Roman", "size": 10.5, "bold": False},
}

MATH_IMG = Path(__file__).resolve().parent / "_math_tmp"
MATH_IMG.mkdir(exist_ok=True)
_math_counter = 0


def set_font(run, style):
    run.font.name = style["ascii"]
    run.font.size = Pt(style["size"])
    run.font.bold = style["bold"]
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), style["ea"])


def para(doc, style_key, align=None, indent_chars=0, line15=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    if align is not None:
        pf.alignment = align
    if line15:
        pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if indent_chars:
        # first-line indent measured in characters
        ind = OxmlElement("w:ind")
        ind.set(qn("w:firstLineChars"), str(indent_chars * 100))
        p._p.get_or_add_pPr().append(ind)
    return p


TAG_RE = re.compile(r"\\tag\{([^}]*)\}")


def math_png(latex, fontsize=12):
    """Render latex (no surrounding $) to a PNG; returns (path, w_px, h_px, tag)."""
    global _math_counter
    tag = None
    m = TAG_RE.search(latex)
    if m:
        tag = m.group(1)
        latex = TAG_RE.sub("", latex)
    latex = latex.replace(r"\dfrac", r"\frac").strip()
    latex = re.sub(r"\\le(?![a-zA-Z])", r"\\leq", latex)
    latex = re.sub(r"\\ge(?![a-zA-Z])", r"\\geq", latex)
    _math_counter += 1
    path = MATH_IMG / f"m{_math_counter}.png"
    fig = plt.figure(figsize=(0.1, 0.1))
    t = fig.text(0, 0, f"${latex}$", fontsize=fontsize)
    fig.canvas.draw()
    bbox = t.get_window_extent()
    plt.close(fig)
    fig = plt.figure(figsize=(max(bbox.width, 2) / 72, max(bbox.height, 2) / 72))
    fig.text(0, 0, f"${latex}$", fontsize=fontsize)
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.01, transparent=True)
    plt.close(fig)
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return str(path), w, h, tag


INLINE_MATH_RE = re.compile(r"\$([^$]+)\$")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
IMG_RE = re.compile(r"^!\[(.*?)\]\((.*?)\)\s*$")
CAPTION_RE = re.compile(r"^(图|表)\s*\d+\s*[:：]")


def add_runs(p, text, style, base_dir):
    """Add text runs to paragraph, handling $math$ and **bold**."""
    pos = 0
    for m in INLINE_MATH_RE.finditer(text):
        if m.start() > pos:
            _add_bold_aware(p, text[pos:m.start()], style)
        img, w, h, _ = math_png(m.group(1), fontsize=int(style["size"]))
        height_pt = style["size"] * 1.15
        run = p.add_run()
        run.add_picture(img, height=Pt(height_pt), width=Pt(height_pt * w / h))
        pos = m.end()
    if pos < len(text):
        _add_bold_aware(p, text[pos:], style)


def _add_bold_aware(p, text, style):
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            r = p.add_run(text[pos:m.start()]); set_font(r, style)
        r = p.add_run(m.group(1)); set_font(r, {**style, "bold": True})
        pos = m.end()
    if pos < len(text):
        r = p.add_run(text[pos:]); set_font(r, style)


def set_cell_border(cell, **kwargs):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge, on in kwargs.items():
        el = OxmlElement(f"w:{edge}")
        if on:
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "8")
        else:
            el.set(qn("w:val"), "nil")
        borders.append(el)
    tc_pr.append(borders)


def add_table(doc, rows):
    n_rows, n_cols = len(rows), len(rows[0])
    t = doc.add_table(rows=n_rows, cols=n_cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, cell_text in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            style = {**SPEC["table"], "bold": (i == 0)}
            add_runs(p, cell_text, style, None)
            set_cell_border(cell,
                            top=(i == 0), bottom=(i in (0, n_rows - 1)),
                            left=False, right=False,
                            insideH=False, insideV=False)
    return t


def build(md_path: Path, out_path: Path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin = sec.right_margin = Cm(3.17)

    base = md_path.parent
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1; continue
        # headings
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            key = {1: "title", 2: "h1", 3: "h2", 4: "h3"}[level]
            align = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else None
            p = para(doc, key, align=align)
            pf = p.paragraph_format
            pf.space_before = Pt(12 if level <= 2 else 6)
            pf.space_after = Pt(6)
            add_runs(p, text, SPEC[key], base)
            i += 1; continue
        # display math block $$ .. $$ (single or multi-line)
        if line.strip().startswith("$$"):
            buf = line.strip()[2:]
            while not buf.endswith("$$"):
                i += 1
                buf += lines[i].strip()
            latex = buf[:-2]
            img, w, h, tag = math_png(latex, fontsize=13)
            p = para(doc, "body", align=WD_ALIGN_PARAGRAPH.CENTER)
            run = p.add_run()
            max_w_cm, nat_w_cm = 14.0, w / 300 * 2.54
            scale = min(1.0, max_w_cm / max(nat_w_cm, 0.1))
            run.add_picture(img, width=Cm(nat_w_cm * scale),
                            height=Cm(h / 300 * 2.54 * scale))
            if tag:
                r = p.add_run("\t\t（" + tag + "）"); set_font(r, SPEC["body"])
            i += 1; continue
        # image
        m = IMG_RE.match(line.strip())
        if m:
            img_path = (base / m.group(2)).resolve()
            p = para(doc, "body", align=WD_ALIGN_PARAGRAPH.CENTER)
            run = p.add_run()
            run.add_picture(str(img_path), width=Cm(12.5))
            i += 1; continue
        # table block
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                add_table(doc, rows)
            continue
        # caption line (图 n：... / 表 n：...)
        if CAPTION_RE.match(line.strip()):
            p = para(doc, "caption", align=WD_ALIGN_PARAGRAPH.CENTER)
            add_runs(p, line.strip(), SPEC["caption"], base)
            i += 1; continue
        # list item
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            p = para(doc, "body", indent_chars=0)
            p.paragraph_format.left_indent = Cm(0.75)
            add_runs(p, m.group(2) + " " + m.group(3) if m.group(2) in "-*"
                     else m.group(2) + " " + m.group(3), SPEC["body"], base)
            i += 1; continue
        # normal paragraph
        p = para(doc, "body", indent_chars=2)
        add_runs(p, line.strip(), SPEC["body"], base)
        i += 1

    doc.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paper", help="path to paper.md")
    ap.add_argument("--out", default=None, help="output docx path")
    args = ap.parse_args()
    md = Path(args.paper)
    out = Path(args.out) if args.out else md.with_suffix(".docx")
    build(md, out)
    print(f"OK: {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    sys.exit(main())
