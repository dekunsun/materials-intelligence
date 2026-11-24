"""Per-target figure for the CSP random-removal control: which of the 11 targets each run recovers.

One row per target, one column per training run (PEROV seeds 42-44, then R1-R3). A filled dot means the run's
20 relaxed candidates include a consensus match (structure match with the reference space group); a hollow
ring means it does not. Column totals are the relaxed consensus counts the pre-registered decision used.

Reads <eval dir>/per_target_all_runs.csv (written by src/csp/r_decision.py) and the target compositions from
<eval dir>/R1_s42/raw/sample_meta.json. Writes <eval dir>/per_target_consensus.png.

Usage (repository root):
    .venv/bin/python -I src/csp/plot_r_control.py results/csp_r_eval_20261124T0335Z
"""
import csv
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

PEROV_C, R_C = "#eb6834", "#2a78d6"  # categorical slots 2 and 1 of the project palette (plot_screening.py)
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
RUNS = [("PEROV_s42", "42"), ("PEROV_s43", "43"), ("PEROV_s44", "44"),
        ("R1_s42", "42"), ("R2_s43", "43"), ("R3_s44", "44")]
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def pretty(formula: str) -> str:
    """'Ba2Er1Sb1O6' -> 'Ba₂ErSbO₆' (drop the 1s, subscript the rest)."""
    return re.sub(r"([A-Z][a-z]?)(\d+)", lambda m: m.group(1) + ("" if m.group(2) == "1" else m.group(2).translate(SUB)),
                  formula)


def main(eval_dir: str) -> None:
    ev = Path(eval_dir)
    rows = list(csv.DictReader(open(ev / "per_target_all_runs.csv")))
    comp = {t: pretty(v["input"]) for t, v in json.load(open(ev / "R1_s42/raw/sample_meta.json"))["targets"].items()}
    hit = {r["material_id"]: [r[f"{k}_consensus"] == "True" for k, _ in RUNS] for r in rows}
    # order: recovered by both arms, then by R only, then mixed, then by neither; ties by R count, then PEROV count
    order = sorted(hit, key=lambda t: (-(sum(hit[t][:3]) > 0 and sum(hit[t][3:]) > 0), -sum(hit[t][3:]), -sum(hit[t][:3]), t))

    xs = [0, 1, 2, 3.6, 4.6, 5.6]
    fig, ax = plt.subplots(figsize=(6.6, 6.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    n = len(order)
    for i, t in enumerate(order):
        y = n - 1 - i
        ax.axhline(y, color=GRID, lw=0.8, zorder=0)
        for j, (x, h) in enumerate(zip(xs, hit[t])):
            c = PEROV_C if j < 3 else R_C
            if h:
                ax.scatter(x, y, s=150, color=c, edgecolor=SURFACE, linewidth=2, zorder=3)
            else:
                ax.scatter(x, y, s=60, facecolor=SURFACE, edgecolor="#b8b6af", linewidth=1.2, zorder=2)
    totals = [sum(hit[t][j] for t in order) for j in range(6)]
    for x, tot in zip(xs, totals):
        ax.text(x, -1.15, str(tot), ha="center", va="center", fontsize=11, color=INK, fontweight="bold")
    ax.text(-0.75, -1.15, "consensus / 11", ha="right", va="center", fontsize=8.5, color=INK2)
    ax.axhline(-0.6, color=INK2, lw=0.8)

    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{comp[t]}  {t}" for t in reversed(order)], fontsize=8.5, color=INK)
    ax.set_xticks([])
    for x, (_, sd) in zip(xs, RUNS):
        ax.text(x, n - 0.35, f"seed {sd}", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xlim(-0.6, 6.2)
    ax.set_ylim(-1.6, n + 1.5)
    ax.text(1, n + 0.45, "PEROV\nperovskite frameworks removed", ha="center", va="bottom", fontsize=9, color=PEROV_C, fontweight="bold", linespacing=1.15)
    ax.text(4.6, n + 0.45, "R1–R3\nsame number removed at random", ha="center", va="bottom", fontsize=9, color=R_C, fontweight="bold", linespacing=1.15)

    fig.suptitle("Random removal keeps 8 of 11 targets on every seed;\nremoving the perovskite frameworks keeps 3–4",
                 x=0.02, y=0.995, ha="left", fontsize=12, color=INK, fontweight="bold")
    handles = [Line2D([], [], marker="o", ls="", markersize=9, markerfacecolor=INK2, markeredgecolor=SURFACE,
                      label="consensus: a match with the reference space group in the 20 relaxed candidates"),
               Line2D([], [], marker="o", ls="", markersize=6, markerfacecolor=SURFACE, markeredgecolor="#b8b6af",
                      label="no consensus match")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.02, 0.045), frameon=False, fontsize=7.5,
               labelcolor=INK2, ncol=1)
    fig.text(0.03, 0.012, "EquiCSP retrained from scratch, 106,000 steps per run; 11 targets of type 1:1:2:6. Pre-registered outcome: template_specific.",
             ha="left", va="bottom", fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.11, 1, 0.93))
    out = ev / "per_target_consensus.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(out, "totals", totals)


if __name__ == "__main__":
    main(sys.argv[1])
