#!/usr/bin/env python3
"""One-click EDA report for C-track (data-driven) problems (V3).

Reads a contest attachment (Excel/CSV) and produces:
  - overview stats (shape, dtypes, missing, duplicates)
  - distribution grid (hist + box for numeric columns)
  - correlation heatmap (numeric columns)
  - time-series panel (if a datetime column exists / --time-col given)
  - grouped boxplots (if a low-cardinality categorical column exists)
  - outlier counts (IQR rule)
  - eda-report.md with tables + an auto-generated findings list

CLI:
    python scripts/eda.py data/raw/attachment1.xlsx
    python scripts/eda.py data/raw/a.csv --out analysis/eda --time-col 日期 --group 品类

The report's findings list is the starting point for the paper's
"发现 1: ..." enumeration required by references/track-c-modeling.md.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- plot bootstrap: prefer the project's code/plot_setup.py ---------------
def _bootstrap_plot():
    here = Path(__file__).resolve().parent
    for cand in (here, Path.cwd() / "code", Path.cwd()):
        if (cand / "plot_setup.py").exists():
            sys.path.insert(0, str(cand))
            from plot_setup import plt, paper_style  # noqa
            return plt, paper_style
    sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        from daimon_runtime import setup_plot
        setup_plot()
    except Exception:
        for f in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC"):
            try:
                plt.rcParams["font.sans-serif"] = [f]
                break
            except Exception:
                pass
        plt.rcParams["axes.unicode_minus"] = False

    def paper_style(ax=None, grid=True):
        ax = ax or plt.gca()
        ax.set_facecolor("white")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        if grid:
            ax.grid(True, color="#DDDDDD", lw=0.6, alpha=0.8)
            ax.set_axisbelow(True)
        ax.tick_params(colors="#333333", labelsize=9)
        return ax
    return plt, paper_style


plt, paper_style = _bootstrap_plot()

MISS_HIGH = 0.20      # missing ratio flagged as "high"
CORR_HIGH = 0.90      # |r| flagged as collinear pair
SKEW_HIGH = 1.0       # |skew| flagged as strongly skewed
MAX_DIST_COLS = 12    # distribution grid capacity
MAX_TS_COLS = 4       # time-series panel capacity
MAX_GROUP_LEVELS = 12


# ---------------------------------------------------------------------------
def read_table(path: Path, sheet=0) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=sheet)
    for enc in ("utf-8", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="ignore")


def classify_columns(df: pd.DataFrame, time_col=None):
    dt_cols, num_cols, cat_cols = [], [], []
    for c in df.columns:
        if time_col and c == time_col:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            dt_cols.append(c)
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            dt_cols.append(c)
        elif pd.api.types.is_numeric_dtype(df[c]):
            num_cols.append(c)
        else:
            coerced = pd.to_numeric(df[c], errors="coerce")
            if coerced.notna().mean() > 0.9 and df[c].notna().mean() > 0:
                df[c] = coerced
                num_cols.append(c)
            else:
                cat_cols.append(c)
    return dt_cols, num_cols, cat_cols


def iqr_outliers(s: pd.Series):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((s < lo) | (s > hi)).sum()), lo, hi


# ---------------------------------------------------------------------------
def fig_distributions(df, num_cols, figdir):
    cols = num_cols[:MAX_DIST_COLS]
    n = len(cols)
    ncols = 4 if n > 6 else (3 if n > 2 else n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows * 2, ncols,
                             figsize=(3.1 * ncols, 2.1 * nrows * 2),
                             squeeze=False)
    for i, c in enumerate(cols):
        r, k = divmod(i, ncols)
        s = df[c].dropna()
        axes[2 * r][k].hist(s, bins=30, color="#2F5597", alpha=0.85, lw=0)
        axes[2 * r][k].set_title(str(c), fontsize=9)
        paper_style(axes[2 * r][k])
        axes[2 * r + 1][k].boxplot(s, vert=False, widths=0.5,
                                   medianprops={"color": "#C00000"})
        paper_style(axes[2 * r + 1][k])
    for j in range(n, nrows * ncols):
        r, k = divmod(j, ncols)
        axes[2 * r][k].axis("off")
        axes[2 * r + 1][k].axis("off")
    fig.tight_layout()
    out = figdir / "eda_distributions.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


def fig_correlation(df, num_cols, figdir):
    corr = df[num_cols].corr()
    n = len(num_cols)
    fig, ax = plt.subplots(figsize=(max(6, n * 0.55), max(5, n * 0.5)))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(n), [str(c)[:12] for c in num_cols], rotation=45,
                  ha="right", fontsize=8)
    ax.set_yticks(range(n), [str(c)[:12] for c in num_cols], fontsize=8)
    if n <= 12:
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center",
                        va="center", fontsize=7,
                        color="white" if abs(corr.iloc[i, j]) > 0.6 else "black")
    fig.colorbar(im, shrink=0.8)
    ax.set_title("相关系数矩阵", fontsize=11)
    fig.tight_layout()
    out = figdir / "eda_correlation.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out, corr


def fig_timeseries(df, tcol, num_cols, figdir):
    cols = num_cols[:MAX_TS_COLS]
    d = df[[tcol] + cols].dropna(subset=[tcol]).sort_values(tcol)
    fig, axes = plt.subplots(len(cols), 1,
                             figsize=(8, 2.2 * len(cols)), squeeze=False)
    for i, c in enumerate(cols):
        ax = axes[i][0]
        ax.plot(d[tcol], d[c], lw=0.9, color="#2F5597", alpha=0.85)
        if len(d) >= 10:
            ax.plot(d[tcol], d[c].rolling(max(3, len(d) // 20)).mean(),
                    lw=1.6, color="#C00000", label="滑动平均")
            ax.legend(fontsize=8, frameon=False)
        ax.set_title(str(c), fontsize=9)
        paper_style(ax)
    fig.tight_layout()
    out = figdir / "eda_timeseries.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


def fig_grouped(df, gcol, num_cols, figdir):
    cols = num_cols[:4]
    top = df[gcol].value_counts().head(MAX_GROUP_LEVELS).index
    d = df[df[gcol].isin(top)]
    fig, axes = plt.subplots(1, len(cols), figsize=(3.4 * len(cols), 3.2),
                             squeeze=False)
    for i, c in enumerate(cols):
        data = [d.loc[d[gcol] == g, c].dropna() for g in top]
        axes[0][i].boxplot(data, tick_labels=[str(g)[:8] for g in top],
                           medianprops={"color": "#C00000"})
        axes[0][i].set_title(str(c), fontsize=9)
        axes[0][i].tick_params(axis="x", rotation=45, labelsize=7)
        paper_style(axes[0][i])
    fig.tight_layout()
    out = figdir / "eda_grouped.png"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
def build_report(df, dt_cols, num_cols, cat_cols, corr, findings, figs,
                 src: Path):
    miss = df.isna().sum()
    lines = ["# EDA 报告（自动生成）", "",
             f"- 数据文件：`{src.name}`", f"- 规模：{df.shape[0]} 行 × {df.shape[1]} 列",
             f"- 数值列 {len(num_cols)} | 类别列 {len(cat_cols)} | 时间列 {len(dt_cols)}",
             f"- 重复行：{int(df.duplicated().sum())}", "",
             "## 缺失情况", "", "| 列 | 类型 | 缺失数 | 缺失率 |", "|---|---|---|---|"]
    for c in df.columns:
        m = miss[c]
        if m > 0:
            kind = ("数值" if c in num_cols else "时间" if c in dt_cols else "类别")
            lines.append(f"| {c} | {kind} | {m} | {m / len(df):.1%} |")
    if (miss == 0).all():
        lines.append("| （无缺失） | - | 0 | 0% |")
    lines += ["", "## 数值列统计", "",
              "| 列 | 均值 | 标准差 | 最小 | 中位 | 最大 | 偏度 | IQR异常点数 |",
              "|---|---|---|---|---|---|---|---|"]
    for c in num_cols:
        s = df[c].dropna()
        n_out, _, _ = iqr_outliers(s)
        lines.append(f"| {c} | {s.mean():.4g} | {s.std():.4g} | {s.min():.4g} "
                     f"| {s.median():.4g} | {s.max():.4g} | {s.skew():.2f} | {n_out} |")
    lines += ["", "## 图清单", ""]
    for f in figs:
        lines.append(f"- `{f.name}`")
    lines += ["", "## 自动发现列表（人工复核后写入论文）", ""]
    for i, f in enumerate(findings, 1):
        lines.append(f"- 发现 {i}：{f}")
    lines.append("")
    return "\n".join(lines)


def make_findings(df, num_cols, corr):
    f = []
    miss = df.isna().mean()
    for c in df.columns[(miss > MISS_HIGH)]:
        f.append(f"列 `{c}` 缺失率 {miss[c]:.0%}（>{MISS_HIGH:.0%}），需在数据预处理节说明处理规则")
    dup = int(df.duplicated().sum())
    if dup:
        f.append(f"存在 {dup} 条完全重复行，清洗时剔除并记录")
    if corr is not None:
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                r = corr.iloc[i, j]
                if abs(r) > CORR_HIGH:
                    f.append(f"`{cols[i]}` 与 `{cols[j]}` 相关系数 {r:.2f}，"
                             f"存在共线性风险，建模前需剔除或合并其一（VIF 复核）")
    for c in num_cols:
        sk = df[c].dropna().skew()
        if abs(sk) > SKEW_HIGH:
            f.append(f"`{c}` 偏度 {sk:.2f}，明显偏态，考虑对数/Box-Cox 变换")
    outs = {c: iqr_outliers(df[c].dropna())[0] for c in num_cols}
    big = {c: n for c, n in outs.items() if n > len(df) * 0.02}
    for c, n in big.items():
        f.append(f"`{c}` IQR 异常点 {n} 个（占比 {n / len(df):.1%}），需业务判断剔除或截尾")
    if not f:
        f.append("数据质量整体良好，无高缺失/强共线/重偏态列；可直接进入建模阶段")
    return f


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="C-track one-click EDA report")
    ap.add_argument("table", help="Excel/CSV file path")
    ap.add_argument("--out", default="analysis/eda", help="output directory")
    ap.add_argument("--sheet", default=0, help="Excel sheet name/index")
    ap.add_argument("--time-col", default=None, help="datetime column name")
    ap.add_argument("--group", default=None, help="categorical group column")
    args = ap.parse_args()

    src = Path(args.table)
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 1
    out_dir = Path(args.out)
    figdir = out_dir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    sheet = args.sheet
    try:
        sheet = int(sheet)
    except (TypeError, ValueError):
        pass
    df = read_table(src, sheet)
    dt_cols, num_cols, cat_cols = classify_columns(df, args.time_col)

    figs = []
    if num_cols:
        figs.append(fig_distributions(df, num_cols, figdir))
    corr = None
    if len(num_cols) >= 2:
        f, corr = fig_correlation(df, num_cols, figdir)
        figs.append(f)
    tcol = args.time_col if args.time_col in dt_cols else (dt_cols[0] if dt_cols else None)
    if tcol and num_cols:
        figs.append(fig_timeseries(df, tcol, num_cols, figdir))
    gcol = args.group
    if not gcol:
        low_card = [c for c in cat_cols if 2 <= df[c].nunique() <= MAX_GROUP_LEVELS]
        gcol = low_card[0] if low_card else None
    if gcol and num_cols:
        figs.append(fig_grouped(df, gcol, num_cols, figdir))

    findings = make_findings(df, num_cols, corr)
    report = build_report(df, dt_cols, num_cols, cat_cols, corr, findings, figs, src)
    rpt = out_dir / "eda-report.md"
    rpt.write_text(report, encoding="utf-8")

    print(f"rows={df.shape[0]} cols={df.shape[1]} "
          f"numeric={len(num_cols)} cat={len(cat_cols)} time={len(dt_cols)}")
    for f in figs:
        print("fig saved:", f)
    print("report:", rpt)
    print("findings:", len(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
