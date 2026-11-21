"""Re-summarize a finished run without re-running any campaign.

Added after an independent review of run battery_20261121T080824Z found that
the run's own summary.csv treated the 50 cv5 campaigns (10 seeds x 5 folds) as
independent, which makes intervals too narrow. This script writes
summary_v2.csv with:

  * cv5 intervals from a two-stage cluster bootstrap: resample folds, then
    average each chosen fold's seeds. Other splits keep the campaign bootstrap.
  * the share of campaigns censored (no fifth hit / no first hit within budget),
    so a censored mean is never read as a measured one.
  * the share of the hit gap over random that each method closes.
  * success rates (share of campaigns that reached the target within budget)
    and the mean among successful campaigns only, so a censored campaign is
    never read as one that took exactly budget+1 experiments.

Also works on the series-grouped runs from run_grouped.py (split "cv5_grouped").

Usage:
    .venv/bin/python src/battery/analyze.py results/<run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = ["first_hit", "to_5_hits", "hits@10", "hits@20", "hits@40"]


def campaign_ci(x: np.ndarray, rng, n=2000):
    if np.all(x == x[0]):
        return float(x[0]), float(x[0])
    m = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cluster_ci(g: pd.DataFrame, col: str, rng, n=2000):
    folds = g.fold.unique()
    by_fold = {f: g.loc[g.fold == f, col].to_numpy() for f in folds}
    means = []
    for _ in range(n):
        pick = rng.choice(folds, size=len(folds), replace=True)
        means.append(np.mean([by_fold[f].mean() for f in pick]))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    run = Path(sys.argv[1])
    budget = json.loads((run / "config.json").read_text())["budget_experiments"]
    df = pd.read_csv(run / "scores.csv")
    rng = np.random.default_rng(2026)
    rows = []
    for (split, thr, method), g in df.groupby(["split", "threshold", "method"]):
        rec = {"split": split, "threshold": thr, "method": method, "n_campaigns": len(g),
               "ci_method": "cluster bootstrap over folds" if split.startswith("cv5") else "bootstrap over campaigns",
               "censored_first_hit_share": float((g.first_hit > budget).mean()),
               "censored_to_5_share": float((g.to_5_hits > budget).mean()),
               "success_first_hit_share": float((g.first_hit <= budget).mean()),
               "success_to_5_share": float((g.to_5_hits <= budget).mean()),
               "first_hit_mean_if_success": float(g.first_hit[g.first_hit <= budget].mean()) if (g.first_hit <= budget).any() else np.nan,
               "to_5_hits_mean_if_success": float(g.to_5_hits[g.to_5_hits <= budget].mean()) if (g.to_5_hits <= budget).any() else np.nan}
        for col in METRICS:
            x = g[col].to_numpy(dtype=float)
            lo, hi = cluster_ci(g, col, rng) if split.startswith("cv5") else campaign_ci(x, rng)
            rec[f"{col}_mean"], rec[f"{col}_lo"], rec[f"{col}_hi"] = float(x.mean()), lo, hi
        rows.append(rec)
    out = pd.DataFrame(rows)
    # Share of the random-to-best gap in to_5_hits that each method closes, per split x threshold.
    for (split, thr), g in out.groupby(["split", "threshold"]):
        r = g.loc[g.method == "random", "to_5_hits_mean"].iloc[0]
        best = g.to_5_hits_mean.min()
        for i in g.index:
            out.loc[i, "gap_closed_vs_random"] = (r - out.loc[i, "to_5_hits_mean"]) / (r - best) if r > best else np.nan
    out.to_csv(run / "summary_v2.csv", index=False)
    print(run / "summary_v2.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
