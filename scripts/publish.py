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
    ap.add_argument("--mcm", action="store_true",
                    help="MCM mode: en precheck + mcm-template docx")
    ap.add_argument("--appendix-code", default=None, metavar="DIR",
                    help="forwarded to build_docx: embed .py files as appendix")
    args = ap.parse_args()
    md = Path(args.paper).resolve()
    if not md.is_file():
        print(f"ERROR: not found: {md}")
        return 1
    lang = "en" if args.mcm else args.lang

    print("[1/4] precheck ...")
    r = run([sys.executable, str(SKILL_DIR / "precheck.py"), str(md), "--lang", lang])
    if r.returncode != 0:
        print("ABORT: fix precheck errors first")
        return 1

    print("[2/4] build docx ...")
    build_cmd = [sys.executable, str(SKILL_DIR / "build_docx.py"), str(md)]
    if args.mcm:
        build_cmd += ["--mcm"]
    else:
        build_cmd += ["--lang", lang]
    if args.appendix_code:
        build_cmd += ["--appendix-code", args.appendix_code]
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
        try:
            r = run([POWERSHELL, "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and pdf.is_file():
                print(f"      PDF OK: {pdf}")
            else:
                print("      PDF skipped (Word COM failed)")
        except Exception as e:
            print(f"      PDF skipped ({type(e).__name__})")
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
