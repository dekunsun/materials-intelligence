"""Two panels for the thermal report.

Left: for seven commercially relevant high-kappa materials, the DFT reference,
the range of the five best models (by kappa_SRME), and measured values.
Right: leaderboard kappa_SRME vs recall@10 (share of the DFT top 10 the model
also ranks top 10) for all 62 models, with the best no-ML rule as a reference line.

Usage:
    .venv/bin/python src/thermal/plot_thermal.py results/<thermal_run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"   # palette slots 1-3, validated for the battery chart
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"


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
    ex = pd.read_csv(run / "experiment_comparison.csv").sort_values("k_dft").reset_index(drop=True)
    mm = pd.read_csv(run / "model_metrics.csv")
    rule = json.loads((run / "rule_baselines.json").read_text())["tetrahedral_then_lightest"]["recall@10"]

    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.9), facecolor=SURFACE, gridspec_kw={"width_ratios": [1.15, 1]})
    style(a); style(b)
    y = np.arange(len(ex))
    a.grid(axis="x", color=GRID, linewidth=0.8)
    a.scatter(ex.k_dft, y + 0.22, s=46, color=BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=3, label="DFT reference (benchmark)")
    a.hlines(y, ex.best5_min, ex.best5_max, color=GREEN, linewidth=5, label="Five best models by SRME (range)")
    a.hlines(y - 0.22, ex.exp_low, ex.exp_high, color=ORANGE, linewidth=2.5)
    lb = ex.exp_is_lower_bound.astype(bool).to_numpy()
    mid = ((ex.exp_low + ex.exp_high) / 2).to_numpy()
    a.scatter(mid[~lb], (y - 0.22)[~lb], s=46, marker="D", color=ORANGE, edgecolor=SURFACE, linewidth=1.5, zorder=3, label="Measured, single crystal or film")
    for yy, xx in zip((y - 0.22)[lb], mid[lb]):
        a.annotate("", xy=(xx * 1.18, yy), xytext=(xx, yy), arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 1.6})
        a.scatter([xx], [yy], s=46, marker="D", facecolor=SURFACE, edgecolor=ORANGE, linewidth=1.6, zorder=3)
        a.text(xx * 1.2, yy, "lower bound", va="center", fontsize=7.5, color=INK2)
    cg = ex.dropna(subset=["commercial_grade_low"])
    a.hlines(np.asarray(y)[ex.index.get_indexer(cg.index)] - 0.22, cg.commercial_grade_low, cg.commercial_grade_high,
             color=ORANGE, linewidth=2.5, linestyle=(0, (1, 1.2)), label="Measured, commercial bulk")
    a.set_xscale("log"); a.set_xlim(150, 1700)
    a.set_xticks([200, 300, 500, 1000]); a.set_xticklabels(["200", "300", "500", "1000"])
    a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a.set_yticks(y); a.set_yticklabels([f"{m} ({p.split(' ')[0]})" for m, p in zip(ex.material, ex.phase)], fontsize=9, color=INK)
    a.set_xlabel("Room-temperature lattice thermal conductivity (W/m·K, log scale)", fontsize=9, color=INK2)
    a.set_title("Top models sit within 6% of DFT;\nDFT is 10–27% below measurement for 6 of 7", fontsize=10.5, color=INK, loc="left")
    a.legend(loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK)

    b.grid(axis="y", color=GRID, linewidth=0.8)
    jitter = (np.random.default_rng(0).random(len(mm)) - 0.5) * 0.025
    b.scatter(mm.srme, mm["recall@10"] + jitter, s=34, color=BLUE, alpha=0.85, edgecolor=SURFACE, linewidth=1, zorder=3)
    b.axhline(rule, color=INK2, linestyle="--", linewidth=1.2)
    b.text(1.98, rule + 0.025, "No-ML rule: tetrahedral, then lightest atoms (misses BAs)", ha="right", fontsize=8, color=INK2)
    b.set_xlim(0, 2.02); b.set_ylim(0, 1.08)
    b.set_xlabel("Leaderboard κ_SRME (lower is better)", fontsize=9, color=INK2)
    b.set_ylabel("Share of DFT top 10 found in model's top 10", fontsize=9, color=INK2)
    med = float(mm.srme.median())
    b.axvline(med, color=GRID, linewidth=1.2)
    b.text(med + 0.02, 0.05, f"median SRME {med:.2f}", fontsize=7.5, color=INK2)
    b.set_title("Better half of the leaderboard:\n28 of 31 models find the same top 10", fontsize=10.5, color=INK, loc="left")

    fig.suptitle("On these 103 binaries, model choice barely changes the top 10; DFT vs measurement is the larger gap", x=0.01, ha="left", fontsize=13, color=INK, fontweight="bold")
    fig.text(0.01, 0.01, "Re-scored from published Matbench Discovery predictions (62 models, 103 phononDB-PBE binaries, 300 K). Right panel: small vertical jitter added.\n"
             "Measured values and sources: data/thermal/experimental_kappa.csv. Left panel is post-hoc (7 hand-picked materials).", fontsize=7.2, color=INK2)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    out = run / "thermal_summary.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
