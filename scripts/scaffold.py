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

DIRS = ["problem", "data", "code", "figures", "results", "paper", "analysis"]

DERIVATIONS_MD = """# 推导稿（工作文档，不入最终论文）

> 制度见 references/deep-reasoning.md：纸面推导先行，代码只实现本文档的结论。

## 赛道判定

- 判定：B 型 / C 型 / 混合型（理由：）

## Q1 模型推导

### 定义与符号

<!-- 每个量：符号 / 定义域 / 量纲 -->

### 引理/中间结论

<!-- 可独立证明的小结论 -->

### 推导

<!-- 定义 → 引理 → 可解形式，每步一句话理由 -->

### 可解形式

<!-- 最终方程/算法的输入输出 -->

### 六检查记录

1. 量纲一致：
2. 退化检验：
3. 不变量：
4. 界与误差：
5. 良态性（奇异构型）：
6. 反例压力测试（≥3 个对抗场景）：

## Q2 模型推导

<!-- 同 Q1 结构 -->
"""

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


def savefig(fig, name, dpi=300):
    out = FIGDIR / name
    fig.savefig(out, bbox_inches="tight", dpi=dpi)
    print("fig saved:", out)
    return out


def paper_style(ax=None, grid=True):
    """White-background professional style for paper figures.

    Call AFTER plotting: paper_style() uses current axes when ax is None.
    Removes top/right spines, light-gray thin grid below artists.
    """
    import matplotlib.pyplot as _plt
    ax = ax or _plt.gca()
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#888888")
        ax.spines[side].set_linewidth(0.8)
    if grid:
        ax.grid(True, color="#DDDDDD", lw=0.6, alpha=0.8)
        ax.set_axisbelow(True)
    ax.tick_params(colors="#333333", labelsize=9)
    return ax


def draw_circle(ax, center, r, label=None, **kw):
    """Draw a circle (thin dark line by default). Returns the patch."""
    import matplotlib.patches as mp
    c = mp.Circle(center, r, fill=False, lw=1.0, color="#333333", **kw)
    ax.add_patch(c)
    if label:
        ax.text(center[0], center[1], label, ha="center", va="center", fontsize=9)
    return c


def mark_point(ax, p, label, color="#C00000", offset=(0.8, 0.6), s=28,
               fontsize=10, **kw):
    """Mark a geometry point with a label (offset in points)."""
    ax.scatter([p[0]], [p[1]], s=s, color=color, zorder=5, **kw)
    ax.annotate(label, (p[0], p[1]), textcoords="offset points",
                xytext=offset, fontsize=fontsize, color=color)


def mark_angle(ax, vertex, p1, p2, label=None, radius=None, color="#2F5597",
               fontsize=9, arc_kw=None):
    """Draw an angle arc at `vertex` between rays to p1 and p2, + label."""
    import numpy as np
    import matplotlib.patches as mp
    v = np.asarray(vertex, float)
    a = np.asarray(p1, float) - v
    b = np.asarray(p2, float) - v
    r = radius or 0.18 * min(np.linalg.norm(a), np.linalg.norm(b))
    t1 = np.degrees(np.arctan2(a[1], a[0]))
    t2 = np.degrees(np.arctan2(b[1], b[0]))
    sweep = (t2 - t1) % 360
    if sweep > 180:
        t1, sweep = t2, (t1 - t2) % 360
    ax.add_patch(mp.Arc(v, 2 * r, 2 * r, angle=0, theta1=t1,
                        theta2=t1 + sweep, color=color, lw=1.0, **(arc_kw or {})))
    if label:
        mid = np.radians(t1 + sweep / 2)
        ax.text(v[0] + 1.3 * r * np.cos(mid), v[1] + 1.3 * r * np.sin(mid),
                label, fontsize=fontsize, color=color, ha="center", va="center")


def flow(layers, edges, name, title=None, vgap=2.0, hgap=0.9,
         orientation="tb", phases=None):
    """Flowchart for 技术路线图 / 模型框架图 / 数据链路图.

    layers: [[(key, label), ...], ...]  # each inner list is one stage
    edges:  [(src_key, dst_key), ...] or [(src, dst, edge_label), ...]
    name:   output filename under figures/
    orientation: "tb" stages top-down (default); "lr" stages left-to-right
    phases: optional per-stage swimlane labels (list aligned with layers;
            None entries skipped). Shown left of rows (tb) / above columns (lr).

    Example:
        flow([[("a", "读取数据")], [("b", "清洗"), ("c", "EDA")], [("d", "建模")]],
             [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
             "fig_flow.png", title="技术路线图",
             phases=["数据", "预处理", "建模"])
    """
    import matplotlib.patches as mpatches

    tb = orientation != "lr"
    box_h, ec, fc = 0.95, "#2F5597", "#EAF2FB"
    label_of = {k: lab for layer in layers for k, lab in layer}

    def box_w(lab):
        return max(2.4, 0.34 * len(str(lab)) + 1.0)

    if tb:
        main_step = vgap

        def span(layer):
            return sum(box_w(l) for _, l in layer) + hgap * max(len(layer) - 1, 0)
    else:
        main_step = max(box_w(l) for layer in layers for _, l in layer) + max(hgap, 1.2)

        def span(layer):
            return len(layer) * (box_h + 0.55) - 0.55

    pos, widths, maxw = {}, {}, 0.0
    for li, layer in enumerate(layers):
        total = span(layer)
        maxw = max(maxw, total)
        u = -total / 2
        for key, lab in layer:
            w = box_w(lab)
            if tb:
                pos[key] = (u + w / 2, -li * main_step)
                u += w + hgap
            else:
                pos[key] = (li * main_step, -(u + box_h / 2))
                u += box_h + 0.55
            widths[key] = w

    nst = len(layers)
    if tb:
        figw = min(max(7.5, maxw * 0.95 + (2.4 if phases else 0)), 16)
        figh = max(2.2, nst * main_step * 0.62 + (0.9 if title else 0.3))
    else:
        figw = min(max(7.5, nst * main_step * 1.0), 16)
        figh = max(2.2, maxw * 0.9 + (0.9 if title else 0.3) + (0.9 if phases else 0))
    fig, ax = plt.subplots(figsize=(figw, figh))
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
    if phases:
        for li, ph in enumerate(phases):
            if ph is None:
                continue
            if tb:
                ax.text(-maxw / 2 - 1.2, -li * main_step, str(ph), ha="right",
                        va="center", fontsize=9, fontweight="bold", color=ec)
            else:
                ax.text(li * main_step, maxw / 2 + 1.0, str(ph), ha="center",
                        fontsize=9, fontweight="bold", color=ec)
    if title:
        ax.set_title(title, fontsize=12)
    if tb:
        ax.set_xlim(-maxw / 2 - (2.8 if phases else 1), maxw / 2 + 1)
        ax.set_ylim(-nst * main_step, main_step * 0.4)
    else:
        half = max(widths.values()) / 2 + 0.8
        ax.set_xlim(-half, (nst - 1) * main_step + half)
        ax.set_ylim(-maxw / 2 - 1, maxw / 2 + (2.0 if phases else 1))
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
    (root / "analysis" / "derivations.md").write_text(DERIVATIONS_MD, encoding="utf-8")

    # stats_utils.py：随 skill 发布的统计/ML 工具库（无 scipy/sklearn 环境自实现）
    su = Path(__file__).resolve().parent / "stats_utils.py"
    if su.is_file():
        shutil.copy(su, root / "code" / "stats_utils.py")
        print("  - code/stats_utils.py (statistics/ML toolbox)")
    else:
        print("  - WARN: stats_utils.py not found next to scaffold.py, skipped")

    print(f"OK: project created at {root}")
    for d in DIRS:
        print(f"  - {d}/")
    print("  - paper/paper.md (from template)")
    print("  - data/SOURCES.md")
    print("  - code/plot_setup.py (plot bootstrap)")
    print("  - analysis/derivations.md (deep-reasoning scratchpad)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
