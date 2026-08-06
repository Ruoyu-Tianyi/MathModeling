#!/usr/bin/env python3
"""One-command publish: precheck -> build_docx -> Word COM PDF -> cleanup.

Usage:
    python publish.py <paper.md> [--lang zh|en] [--no-pdf]

Stops at the first failing stage. PDF export uses Word COM (Windows +
Office); silently skipped when Word is unavailable or --no-pdf is given.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def run(cmd, **kw):
    return subprocess.run(cmd, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper", help="path to paper.md")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--appendix-code", default=None, metavar="DIR",
                    help="forwarded to build_docx: embed .py files as appendix")
    args = ap.parse_args()
    md = Path(args.paper).resolve()
    if not md.is_file():
        print(f"ERROR: not found: {md}")
        return 1

    print("[1/4] precheck ...")
    r = run([sys.executable, str(SKILL_DIR / "precheck.py"), str(md), "--lang", args.lang])
    if r.returncode != 0:
        print("ABORT: fix precheck errors first")
        return 1

    print("[2/4] build docx ...")
    build_cmd = [sys.executable, str(SKILL_DIR / "build_docx.py"), str(md)]
    appendix_code = args.appendix_code
    if not appendix_code:
        # V3.7.2：未指定时自动探测项目 code/ 目录（<paper>/../code），
        # 附录嵌代码是国赛硬性期望，默认带上
        cand = md.parent.parent / "code"
        if cand.is_dir() and list(cand.glob("*.py")):
            appendix_code = str(cand)
            print(f"  appendix-code auto-detected: {cand}")
    if appendix_code:
        build_cmd += ["--appendix-code", appendix_code]
    r = run(build_cmd)
    if r.returncode != 0:
        print("ABORT: docx build failed")
        return 1
    docx = md.with_suffix(".docx")

    pdf = md.parent / f"{md.stem}_word.pdf"
    if args.no_pdf:
        print("[3/4] pdf export skipped (--no-pdf)")
    elif Path(POWERSHELL).is_file():
        print("[3/4] export pdf via Word COM ...")
        cmd = ("$w=New-Object -ComObject Word.Application;$w.Visible=$false;"
               f"$d=$w.Documents.Open('{docx}',$false,$true);"
               f"$d.SaveAs([ref]'{pdf}',[ref]17);"
               "$d.Close($false);$w.Quit()")
        docx_mtime = docx.stat().st_mtime

        def pdf_fresh():
            # V3.9：必须是本次导出的新 PDF——陈旧 PDF 会掩盖 COM 失败
            return pdf.is_file() and pdf.stat().st_mtime >= docx_mtime - 1

        try:
            if pdf.is_file():
                pdf.unlink()  # 先删陈旧 PDF，存在性检查才有意义
            r = run([POWERSHELL, "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and pdf_fresh():
                print(f"      PDF OK: {pdf}")
            else:
                err = (r.stderr or r.stdout or "").strip().splitlines()
                print(f"      PDF failed: {err[0][:160] if err else 'unknown COM error'}")
                print("      retrying once ...")
                r = run([POWERSHELL, "-NoProfile", "-Command", cmd],
                        capture_output=True, text=True, timeout=300)
                if r.returncode == 0 and pdf_fresh():
                    print(f"      PDF OK (retry): {pdf}")
                else:
                    print("      PDF skipped. 自查: ① Word 能否手动打开该 docx "
                          "② 是否有弹窗/保护视图 ③ 手动导出验证")
        except Exception as e:
            print(f"      PDF skipped ({type(e).__name__}: {e})")
    else:
        print("[3/4] pdf export skipped (no PowerShell/Word)")

    tmp = SKILL_DIR / "_math_tmp"
    if tmp.is_dir():
        shutil.rmtree(tmp)
    print("[4/4] temp cleaned")
    print(f"DONE: {docx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
