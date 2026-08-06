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
    # 独立成行的 "表 N 标题"（无冒号）不会被识别为题注——样式与分页绑定都失效
    for li, line in enumerate(lines):
        if re.match(r"^(图|表)\s*\d+\s+\S", line.strip()):
            warns.append(f"caption missing colon (line {li + 1}): "
                         f"'{line.strip()[:30]}' —— 用 '图/表 N: 标题' 形式")

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

    # --- thickness checks (V3.8，对照 deep-reasoning.md R6 深度档位自检) ------
    body = text.split("## 参考文献")[0]
    n_fig_body = len(IMG_MD_RE.findall(body))
    n_tab_body = len({m.group(1) for m in TAB_CAPTION_RE.finditer(body)})
    prose = re.sub(r"\$\$.+?\$\$", "M", body, flags=re.S)
    prose = re.sub(r"[!|`*#_\s\[\](){}<>:：;；,，.。/\\\-=$~^]", "", prose)
    page_est = len(prose) / 800 + 0.4 * n_fig_body + 0.35 * n_tab_body
    if page_est < 12:
        warns.append(f"thin body: ~{page_est:.0f} pages estimated "
                     f"(prose+figures+tables, expect >=12 for 获奖论文形态) —— "
                     f"按 R6 深度档位自检补分析增量，不要段落注水")
    n_eq_total = len(re.findall(r"\$\$.+?\$\$", body, re.S))
    if n_eq_total < 8:
        warns.append(f"low total display-math count ({n_eq_total}, expect >=8) —— "
                     f"推导链偏短，对照深化阶梯升级至少一个模型")
    # figure type diversity (heuristic on caption keywords)
    FIG_TYPES = {"流程/框架": r"流程|路线|链路|框架", "热力": r"热力",
                 "柱状/条形": r"柱状|条形|对比|MAE|区分度|重要性",
                 "折线/曲线": r"折线|曲线|趋势|扰动", "散点": r"散点|落点",
                 "雷达/画像": r"雷达|画像", "箱线": r"箱线", "饼图": r"饼"}
    caps = re.findall(r"(?m)^图\s*\d+[:：]\s*(.+)$", body)
    if n_fig_body >= 5:
        hit = {name for name, pat in FIG_TYPES.items()
               if any(re.search(pat, c) for c in caps)}
        if len(hit) <= 2:
            warns.append(f"low figure-type diversity {sorted(hit)} —— "
                         f"可视化方式要多样（散点/箱线/雷达/误差棒/扰动曲线等）")
    # model-section five-part completeness: each 问题 H3 needs 建立 + 求解/结果
    build_sec = re.search(r"##\s*模型的建立与求解\s*\n(.*?)(?=\n##\s|\Z)",
                          text, re.S)
    if build_sec:
        h3s = list(re.finditer(r"(?m)^###\s+(问题.+)$", build_sec.group(1)))
        for k, h in enumerate(h3s):
            seg = build_sec.group(1)[h.end():h3s[k + 1].start()
                                     if k + 1 < len(h3s) else None]
            has_build = re.search(r"(?m)^####\s+.*(建立|模型)", seg)
            has_solve = re.search(r"(?m)^####\s+.*(求解|结果)", seg)
            if not (has_build and has_solve):
                warns.append(f"model section incomplete: {h.group(1)[:24]} "
                             f"(五段式：建立→求解→结果→检验→小结)")

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

    # --- pseudo-math typography (V3.9) ---------------------------------------
    # 散文中的伪数学必须写成行内 LaTeX：p_FDR→$p_{\mathrm{FDR}}$、
    # χ²→$\chi^2$、裸 p=0.01→$p=0.01$。逐行检查，跳过代码块与 $$ 行，
    # 先剥离行内 $...$ 区间再匹配。
    PSEUDO_SUB_RE = re.compile(r"[A-Za-z]_[A-Za-z0-9一-鿿]+")
    UNICODE_MATH_RE = re.compile(r"[χΣ∑∏√≤≥≠∈]")
    BARE_STAT_RE = re.compile(r"(?<![$\w.])[pVFr]=\d")
    pm_sub, pm_uni, pm_bare = [], [], []
    in_code = False
    for li, line in enumerate(text.splitlines()):
        ls = line.strip()
        if ls.startswith("```"):
            in_code = not in_code
            continue
        if in_code or ls.startswith("$$"):
            continue
        plain = re.sub(r"\$[^$]+\$", "", line)  # 剥掉合法行内公式
        plain = IMG_MD_RE.sub("", plain)        # 图片路径（fig1_xxx.png）不算
        plain = re.sub(r"`[^`]+`", "", plain)   # 行内代码（文件名/变量）不算
        plain = re.sub(r"\S+\.(?:py|csv|png|jpg|xlsx|md|tex)\b", "", plain)  # 文件路径
        if PSEUDO_SUB_RE.search(plain):
            pm_sub.append(li + 1)
        if UNICODE_MATH_RE.search(plain):
            pm_uni.append(li + 1)
        if BARE_STAT_RE.search(plain):
            pm_bare.append(li + 1)
    if pm_sub:
        warns.append(f"pseudo subscript 'x_y' outside math (lines {pm_sub[:5]}) —— "
                     f"用 $x_{{y}}$ 行内公式，不要下划线拼写")
    if pm_uni:
        warns.append(f"unicode math char (χ/Σ/≤/≥...) outside math (lines {pm_uni[:5]}) —— "
                     f"用 $\\chi^2$、$\\le$ 等 LaTeX 符号")
    if pm_bare:
        warns.append(f"bare statistic 'p=0.01' outside math (lines {pm_bare[:5]}) —— "
                     f"统计量写 $p=0.01$ 保持字体统一")

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
