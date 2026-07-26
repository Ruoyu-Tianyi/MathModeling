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


def flow(layers, edges, name, title=None, vgap=2.0, hgap=0.9):
    """Top-down flowchart for the 技术路线图 / 问题分析 figure.

    layers: [[(key, label), ...], ...]  # each inner list is one row, top->down
    edges:  [(src_key, dst_key), ...] or [(src, dst, edge_label), ...]
    name:   output filename under figures/

    Example:
        flow([("s", "赛题")], [("s", "s")], "fig_flow.png")  # minimal
        flow([[("a", "读取数据")], [("b", "清洗"), ("c", "EDA")], [("d", "建模")]],
             [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
             "fig_flow.png", title="技术路线图")
    """
    import matplotlib.patches as mpatches

    label_of = {k: lab for layer in layers for k, lab in layer}

    def box_w(lab):
        return max(2.4, 0.34 * len(str(lab)) + 1.0)

    pos, widths, maxw = {}, {}, 0.0
    for li, layer in enumerate(layers):
        total = sum(box_w(lab) for _, lab in layer) + hgap * max(len(layer) - 1, 0)
        maxw = max(maxw, total)
        x = -total / 2
        for key, lab in layer:
            w = box_w(lab)
            pos[key] = (x + w / 2, -li * vgap)
            widths[key] = w
            x += w + hgap

    figw = min(max(7.5, maxw * 0.95), 16)
    figh = max(2.2, len(layers) * vgap * 0.62 + (0.9 if title else 0.3))
    fig, ax = plt.subplots(figsize=(figw, figh))
    box_h, ec, fc = 0.95, "#2F5597", "#EAF2FB"
    for key, (cx, cy) in pos.items():
        w = widths[key]
        ax.add_patch(mpatches.FancyBboxPatch(
            (cx - w / 2, cy - box_h / 2), w, box_h,
            boxstyle="round,pad=0.08", fc=fc, ec=ec, lw=1.2))
        ax.text(cx, cy, label_of[key], ha="center", va="center", fontsize=10)
    for e in edges:
        src, dst = e[0], e[1]
        x1, y1 = pos[src]; x2, y2 = pos[dst]
        ax.add_patch(mpatches.FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
            color=ec, lw=1.1, shrinkA=26, shrinkB=26))
        if len(e) == 3:
            ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2, str(e[2]), fontsize=8, color=ec)
    if title:
        ax.set_title(title, fontsize=12)
    ax.set_xlim(-maxw / 2 - 1, maxw / 2 + 1)
    ax.set_ylim(-len(layers) * vgap, vgap * 0.8)
    ax.axis("off")
    return savefig(fig, name)
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
