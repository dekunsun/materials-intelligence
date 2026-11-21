"""Battery module: how many experiments does each selection policy need?

Writes everything to results/<run_id>/:
  config.json        the pre-registered design, written BEFORE any campaign runs
  env.json           package versions and input-file hashes
  sequences.jsonl    every campaign: split, fold, threshold, method, seed, queried keys
  scores.csv         per-campaign metrics
  summary.csv        mean and 95% bootstrap CI per split x threshold x method
  rl_curves.json     REINFORCE training curves (hits per training episode)

Usage:
    .venv/bin/python src/battery/run_experiment.py            # full run
    .venv/bin/python src/battery/run_experiment.py --smoke    # tiny settings, to check the code
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from battery.campaign import (Context, ReinforcePolicy, run_bo_gp, run_bo_rf_prior,  # noqa: E402
                              run_family_rule, run_random, run_rl, run_screen_rf, score)
from battery.data import COMMIT, family_of, load_pool  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

DESIGN = {
    "question": "How many experiments does each selection policy need to find solid electrolytes above a conductivity threshold?",
    "data": f"OBELiX @ {COMMIT}, room-temperature total ionic conductivity, duplicates merged by median log10",
    "features": "composition only (38 features: Li fraction, element-property statistics, framework/anion element fractions)",
    "primary_threshold_S_per_cm": 1e-3,
    "sensitivity_thresholds_S_per_cm": [1e-4, 1e-2],
    "threshold_note": "1e-3 S/cm chosen before running as the primary gate; the buyer-side source for this number is still to be found (open item). 1e-4 is too easy here (42.5% of compositions pass).",
    "budget_experiments": 40,
    "metrics": ["first_hit (experiments until the first composition above threshold; budget+1 if none)",
                "to_5_hits (experiments until five compositions above threshold; budget+1 if not reached)",
                "hits@10", "hits@20", "hits@40"],
    "families": "oxide if O present; else sulfide if S or Se; else halide if Cl/Br/I/F; else other",
    "splits": {"official": "OBELiX train/test split; prior = train compositions, pool = test compositions",
               "cv5": "5 folds over unique compositions; prior = other 4 folds, pool = held-out fold",
               "family": "leave one chemistry family out (oxide, sulfide); prior = all other families, pool = that family. Tests whether prior data helps when the lab moves to a new chemistry."},
    "methods": ["random", "family_rule", "bo_gp", "screen_rf", "bo_rf_prior", "rl_reinforce"],
    "seeds_official": 30, "seeds_cv5_per_fold": 10, "seeds_family": 10,
    "rl": {"algorithm": "REINFORCE, linear softmax, Adam lr 0.02, gamma 0.97, running per-step baseline",
           "episodes": 1500, "training_pool_size": 110, "trained_on": "prior compositions only"},
    "ci": "95% percentile bootstrap over campaigns, 2000 resamples. Captures algorithm randomness and, for cv5, fold variation; it does not capture uncertainty about which materials the literature happened to report.",
    "limits": ["retrospective on materials already reported in papers, not new discovery",
               "published conductivities skew toward successes; negative results are under-represented",
               "composition features only; no structure",
               "DFT is not involved; values are experimental measurements as curated by OBELiX"],
}


def bootstrap_ci(x: np.ndarray, rng: np.random.Generator, n: int = 2000) -> tuple[float, float]:
    if len(x) < 2 or np.all(x == x[0]):
        return float(x.mean()), float(x.mean())
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    design = json.loads(json.dumps(DESIGN))
    if args.smoke:
        design.update(seeds_official=2, seeds_cv5_per_fold=1, seeds_family=1, sensitivity_thresholds_S_per_cm=[])
        design["rl"]["episodes"] = 30

    run_id = datetime.now(timezone.utc).strftime("battery_%Y%m%dT%H%M%SZ") + ("_smoke" if args.smoke else "")
    out = ROOT / "results" / run_id
    out.mkdir(parents=True)
    (out / "config.json").write_text(json.dumps(design, indent=2))   # pre-registration first

    pool, info = load_pool()
    import scipy, sklearn, pymatgen.core  # noqa: E401
    (out / "env.json").write_text(json.dumps({
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "scikit-learn": sklearn.__version__, "scipy": scipy.__version__,
        "pymatgen": getattr(pymatgen.core, "__version__", "unknown"),
        "data_info": info, "started_utc": datetime.now(timezone.utc).isoformat()}, indent=2))

    # Standardize with statistics of all compositions' features (no labels involved).
    mu, sd = pool.X.mean(0), pool.X.std(0); sd[sd == 0] = 1
    X = (pool.X - mu) / sd
    keys = np.array(pool.keys)
    fams = np.array([family_of(k) for k in pool.keys])

    # Fold assignment for cv5, fixed by seed 0.
    fold_of = np.random.default_rng(0).permutation(len(keys)) % 5
    splits = [("official", 0, pool.split == "train", pool.split == "test")]
    splits += [("cv5", f, fold_of != f, fold_of == f) for f in range(5)]
    splits += [(f"family_{fam}", 0, fams != fam, fams == fam) for fam in ["oxide", "sulfide"]]
    method_code = {m: i for i, m in enumerate(design["methods"])}   # fixed, unlike hash()
    split_code = {"official": 0, "cv5": 1, "family_oxide": 2, "family_sulfide": 3}

    thresholds = [design["primary_threshold_S_per_cm"]] + design["sensitivity_thresholds_S_per_cm"]
    budget = design["budget_experiments"]
    rows, curves = [], {}
    seq_f = (out / "sequences.jsonl").open("w")
    t0 = time.time()

    for thr in thresholds:
        lt = float(np.log10(thr))
        for name, fold, prior_m, pool_m in splits:
            if name == "cv5" and thr != design["primary_threshold_S_per_cm"] and thr != 1e-2:
                continue   # 1e-4 sensitivity on the official split only, to save time
            if name == "official" and thr == 1e-2:
                continue   # only one test composition clears 1e-2; cv5 pools all folds instead
            if name.startswith("family") and thr != design["primary_threshold_S_per_cm"]:
                continue
            ctx = Context(X=X[pool_m], y=pool.y[pool_m], threshold=lt, budget=budget,
                          X_prior=X[prior_m], y_prior=pool.y[prior_m], fam=fams[pool_m], fam_prior=fams[prior_m])
            n_seeds = {"official": design["seeds_official"], "cv5": design["seeds_cv5_per_fold"],
                       "family_oxide": design["seeds_family"],
                       "family_sulfide": design["seeds_family"]}[name]
            policy = ReinforcePolicy(X.shape[1], seed=1000 + fold)
            curve = policy.train(ctx.X_prior, ctx.y_prior, lt, budget, episodes=design["rl"]["episodes"],
                                 pool_size=design["rl"]["training_pool_size"])
            curves[f"{name}_f{fold}_thr{thr:g}"] = curve
            n_hits_pool = int((ctx.y >= lt).sum())
            for method in design["methods"]:
                for s in range(n_seeds):
                    rng = np.random.default_rng([split_code[name], fold, s, method_code[method], int(round(-lt * 10))])
                    if method == "random": seq = run_random(ctx, rng)
                    elif method == "family_rule": seq = run_family_rule(ctx, rng)
                    elif method == "bo_gp": seq = run_bo_gp(ctx, rng)
                    elif method == "screen_rf": seq = run_screen_rf(ctx, rng)
                    elif method == "bo_rf_prior": seq = run_bo_rf_prior(ctx, rng)
                    else: seq = run_rl(ctx, rng, policy)
                    sc = score(seq, ctx.y, lt, budget)
                    rows.append({"split": name, "fold": fold, "threshold": thr, "method": method, "seed": s,
                                 "pool_size": int(len(ctx.y)), "pool_hits": n_hits_pool, **sc})
                    seq_f.write(json.dumps({"split": name, "fold": fold, "threshold": thr, "method": method,
                                            "seed": s, "queried": keys[pool_m][seq].tolist()}) + "\n")
            print(f"[{time.time() - t0:7.1f}s] thr={thr:g} {name} fold {fold}: pool {len(ctx.y)}, hits {n_hits_pool}", flush=True)
    seq_f.close()

    df = pd.DataFrame(rows)
    df.to_csv(out / "scores.csv", index=False)
    (out / "rl_curves.json").write_text(json.dumps(curves))

    rng = np.random.default_rng(12345)
    summ = []
    for (split, thr, method), g in df.groupby(["split", "threshold", "method"]):
        rec = {"split": split, "threshold": thr, "method": method, "n_campaigns": len(g),
               "pool_size_mean": g.pool_size.mean(), "pool_hits_mean": g.pool_hits.mean()}
        for col in ["first_hit", "to_5_hits", "hits@10", "hits@20", "hits@40"]:
            lo, hi = bootstrap_ci(g[col].to_numpy(), rng)
            rec[f"{col}_mean"] = g[col].mean(); rec[f"{col}_lo"] = lo; rec[f"{col}_hi"] = hi
        # Expected first hit for random sampling without replacement: (N+1)/(K+1), averaged over pools.
        rec["random_first_hit_expected"] = float(((g.pool_size + 1) / (g.pool_hits + 1)).mean())
        summ.append(rec)
    pd.DataFrame(summ).to_csv(out / "summary.csv", index=False)
    print(f"done in {time.time() - t0:.0f}s -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
