"""Post-hoc check: how much of the cv5 gain is interpolation inside a doping series?

Added after a review of run battery_20261121T080824Z. That run's cv5 folds were
assigned at random over compositions, and about half of every held-out fold sits
within 0.3 (Euclidean distance in standardized feature space) of a composition
in the other folds, usually the same doping series. This script repeats the cv5
campaigns with *series-grouped* folds:

  1. Link any two compositions closer than LINK_DIST; connected components are
     "series". (Single linkage, so a chain of close neighbours forms one series.)
  2. Assign whole series to 5 folds, largest first, each to the currently
     smallest fold (deterministic).
  3. Run the same policies, seeds and budget as the main run.

RL is not re-run here (decision on 2026-11-21: RL work is paused).
This analysis was designed after seeing the main results, so it is labelled
post-hoc in config.json and in the report.

Usage:
    .venv/bin/python src/battery/run_grouped.py [link_dist]   # default 0.3
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from battery.campaign import Context, run_bo_gp, run_bo_rf_prior, run_family_rule, run_random, run_screen_rf, score  # noqa: E402
from battery.data import COMMIT, family_of, load_pool  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LINK_DIST = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3   # 1.0 run as a sensitivity
METHODS = ["random", "family_rule", "bo_gp", "screen_rf", "bo_rf_prior"]
RUNNERS = {"random": run_random, "family_rule": run_family_rule, "bo_gp": run_bo_gp,
           "screen_rf": run_screen_rf, "bo_rf_prior": run_bo_rf_prior}
DESIGN = {
    "status": "post-hoc (designed after seeing battery_20261121T080824Z)",
    "question": "Does the advantage of prior data survive when no doping-series neighbour of a candidate is in the prior?",
    "data": f"OBELiX @ {COMMIT}, same pool and features as the main run",
    "series_definition": f"connected components of compositions linked when standardized Euclidean distance < {LINK_DIST}",
    "folds": "5 folds of whole series, largest series first, each to the currently smallest fold",
    "threshold_S_per_cm": 1e-3, "budget_experiments": 40, "seeds_per_fold": 10, "methods": METHODS,
    "rl": "not re-run (paused)",
}


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime(f"battery_grouped{LINK_DIST:g}_%Y%m%dT%H%M%SZ")
    out = ROOT / "results" / run_id
    out.mkdir(parents=True)
    (out / "config.json").write_text(json.dumps(DESIGN, indent=2))

    pool, info = load_pool()
    mu, sd = pool.X.mean(0), pool.X.std(0); sd[sd == 0] = 1
    X = (pool.X - mu) / sd
    fams = np.array([family_of(k) for k in pool.keys])
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    n_series, series = connected_components(D < LINK_DIST, directed=False)
    sizes = np.bincount(series)
    fold_of_series, fold_size = {}, np.zeros(5, int)
    for s in np.argsort(-sizes, kind="stable"):
        f = int(np.argmin(fold_size)); fold_of_series[s] = f; fold_size[f] += sizes[s]
    fold = np.array([fold_of_series[s] for s in series])

    lt = float(np.log10(DESIGN["threshold_S_per_cm"])); B = DESIGN["budget_experiments"]
    rows, diag = [], []
    for f in range(5):
        pm, prm = fold == f, fold != f
        nn = D[np.ix_(pm, prm)].min(1)
        diag.append({"fold": f, "pool": int(pm.sum()), "hits": int((pool.y[pm] >= lt).sum()),
                     "min_dist_to_prior": float(nn.min()), "share_within_link_dist": float((nn < LINK_DIST).mean()),
                     "families": pd.Series(fams[pm]).value_counts().to_dict()})
        ctx = Context(X=X[pm], y=pool.y[pm], threshold=lt, budget=B, X_prior=X[prm], y_prior=pool.y[prm],
                      fam=fams[pm], fam_prior=fams[prm])
        for mi, m in enumerate(METHODS):
            for s in range(DESIGN["seeds_per_fold"]):
                rng = np.random.default_rng([9, f, s, mi, 30])
                rows.append({"split": "cv5_grouped", "fold": f, "threshold": DESIGN["threshold_S_per_cm"],
                             "method": m, "seed": s, **score(RUNNERS[m](ctx, rng), ctx.y, lt, B)})
        print(diag[-1], flush=True)
    (out / "env.json").write_text(json.dumps({"data_info": info, "n_series": int(n_series),
                                              "largest_series": int(sizes.max()), "folds": diag}, indent=2, default=int))
    pd.DataFrame(rows).to_csv(out / "scores.csv", index=False)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
