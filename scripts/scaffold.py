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

# V3.7 图题纪律：论文用图不带图内标题——题注以文本形式写在 md 图片行
# 下一行（"图 N: 标题"，编号全文连续），由 Word 样式统一字号。
# savefig 自动剥离 suptitle / ax.set_title 并提醒；子图只允许 (a)/(b)
# 式面板小标签，用 panel_tag() 添加（豁免剥离）。
#
# V3.7.1 字号纪律：图插进 Word 会等比缩小，图内文字跟着缩水。
# savefig(insert_cm=...) 按"目标插入宽度"反向放大图内字号，使插入
# Word 缩放后图内文字 ≈10 pt（五号）；图背景默认透明（无边框、无填充色）。


def _strip_titles(fig, name):
    """剥离图内标题（V3.7 纪律），panel_tag 标记的面板标签豁免。"""
    removed = []
    if getattr(fig, "_suptitle", None) is not None and fig._suptitle.get_text():
        removed.append(fig._suptitle.get_text())
        fig.suptitle("")
    for ax in fig.axes:
        if getattr(ax, "_v37_panel_tag", False):
            continue
        t = ax.get_title()
        if t:
            removed.append(t)
            ax.set_title("")
    if removed:
        print(f"[V3.7] {name}: 图内标题已移除 {removed} —— "
              f"请在 md 中补 '图 N: <标题>' 题注行")
    return removed


def _boost_fonts(fig, insert_cm, target_pt=10.0):
    """按插入宽度反向放大图内字号：fig 越宽、插入越窄，放大越多。

    目标：PNG 插入 Word 缩到 insert_cm 宽后，基准文字 ≈ target_pt。
    缩放比 scale = insert_cm / fig_width_cm；所有文字乘 1/scale，
    再乘 target_pt/10（rcParams 基准 10 pt）。

    V3.9 防重叠：
    - boost 封顶 1.5 —— 本函数只放大字形不改布局，过度放大必然重叠；
    - boost>1.15 且 x 刻度 ≥6 个时旋转刻度 40°，避免相邻刻度相撞；
    - flow() 等自缩放图（fig._v37_no_boost）跳过，禁止二次放大。
    """
    if getattr(fig, "_v37_no_boost", False):
        return
    fig_w_cm = fig.get_size_inches()[0] * 2.54
    scale = insert_cm / max(fig_w_cm, 1e-6)
    boost = (1.0 / scale) * (target_pt / 10.0) if scale < 0.999 else (target_pt / 10.0)
    boost = min(boost, 1.5)
    if abs(boost - 1.0) < 0.02:
        return
    for ax in fig.axes:
        items = ([ax.title, ax.xaxis.label, ax.yaxis.label]
                 + list(ax.get_xticklabels()) + list(ax.get_yticklabels())
                 + list(ax.texts))
        leg = ax.get_legend()
        if leg is not None:
            items += list(leg.get_texts())
        for t in items:
            t.set_fontsize(t.get_fontsize() * boost)
        xt = ax.get_xticklabels()
        if boost > 1.15 and len(xt) >= 6 and not getattr(ax, "_v37_no_rotate", False):
            for t in xt:
                t.set_rotation(40)
                t.set_ha("right")


def savefig(fig, name, dpi=300, insert_cm=12.0, transparent=True):
    """保存论文用图。

    insert_cm: 该图在 md 中指定的插入宽度（{w=14cm} → insert_cm=14），
               用于字号反缩放；未指定时按默认档 12 cm 估算。
    transparent: 图背景透明（无边框、无填充色，V3.7.1 默认）。
    """
    _strip_titles(fig, name)
    _boost_fonts(fig, insert_cm)
    if transparent:
        fig.patch.set_alpha(0.0)
        for ax in fig.axes:
            ax.patch.set_alpha(0.0)
    out = FIGDIR / name
    fig.savefig(out, bbox_inches="tight", dpi=dpi, transparent=transparent)
    print("fig saved:", out)
    return out


def panel_tag(ax, tag, loc="upper left", fontsize=10):
    """子图面板小标签 '(a)'/'(b)' —— 图内唯一允许的文字标识。"""
    ax.set_title(tag, fontsize=fontsize, loc=loc, fontweight="bold")
    ax._v37_panel_tag = True  # 标记为面板标签，_strip_titles 豁免
    return ax


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
    ax.tick_params(colors="#333333", labelsize=10)  # 基准 10pt（savefig 反缩放后即终稿字号）
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
         orientation="tb", phases=None, insert_cm=12.0):
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
             "fig_flow.png",
             phases=["数据", "预处理", "建模"])
        # V3.7 起 title 参数废弃：图题不写进图内，在 md 图片行下一行
        # 写 "图 N: 技术路线图" 题注。
    """
    import matplotlib.patches as mpatches

    tb = orientation != "lr"
    box_h, ec, fc = 0.95, "#2F5597", "#EAF2FB"
    label_of = {k: lab for layer in layers for k, lab in layer}
    nst = len(layers)

    def box_w(lab, k=1.0):
        # V3.9：盒宽随字号系数 k 同步放大，保证放大后的文字始终装得下
        return max(2.4 * k, 0.34 * k * len(str(lab)) + 1.0)

    def layout(k=1.0):
        """按字号系数 k 计算节点坐标与图幅（坐标/盒宽/间距全部随 k 缩放）。"""
        if tb:
            main_step = vgap * k

            def span(layer):
                return sum(box_w(l, k) for _, l in layer) + hgap * k * max(len(layer) - 1, 0)
        else:
            main_step = max(box_w(l, k) for layer in layers for _, l in layer) + max(hgap, 1.2) * k

            def span(layer):
                return len(layer) * (box_h + 0.55) * k - 0.55 * k
        pos, widths, maxw = {}, {}, 0.0
        for li, layer in enumerate(layers):
            total = span(layer)
            maxw = max(maxw, total)
            u = -total / 2
            for key, lab in layer:
                w = box_w(lab, k)
                if tb:
                    pos[key] = (u + w / 2, -li * main_step)
                    u += w + hgap * k
                else:
                    pos[key] = (li * main_step, -(u + box_h * k / 2))
                    u += (box_h + 0.55) * k
                widths[key] = w
        if tb:
            figw = min(max(7.5, maxw * 0.95 + (2.4 * k if phases else 0)), 16 * k)
            figh = max(2.2, nst * main_step * 0.62 + 0.3)
        else:
            figw = min(max(7.5, nst * main_step * 1.0), 16 * k)
            figh = max(2.2, maxw * 0.9 + 0.3 + (0.9 * k if phases else 0))
        return pos, widths, maxw, main_step, figw, figh

    # V3.9 自缩放：先按基准 10pt 布局估算图宽，推出放大系数 factor
    # （与 _boost_fonts 同公式、同 1.5 封顶），再按放大字号重新布局——
    # 布局一开始就为终稿字号设计，杜绝"先布局后放大字形"导致的重叠。
    _, _, _, _, figw0, _ = layout(1.0)
    factor = min(max(figw0 * 2.54 / max(insert_cm, 1e-6), 1.0), 1.5)
    pos, widths, maxw, main_step, figw, figh = layout(factor)
    fs = 10.0 * factor
    k = factor

    if title:
        # V3.7：title 参数已废弃（图题改走 md 题注行），不再渲染也不占版面
        print(f"[V3.7] flow(): title={title!r} 已忽略 —— 请在 md 中补 '图 N: {title}' 题注行")
        title = None
    fig, ax = plt.subplots(figsize=(figw, figh))
    fig._v37_no_boost = True  # 已按 factor 自缩放，_boost_fonts 不得二次放大
    for key, (cx, cy) in pos.items():
        w = widths[key]
        ax.add_patch(mpatches.FancyBboxPatch(
            (cx - w / 2, cy - box_h * k / 2), w, box_h * k,
            boxstyle=f"round,pad={0.08 * k}", fc=fc, ec=ec, lw=1.2))
        ax.text(cx, cy, label_of[key], ha="center", va="center", fontsize=fs)
    for e in edges:
        src, dst = e[0], e[1]
        x1, y1 = pos[src]; x2, y2 = pos[dst]
        ax.add_patch(mpatches.FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14 * k,
            color=ec, lw=1.1, shrinkA=26 * k, shrinkB=26 * k))
        if len(e) == 3:
            ax.text((x1 + x2) / 2 + 0.15 * k, (y1 + y2) / 2, str(e[2]),
                    fontsize=8 * k, color=ec)
    if phases:
        for li, ph in enumerate(phases):
            if ph is None:
                continue
            if tb:
                ax.text(-maxw / 2 - 1.2 * k, -li * main_step, str(ph), ha="right",
                        va="center", fontsize=9 * k, fontweight="bold", color=ec)
            else:
                ax.text(li * main_step, maxw / 2 + 1.0 * k, str(ph), ha="center",
                        fontsize=9 * k, fontweight="bold", color=ec)
    if tb:
        ax.set_xlim(-maxw / 2 - (2.8 * k if phases else 1.0 * k), maxw / 2 + 1.0 * k)
        ax.set_ylim(-nst * main_step, main_step * 0.4)
    else:
        half = max(widths.values()) / 2 + 0.8 * k
        ax.set_xlim(-half, (nst - 1) * main_step + half)
        ax.set_ylim(-maxw / 2 - 1.0 * k, maxw / 2 + (2.0 * k if phases else 1.0 * k))
    ax.axis("off")
    return savefig(fig, name, insert_cm=insert_cm)
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
