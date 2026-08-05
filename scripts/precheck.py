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


# --- plagiarism self-check (N5) ----------------------------------------------
def _norm_text(t: str) -> str:
    return re.sub(r"[^\w一-鿿]", "", t.lower())


def _shingles(t: str, n: int = 8) -> set:
    return {t[i:i + n] for i in range(max(len(t) - n + 1, 0))}


def _problem_text(problem_dir: Path) -> str:
    buf = []
    for f in sorted(problem_dir.iterdir()):
        try:
            if f.suffix.lower() in (".txt", ".md"):
                buf.append(f.read_text(encoding="utf-8", errors="ignore"))
            elif f.suffix.lower() == ".pdf":
                from pypdf import PdfReader
                buf.append("".join(p.extract_text() or "" for p in PdfReader(str(f)).pages))
        except Exception:
            continue
    return "\n".join(buf)


def plagiarism_check(text: str, problem_dir: Path, lang: str):
    """Overlap between the restatement section and problem/ originals.
    Returns (status, ratio): status in {'ok','warn','error','skip'}."""
    sec_pat = (r"问题重述\s*\n+(.*?)(?=\n##|\Z)" if lang == "zh"
               else r"Introduction\s*\n+(.*?)(?=\n##|\Z)")
    m = re.search(sec_pat, text, re.S)
    if not m or not problem_dir.is_dir():
        return "skip", 0.0
    src = _problem_text(problem_dir)
    paper_sh = _shingles(_norm_text(m.group(1)))
    prob_sh = _shingles(_norm_text(src))
    if not paper_sh or not prob_sh:
        return "skip", 0.0
    ratio = len(paper_sh & prob_sh) / len(paper_sh)
    if ratio > 0.40:
        return "error", ratio
    if ratio > 0.25:
        return "warn", ratio
    return "ok", ratio


def check(path: Path, lang: str, problem_dir: Path = None):
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

    # --- figure caption discipline (V3.7) -------------------------------------
    # every image must be followed by a "图 N: ..." caption on the next
    # non-empty line; caption numbers must run 1..n without gaps/dups
    lines = text.splitlines()
    n_imgs = 0
    for li, line in enumerate(lines):
        if not IMG_MD_RE.search(line):
            continue
        n_imgs += 1
        nxt = ""
        for lj in range(li + 1, min(li + 4, len(lines))):
            if lines[lj].strip():
                nxt = lines[lj].strip()
                break
        if not FIG_CAPTION_RE.match(nxt):
            warns.append(f"figure without 图 N caption (line {li + 1}): "
                         f"{line.strip()[:40]}")
    for kind, cre in (("图", FIG_CAPTION_RE), ("表", TAB_CAPTION_RE)):
        seq = [int(m.group(1)) for m in cre.finditer(text)]
        if not seq:
            continue
        dups = sorted({n for n in seq if seq.count(n) > 1})
        if dups:
            warns.append(f"{kind} caption numbers duplicated: {dups}")
        expect = list(range(1, max(seq) + 1))
        missing = sorted(set(expect) - set(seq))
        if missing:
            warns.append(f"{kind} caption numbers not continuous, missing: {missing}")

    # abstract sanity: length + contains digits (concrete results)
    abs_m = re.search(r"摘要\s*\n+(.*?)\n\s*\*\*关键词", text, re.S)
    if abs_m:
        body = re.sub(r"\$[^$]+\$", "M", abs_m.group(1))  # each formula ~1 char
        body = re.sub(r"[*`#_\s]", "", body)
        if not (150 <= len(body) <= 800):
            warns.append(f"abstract length {len(body)} chars (expect 150-800)")
        if not NUM_RE.search(body):
            errors.append("abstract contains no numeric result")
    elif "摘要" in text:
        warns.append("could not isolate abstract body for checks")

    if "灵敏度" not in text and "Sensitivity" not in text:
        errors.append("no sensitivity analysis section found")

    kw_m = re.search(r"关键词\*\*[：:]\s*(.+)", text)
    if kw_m:
        kws = re.split(r"[；;,，]+", kw_m.group(1).strip())
        if not (3 <= len([k for k in kws if k.strip()]) <= 6):
            warns.append(f"keyword count looks off: {kw_m.group(1).strip()}")

    # --- depth checks (math-writing.md) -------------------------------------
    # 1) formula density: display-math blocks inside each 建模 H3 section
    for m in re.finditer(r"####\s+.*?模型(?:的)?建立\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
                         text, re.S):
        n_eq = len(re.findall(r"\$\$.+?\$\$", m.group(1), re.S))
        if n_eq < 2:
            warns.append(f"low formula density ({n_eq}) in a 模型建立 section")
    # 2) thin sections: prose under 120 chars between consecutive headings
    #    (judged by character volume, not line count — one long paragraph is fine)
    parts = re.split(r"(?m)^(#{2,4}\s+.*)$", text)
    for k in range(1, len(parts) - 1, 2):
        head, body = parts[k], parts[k + 1]
        if not re.search(r"模型|问题|分析|求解", head):
            continue
        prose = "".join(l for l in body.splitlines()
                        if l.strip() and not l.strip().startswith(("|", "!", "$$")))
        prose = re.sub(r"\$[^$]+\$", "M", prose)
        prose = re.sub(r"[*`#_\s]", "", prose)
        if 0 < len(prose) < 120:
            warns.append(f"thin section (<120 prose chars): {head.strip()[:30]}")
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

    # --- plagiarism check (N5) -----------------------------------------------
    pdir = problem_dir or (path.parent.parent / "problem")
    status, ratio = plagiarism_check(text, pdir, lang)
    if status == "error":
        errors.append(f"问题重述/Introduction overlap with problem statement: "
                      f"{ratio:.0%} (>40%, official rule: never copy the problem)")
    elif status == "warn":
        warns.append(f"restatement overlap {ratio:.0%} (>25%, rewrite in your own words)")

    return errors, warns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper", help="path to paper.md")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    ap.add_argument("--problem", default=None,
                    help="problem-statement dir for plagiarism check "
                         "(default: ../problem relative to paper/)")
    args = ap.parse_args()

    path = Path(args.paper)
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    errors, warns = check(path, args.lang,
                          Path(args.problem) if args.problem else None)
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
