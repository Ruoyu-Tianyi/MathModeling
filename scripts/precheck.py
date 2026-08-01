#!/usr/bin/env python3
"""Pre-submission checker for a math-modeling paper (Markdown).

Usage:
    python precheck.py paper/paper.md [--lang zh|en]

Exit code 0 = no ERROR; 1 = at least one ERROR. WARNs do not fail the check.
"""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_ZH = ["摘要", "关键词", "问题重述", "问题分析", "模型假设", "符号说明",
               "模型的建立与求解", "灵敏度", "模型评价", "参考文献"]
REQUIRED_EN = ["Summary", "Keywords", "Introduction", "Assumptions", "Notation",
               "Model", "Sensitivity", "Strengths", "References"]

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
TODO_RE = re.compile(r"TODO|FIXME|XXX|待补|待写|占位")
FIG_REF_RE = re.compile(r"图\s*(\d+)")
FIG_CAPTION_RE = re.compile(r"图\s*(\d+)\s*[:：]")
TAB_REF_RE = re.compile(r"表\s*(\d+)")
TAB_CAPTION_RE = re.compile(r"表\s*(\d+)\s*[:：]")
NUM_RE = re.compile(r"\d")
IMG_MD_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def check(path: Path, lang: str):
    text = path.read_text(encoding="utf-8")
    errors, warns = [], []

    required = REQUIRED_ZH if lang == "zh" else REQUIRED_EN
    for sec in required:
        if sec not in text:
            errors.append(f"missing section: {sec}")

    for m in PLACEHOLDER_RE.finditer(text):
        errors.append(f"unfilled placeholder: {m.group(0)}")
    for m in TODO_RE.finditer(text):
        warns.append(f"TODO-like residue: '{m.group(0)}'")

    # referenced image files must exist
    for m in IMG_MD_RE.finditer(text):
        img = (path.parent / m.group(1)).resolve()
        if not img.is_file():
            errors.append(f"missing image file: {m.group(1)}")

    # figure/table numbering: every caption should be referenced in text
    fig_caps = {m.group(1) for m in FIG_CAPTION_RE.finditer(text)}
    fig_refs = {m.group(1) for m in FIG_REF_RE.finditer(text)}
    for n in sorted(fig_caps - fig_refs, key=int):
        warns.append(f"figure 图{n} has caption but no in-text reference")
    tabs_caps = {m.group(1) for m in TAB_CAPTION_RE.finditer(text)}
    tabs_refs = {m.group(1) for m in TAB_REF_RE.finditer(text)}
    for n in sorted(tabs_caps - tabs_refs, key=int):
        warns.append(f"table 表{n} has caption but no in-text reference")

    # abstract sanity: length + contains digits (concrete results)
    abs_m = re.search(r"摘要\s*\n+(.*?)\n\s*\*\*关键词", text, re.S)
    if abs_m:
        body = re.sub(r"\$[^$]+\$", "M", abs_m.group(1))  # each formula ~1 char
        body = re.sub(r"[*`#_\s]", "", body)
        if not (150 <= len(body) <= 600):
            warns.append(f"abstract length {len(body)} chars (expect 150-600)")
        if not NUM_RE.search(body):
            errors.append("abstract contains no numeric result")
    elif "摘要" in text:
        warns.append("could not isolate abstract body for checks")

    if "灵敏度" not in text and "Sensitivity" not in text:
        errors.append("no sensitivity analysis section found")

    kw_m = re.search(r"关键词\*\*[：:]\s*(.+)", text)
    if kw_m:
        kws = re.split(r"[；;,，\s]+", kw_m.group(1).strip())
        if not (3 <= len([k for k in kws if k.strip()]) <= 6):
            warns.append(f"keyword count looks off: {kw_m.group(1).strip()}")

    # --- depth checks (math-writing.md) -------------------------------------
    # 1) formula density: display-math blocks inside each 建模 H3 section
    for m in re.finditer(r"####\s+.*?模型(?:的)?建立\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
                         text, re.S):
        n_eq = len(re.findall(r"\$\$.+?\$\$", m.group(1), re.S))
        if n_eq < 2:
            warns.append(f"low formula density ({n_eq}) in a 模型建立 section")
    # 2) thin sections: body < 3 content lines between consecutive headings
    parts = re.split(r"(?m)^(#{2,4}\s+.*)$", text)
    for k in range(1, len(parts) - 1, 2):
        head, body = parts[k], parts[k + 1]
        if not re.search(r"模型|问题|分析|求解", head):
            continue
        lines = [l for l in body.splitlines()
                 if l.strip() and not l.strip().startswith(("|", "!", "$$"))]
        if 0 < len(lines) < 3:
            warns.append(f"thin section (<3 lines): {head.strip()[:30]}")
    # 3) appendix must contain code
    if "附录" in text and "```" not in text:
        warns.append("appendix has no code block (consider --appendix-code)")

    # --- rigor checks (deep-reasoning.md, R5) --------------------------------
    # 4) assumptions count + each assumption should be referenced later
    am = re.search(r"模型假设\s*\n+(.*?)(?=\n##|\Z)", text, re.S)
    if am:
        items = re.findall(r"(?m)^\s*\d+\.\s", am.group(1))
        if len(items) < 3:
            warns.append(f"only {len(items)} assumptions (expect >=3)")
        body_after = text[am.end():]
        if "假设" not in body_after:
            warns.append("assumptions never referenced in later sections")
    # 5) symbol-table symbols should be used in the body
    sm = re.search(r"符号说明\s*\n+(\|.*?)(?=\n##|\Z)", text, re.S)
    if sm:
        rest = text[sm.end():]
        for row in sm.group(1).splitlines():
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0].startswith("$"):
                sym = cells[0].strip("$").replace("\\", "")
                if sym and not re.search(re.escape(sym[:1]), rest):
                    warns.append(f"symbol {cells[0]} defined but unused in body")

    return errors, warns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper", help="path to paper.md")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = ap.parse_args()

    path = Path(args.paper)
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    errors, warns = check(path, args.lang)
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN : {w}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    if not errors:
        print("PASS: no blocking issues")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
