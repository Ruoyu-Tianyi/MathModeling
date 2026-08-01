#!/usr/bin/env python3
"""Parametric sensitivity analysis (N4): sweep a solver over ±5%~20%
parameter perturbations, output a perturbation curve and a change table.

Library usage in your q*_*.py:
    from sensitivity import sweep, report, sweep_multi, tornado

    def solve(x):                      # x = perturbed parameter value
        ...                            # rerun the model
        return {"cost": c, "time": t}  # float or dict of metrics

    res = sweep(solve, base=100.0, label="demand (units)")
    report(res, "fig_sens_demand.png", ylabel="relative change / %")

    # multiple parameters -> tornado chart:
    outs = sweep_multi({"demand": solve_d, "price": solve_p}, base=1.0)
    tornado(outs, "fig_tornado.png")

CLI self-test:  python sensitivity.py --demo
Rules: fix random seeds inside your solver; base run is the 1.0 ratio point.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_setup import plt, savefig, paper_style  # noqa: E402

RATIOS = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]


def sweep(fn, base, ratios=None, label="parameter"):
    """Run fn(base*r) for each ratio. fn returns float or dict[str, float]."""
    ratios = ratios or RATIOS
    points = []
    for r in ratios:
        out = fn(base * r)
        if isinstance(out, dict):
            points.append((r, out))
        else:
            points.append((r, {"value": float(out)}))
    base_out = points[ratios.index(1.00)][1] if 1.00 in ratios else None
    return {"label": label, "base": base, "ratios": ratios,
            "base_out": base_out, "points": points}


def _rel_changes(res):
    """{metric: [(ratio, pct_change)]} relative to the base point."""
    metrics = res["points"][0][1].keys()
    base = res["base_out"] or res["points"][len(res["points"]) // 2][1]
    out = {}
    for m in metrics:
        b = base[m]
        out[m] = [(r, 0.0 if b == 0 else (p[m] - b) / abs(b) * 100.0)
                  for r, p in res["points"]]
    return out


def report(res, name, ylabel="relative change / %", results_dir=None):
    """Perturbation curve + markdown table. Returns the table text."""
    rel = _rel_changes(res)
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for m, series in rel.items():
        ax.plot([r for r, _ in series], [v for _, v in series], "o-", ms=4, label=m)
    ax.axhline(0, color="#888888", lw=0.8)
    ax.set_xlabel(f"{res['label']} (ratio to base {res['base']:g})")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Sensitivity: {res['label']}")
    ax.legend(fontsize=9)
    paper_style(ax)
    savefig(fig, name)

    header = "| ratio | " + " | ".join(rel.keys()) + " |"
    sep = "|" + "---|" * (len(rel) + 1)
    lines = [header, sep]
    for i, r in enumerate(res["ratios"]):
        row = f"| {r:.2f} | " + " | ".join(f"{rel[m][i][1]:+.2f}%" for m in rel) + " |"
        lines.append(row)
    table = "\n".join(lines)
    print(table)
    if results_dir:
        Path(results_dir).mkdir(exist_ok=True)
        out = Path(results_dir) / (Path(name).stem + ".md")
        out.write_text(f"# Sensitivity: {res['label']}\n\n{table}\n", encoding="utf-8")
        print("table saved:", out)
    return table


def sweep_multi(fns, base=1.0, ratios=None):
    """{name: fn} -> {name: max_abs_deviation_pct, series}."""
    out = {}
    for k, fn in fns.items():
        res = sweep(fn, base, ratios, label=k)
        rel = _rel_changes(res)
        dev = max(abs(v) for series in rel.values() for _, v in series)
        out[k] = {"res": res, "max_dev": dev}
    return out


def tornado(multi, name):
    """Tornado bar chart: max |deviation| per parameter (sorted)."""
    items = sorted(multi.items(), key=lambda kv: kv[1]["max_dev"])
    fig, ax = plt.subplots(figsize=(6.6, 0.7 * len(items) + 1.8))
    ax.barh([k for k, _ in items], [v["max_dev"] for _, v in items],
            color="#2F5597", alpha=0.85, height=0.55)
    ax.set_xlabel("max |change| under ±20% perturbation / %")
    ax.set_title("Parameter sensitivity (tornado)")
    paper_style(ax, grid=False)
    ax.grid(axis="x", color="#DDDDDD", lw=0.6)
    savefig(fig, name)


def _demo():
    def fn(x):
        return {"cost": (x - 2.0) ** 2 + 5.0, "margin": 10.0 - 0.3 * x}
    res = sweep(fn, base=1.0, label="demo param")
    report(res, "sens_demo.png")
    outs = sweep_multi({"alpha": fn,
                        "beta": lambda x: {"cost": 5 + (x - 1) ** 3, "margin": 9 - x},
                        "gamma": lambda x: 3 + 0.1 * x})
    tornado(outs, "sens_tornado.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run self-test")
    args = ap.parse_args()
    if args.demo:
        _demo()
    else:
        ap.print_help()
