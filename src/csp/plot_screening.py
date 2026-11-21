"""Three panels for the stability-screening report.

(a) Precision of a validation budget (top K% by predicted hull distance) vs K, for
    six models spanning the leaderboard, with the base rate as a reference line.
(b) Leaderboard F1 vs precision at a 1% budget, all models.
(c) Share truly stable among candidates in each band of PREDICTED hull distance
    (known before validation), for three models.

Usage:
    .venv/bin/python src/csp/plot_screening.py results/<csp_run_id>
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]   # validated slots 1-6
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
CURVE_MODELS = ["DPA-4.1-Max-OAM-PFT", "CHGNet", "MACE-MP-0", "M3GNet", "MEGNet", "Voronoi RF"]
BIN_MODELS = ["DPA-4.1-Max-OAM-PFT", "CHGNet", "MACE-MP-0"]
BANDS = [("pred <= -0.05", "Predicted ≤ −0.05"), ("-0.05 < pred <= 0", "Predicted −0.05 to 0"),
         ("0 < pred <= 0.05", "Predicted 0 to 0.05")]


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8.5)
    ax.set_axisbelow(True)


def main() -> int:
    run = Path(sys.argv[1])
    tk = pd.read_csv(run / "topk_curves.csv")
    tk = tk[tk.k_fraction.astype(str).str.match(r"^[0-9.]+$")].copy(); tk["k_fraction"] = tk.k_fraction.astype(float)
    mm = pd.read_csv(run / "model_metrics.csv")
    pb = pd.read_csv(run / "predicted_bands.csv")
    prev = float(mm.prevalence_rounded_ref.iloc[0])
    color = dict(zip(CURVE_MODELS, PALETTE))

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(14.5, 5.0), facecolor=SURFACE, gridspec_kw={"width_ratios": [1.15, 1, 1]})
    for ax in (a, b, c):
        style(ax)
    # (a)
    a.grid(axis="y", color=GRID, linewidth=0.8)
    for m in CURVE_MODELS:
        g = tk[tk.model == m].sort_values("k_fraction")
        x = g.k_fraction * 100
        a.fill_between(x, g.lo, g.hi, color=color[m], alpha=0.15, linewidth=0)
        a.plot(x, g.precision, color=color[m], linewidth=2, marker="o", markersize=4, label=m)
    a.axhline(prev, color=INK2, linestyle="--", linewidth=1.2)
    a.text(10, prev + 0.02, f"Base rate {prev:.1%} (random pick)", fontsize=8, color=INK2, ha="right")
    a.set_xscale("log"); a.set_xticks([0.1, 0.3, 1, 3, 10]); a.set_xticklabels(["0.1%\n(215)", "0.3%", "1%\n(2,155)", "3%", "10%\n(21,549)"])
    a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a.set_ylim(0, 1.04); a.set_xlabel("Validation budget: top share of 215,488 candidates", fontsize=9, color=INK2)
    a.set_ylabel("Share of budget that is DFT-stable", fontsize=9, color=INK2)
    a.set_title("Small budgets: most models fill them\nwith stable structures", fontsize=10.5, color=INK, loc="left")
    a.legend(loc="center left", bbox_to_anchor=(0.0, 0.42), frameon=False, fontsize=8, labelcolor=INK)
    # (b)
    b.grid(color=GRID, linewidth=0.8)
    b.scatter(mm.f1_uniq, mm["prec@0.01"], s=30, color=PALETTE[0], alpha=0.85, edgecolor=SURFACE, linewidth=1, zorder=3)
    for m, off in [("CHGNet", (6, -10)), ("MACE-MP-0", (-8, -14)), ("Voronoi RF", (6, -10))]:
        r = mm[mm.model == m].iloc[0]
        b.scatter([r.f1_uniq], [r["prec@0.01"]], s=46, facecolor="none", edgecolor=INK, linewidth=1.2, zorder=4)
        b.annotate(m, (r.f1_uniq, r["prec@0.01"]), xytext=off, textcoords="offset points", fontsize=8, color=INK2,
                   ha="right" if off[0] < 0 else "left")
    b.set_xlim(0.3, 0.96); b.set_ylim(0.4, 1.02)
    b.set_xlabel("Leaderboard F1 (unique prototypes)", fontsize=9, color=INK2)
    b.set_ylabel("Share DFT-stable at a 1% budget", fontsize=9, color=INK2)
    b.set_title("Above F1 ≈ 0.6, a 1% budget is 87–99%\nstable; F1 keeps separating models", fontsize=10.5, color=INK, loc="left")
    # (c)
    c.grid(axis="x", color=GRID, linewidth=0.8)
    for i, (band, name) in enumerate(BANDS):
        for j, m in enumerate(BIN_MODELS):
            r = pb[(pb.model == m) & (pb.band == band)].iloc[0]
            y = i + (j - 1) * 0.22
            c.scatter([r.share_truly_stable], [y], s=42, color=color[m], edgecolor=SURFACE, linewidth=1.2, zorder=3,
                      label=m if i == 0 else None)
            c.text(r.share_truly_stable + 0.015, y, f"n = {int(r.n):,}", va="center", fontsize=7, color=INK2)
    c.set_yticks(range(len(BANDS))); c.set_yticklabels([n + " eV/atom" for _, n in BANDS], fontsize=9, color=INK)
    c.invert_yaxis(); c.set_xlim(0, 1.15); c.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    c.set_xlabel("Share of candidates in the band that are DFT-stable", fontsize=9, color=INK2)
    c.set_title("Predicted just below the hull: top model\nright 91% of the time, CHGNet 39%", fontsize=10.5, color=INK, loc="left")
    c.legend(loc="lower right", frameon=False, fontsize=8, labelcolor=INK)

    fig.suptitle("Picking which AI candidates to validate: small budgets are easy for most models; past the confident picks, model quality decides",
                 x=0.01, ha="left", fontsize=12.5, color=INK, fontweight="bold")
    fig.text(0.01, 0.01, "Re-scored from published Matbench Discovery predictions (73 models; WBM unique prototypes, 215,488 structures). "
             "Truth = DFT hull distance, not synthesis.\nBands in (a): 95% cluster bootstrap over chemical systems. "
             "Base rate uses the leaderboard's rounded reference (15.5%; 15.3% unrounded).",
             fontsize=7.2, color=INK2)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    out = run / "screening_summary.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
