#!/usr/bin/env python3
"""Initialize a math-modeling contest project directory.

Usage:
    python scaffold.py --name my-contest [--lang zh|en] [--root DIR]

Creates:
    <root>/<name>/
        problem/      # problem statement files go here
        data/         # raw data + SOURCES.md
        code/         # q1_*.py, q2_*.py, ...
        figures/      # fig1_*.png, ...
        results/      # numeric outputs
        paper/paper.md   # from bundled template
"""
import argparse
import shutil
import sys
from pathlib import Path

DIRS = ["problem", "data", "code", "figures", "results", "paper"]

PLOT_SETUP = '''"""Plot bootstrap for the managed Python runtime: sys.path + CJK fonts.

Usage in q*_*.py scripts:
    from plot_setup import plt, savefig
    ...
    savefig(fig, "fig1_desc.png")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))  # daimon_runtime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from daimon_runtime import setup_plot

setup_plot()

FIGDIR = Path(__file__).resolve().parent.parent / "figures"
FIGDIR.mkdir(exist_ok=True)


def savefig(fig, name):
    out = FIGDIR / name
    fig.savefig(out, bbox_inches="tight", dpi=150)
    print("fig saved:", out)
    return out
'''

SOURCES_MD = """# 数据来源记录 (Data Sources)

每条数据一行：文件 | 来源 | 接口/查询参数 | 取数时间 | 字段与单位说明
仿真数据标注 SIMULATED 并给出生成脚本与 seed。

| 文件 | 来源 | 接口/参数 | 取数时间 | 说明 |
|---|---|---|---|---|
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="project folder name")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    ap.add_argument("--root", default=".", help="parent directory (default: cwd)")
    args = ap.parse_args()

    root = Path(args.root).resolve() / args.name
    if root.exists():
        print(f"ERROR: {root} already exists", file=sys.stderr)
        return 1

    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    template = Path(__file__).resolve().parent.parent / "assets" / "paper-template.md"
    shutil.copy(template, root / "paper" / "paper.md")
    (root / "data" / "SOURCES.md").write_text(SOURCES_MD, encoding="utf-8")
    (root / "code" / "plot_setup.py").write_text(PLOT_SETUP, encoding="utf-8")

    print(f"OK: project created at {root}")
    for d in DIRS:
        print(f"  - {d}/")
    print("  - paper/paper.md (from template)")
    print("  - data/SOURCES.md")
    print("  - code/plot_setup.py (plot bootstrap)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
