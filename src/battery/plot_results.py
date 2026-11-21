"""Discovery curves: cumulative hits vs number of experiments, per policy.

Small multiples, one panel per split, shared y-axis, one shared legend (six
series). Three palette colours sit below 3:1 contrast on the surface, so the
report also carries the numbers as a table. Bands are 95% bootstrap intervals.

Usage:
    .venv/bin/python src/battery/plot_results.py results/<run_id> ["title"]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from battery.data import load_pool  # noqa: E402

# Reference categorical palette, slots 1-6 in fixed order (validated: light mode).
COLORS = {"random": "#2a78d6", "family_rule": "#eb6834", "bo_gp": "#1baf7a",
          "screen_rf": "#eda100", "bo_rf_prior": "#e87ba4", "rl_reinforce": "#008300"}
LABELS = {"random": "Random", "family_rule": "Family rule", "bo_gp": "BO (GP, no prior)",
          "screen_rf": "Screen (RF prior)", "bo_rf_prior": "BO + prior (RF)", "rl_reinforce": "RL (REINFORCE)"}
PANELS = [("official", "Official split · 112 candidates"),
          ("cv5", "5-fold CV · ~100 per fold"),
          ("family_oxide", "New family: oxides · 348 candidates, prior has no oxides"),
          ("family_sulfide", "New family: sulfides · 123 candidates, prior has no sulfides")]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"


def main() -> int:
    run = Path(sys.argv[1])
    title = sys.argv[2] if len(sys.argv) > 2 else "Cumulative hits by number of experiments"
    cfg = json.loads((run / "config.json").read_text())
    thr = cfg["primary_threshold_S_per_cm"]; lt = np.log10(thr); B = cfg["budget_experiments"]
    pool, _ = load_pool()
    y_of = dict(zip(pool.keys, pool.y))
    curves: dict[tuple[str, str], list[np.ndarray]] = {}
    for line in (run / "sequences.jsonl").open():
        r = json.loads(line)
        if r["threshold"] != thr:
            continue
        hits = np.cumsum([y_of[k] >= lt for k in r["queried"]])
        curves.setdefault((r["split"], r["method"]), []).append(hits)

    rng = np.random.default_rng(0)
    fig, axes2 = plt.subplots(2, 2, figsize=(11.5, 8.4), sharey="row", facecolor=SURFACE)
    axes = axes2.flatten()
    x = np.arange(1, B + 1)
    for ax, (split, name) in zip(axes, PANELS):
        ax.set_facecolor(SURFACE)
        for m, c in COLORS.items():
            arr = np.array(curves.get((split, m), []), dtype=float)
            if not len(arr):
                continue
            mean = arr.mean(0)
            boots = arr[rng.integers(0, len(arr), (1000, len(arr)))].mean(1)
            lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
            ax.fill_between(x, lo, hi, color=c, alpha=0.12, linewidth=0)
            ax.plot(x, mean, color=c, linewidth=2, label=LABELS[m])
        ax.set_title(name, fontsize=10.5, color=INK, loc="left")
        ax.set_xlim(0, B); ax.set_xlabel("Experiments run", fontsize=9, color=INK2)
        ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        for s in ["left", "bottom"]:
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=8.5)
    for a in (axes[0], axes[2]):
        a.set_ylabel(f"Compositions found ≥ {thr:g} S/cm", fontsize=9, color=INK2)
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, color=INK, fontweight="bold")
    fig.text(0.01, 0.005, "Lines: mean over campaigns. Bands: 95% bootstrap over campaigns (for 5-fold CV this is too narrow; fold-level intervals are in summary_v2.csv). "
             "Data: OBELiX (CC BY 4.0), room-temperature measured conductivity; retrospective, not new discovery.", fontsize=7.5, color=INK2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.01, 0.955), ncol=6, frameon=False,
               fontsize=9, labelcolor=INK, handlelength=1.6, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    fig.subplots_adjust(wspace=0.08, hspace=0.32)
    out = run / "discovery_curves.png"
    fig.savefig(out, dpi=160, facecolor=SURFACE)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
