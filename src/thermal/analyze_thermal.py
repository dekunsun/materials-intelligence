"""Follow-up analysis of a thermal re-score run (no re-scoring).

Everything here except the tier definitions was designed after the first look at
the results, so every output carries status "post-hoc".

1. Tier errors: per model, mean SRE on the 17 high-kappa materials minus mean SRE
   on the other 86, 95% bootstrap over materials (resampled within tier), with a
   Benjamini-Hochberg correction across the 62 models. SRD on the high tier is
   reported on valid predictions only, next to the count of failed predictions
   (a failed prediction scores SRD -2 and would otherwise look like under-prediction).
2. Saturation: does the screening decision still separate the better half of the
   leaderboard (SRME below the median)? Point estimates for rank agreement between
   SRME and recall@10 / high-tier SRE / Spearman log kappa. Intervals only for the
   two continuous metrics: recall@k is not bootstrapped, because a resample with
   repeated materials changes what "top 10" means.
   Also records how well separated the DFT top 10 is from rank 11.
3. Per-material values on the high tier for the five best models by SRME.
4. No-ML rule baselines from Slack's guidance (light atoms, simple tetrahedral
   bonding): (a) lightest mean atomic mass first; (b) tetrahedral structures
   (zinc-blende 216, wurtzite 186) first, then lightest.

Usage:
    .venv/bin/python src/thermal/analyze_thermal.py results/<thermal_run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from thermal.provenance import write as write_provenance  # noqa: E402

SEED, B = 7, 2000


def bh(p: np.ndarray, q: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg: boolean mask of discoveries at FDR q."""
    n = len(p); order = np.argsort(p); ranked = p[order]
    ok = ranked <= q * (np.arange(1, n + 1) / n)
    k = np.max(np.nonzero(ok)[0]) + 1 if ok.any() else 0
    mask = np.zeros(n, bool); mask[order[:k]] = True
    return mask


def boot_mean_ci(x: np.ndarray, rng, n=B):
    if len(x) < 2:
        return np.nan, np.nan
    m = rng.choice(x, (n, len(x))).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main() -> int:
    run = Path(sys.argv[1])
    pm = pd.read_csv(run / "per_material.csv")
    mm = pd.read_csv(run / "model_metrics.csv").sort_values("srme")
    rng = np.random.default_rng(SEED)
    mats = pm.drop_duplicates("material_id").set_index("material_id")
    hi = mats.index[mats.tier == "high"].to_numpy(); rest = mats.index[mats.tier != "high"].to_numpy()
    piv = {c: pm.pivot(index="material_id", columns="model", values=c) for c in ["sre", "srd", "srme", "k_pred"]}
    sre, srd, srme, kp = piv["sre"], piv["srd"], piv["srme"], piv["k_pred"]
    kd = mats.k_dft

    # 1. tier errors
    pos = {mid: i for i, mid in enumerate(sre.index)}
    hi_i = np.vectorize(pos.get)(rng.choice(hi, (B, len(hi))))
    re_i = np.vectorize(pos.get)(rng.choice(rest, (B, len(rest))))
    hi_pos = [pos[x] for x in hi]; re_pos = [pos[x] for x in rest]
    rows = []
    for m in mm.model:
        d = sre[m].to_numpy()
        diff_b = d[hi_i].mean(1) - d[re_i].mean(1)
        valid_hi = kp.loc[hi, m].notna().to_numpy()
        srd_valid = srd.loc[hi[valid_hi], m].to_numpy()
        lo, up = boot_mean_ci(srd_valid, rng)
        rows.append({"model": m, "srme": mm.set_index("model").srme[m],
                     "sre_high": d[hi_pos].mean(), "sre_rest": d[re_pos].mean(), "diff": d[hi_pos].mean() - d[re_pos].mean(),
                     "diff_lo": np.percentile(diff_b, 2.5), "diff_hi": np.percentile(diff_b, 97.5),
                     "p_boot": min(1.0, 2 * min((diff_b <= 0).mean(), (diff_b >= 0).mean())),
                     "n_failed_high": int((~valid_hi).sum()),
                     "srd_high_valid": float(srd_valid.mean()) if len(srd_valid) else np.nan,
                     "srd_high_valid_lo": lo, "srd_high_valid_hi": up})
    tier = pd.DataFrame(rows)
    tier["bh_significant"] = bh(tier.p_boot.to_numpy())
    tier["status"] = "post-hoc"
    tier.to_csv(run / "tier_errors.csv", index=False)
    tier_summary = {
        "status": "post-hoc", "n_models": len(tier),
        "high_worse_uncorrected": int((tier.diff_lo > 0).sum()), "high_better_uncorrected": int((tier.diff_hi < 0).sum()),
        "high_worse_bh": int(((tier["diff"] > 0) & tier.bh_significant).sum()),
        "high_better_bh": int(((tier["diff"] < 0) & tier.bh_significant).sum()),
        "expected_false_positives_per_side_uncorrected": round(len(tier) * 0.025, 1),
        "srd_valid_interval_below_0": int((tier.srd_high_valid_hi < 0).sum()),
        "srd_valid_interval_above_0": int((tier.srd_high_valid_lo > 0).sum()),
        "models_with_failed_high_predictions": int((tier.n_failed_high > 0).sum())}

    # 2. saturation
    kd_sorted = kd.sort_values(ascending=False)
    top10 = set(kd_sorted.index[:10])
    separation = {"rank10": [mats.name[kd_sorted.index[9]], int(mats.spg[kd_sorted.index[9]]), float(kd_sorted.iloc[9])],
                  "rank11": [mats.name[kd_sorted.index[10]], int(mats.spg[kd_sorted.index[10]]), float(kd_sorted.iloc[10])],
                  "relative_gap": float(kd_sorted.iloc[9] / kd_sorted.iloc[10] - 1),
                  "distinct_compounds_in_top10": int(mats.loc[list(top10), "name"].nunique())}

    def metrics(models, pick):
        k = np.log10(kd.loc[pick].to_numpy())
        hp = pick[np.isin(pick, hi)]
        out = {}
        for m in models:
            p = np.log10(kp.loc[pick, m].fillna(1e-3).clip(lower=1e-3).to_numpy())
            out[m] = (srme.loc[pick, m].mean(), sre.loc[hp, m].mean(), spearmanr(p, k).statistic)
        return pd.DataFrame(out, index=["srme", "sre_high", "spearman_log"]).T

    half = mm.model[mm.srme < mm.srme.median()].tolist()
    agree = {"srme_median_split": float(mm.srme.median()), "top10_separation": separation, "status": "post-hoc",
             "note": "recall@10 agreement is a point estimate only; resampling materials with replacement changes the top-10 set"}
    for name, models in [("all_models", mm.model.tolist()), ("better_half", half)]:
        r10 = mm.set_index("model").loc[models, "recall@10"]
        base = metrics(models, mats.index.to_numpy())
        pts = {"sre_high": float(spearmanr(base.srme, base.sre_high).statistic),
               "spearman_log": float(spearmanr(base.srme, -base.spearman_log).statistic),
               "recall10": float(spearmanr(base.srme, -r10.loc[base.index]).statistic)}
        bs = {"sre_high": [], "spearman_log": []}; dropped = 0
        for _ in range(B):
            pick = np.concatenate([rng.choice(hi, len(hi)), rng.choice(rest, len(rest))])
            t = metrics(models, pick)
            a = spearmanr(t.srme, t.sre_high).statistic; b = spearmanr(t.srme, -t.spearman_log).statistic
            if not (np.isfinite(a) and np.isfinite(b)):
                dropped += 1; continue
            bs["sre_high"].append(a); bs["spearman_log"].append(b)
        agree[name] = {"n_models": len(models), "point": pts,
                       "bootstrap_95": {c: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for c, v in bs.items()},
                       "bootstrap_resamples": B, "bootstrap_dropped_nonfinite": dropped,
                       "n_recall10_eq_1": int((r10 == 1).sum()), "recall10_range": [float(r10.min()), float(r10.max())]}
    (run / "saturation.json").write_text(json.dumps(agree, indent=2))

    # 3. high tier, five best
    best = mm.model[:5].tolist()
    t3 = mats.loc[hi, ["name", "spg", "k_dft"]].copy()
    for m in best:
        t3[m] = kp.loc[hi, m].round(0)
    t3.sort_values("k_dft", ascending=False).to_csv(run / "high_tier_best5.csv")

    # 4. rule baselines
    from pymatgen.core import Composition
    mass = mats.name.map(lambda f: Composition(f).weight / Composition(f).num_atoms)
    top5 = set(kd_sorted.index[:5])
    rules = {"lightest_first": mass, "tetrahedral_then_lightest": mass + 1000 * (~mats.spg.isin([216, 186]))}
    rb = {"status": "post-hoc"}
    for name, score in rules.items():
        order = list(score.sort_values(kind="stable").index)
        rb[name] = {"recall@5": len(set(order[:5]) & top5) / 5, "recall@10": len(set(order[:10]) & top10) / 10,
                    "spearman_log": float(spearmanr(-score, np.log10(kd)).statistic),
                    "rank_of_zb_BAs": order.index("mp-10044") + 1, "rank_of_wz_BAs": order.index("mp-984718") + 1,
                    "ranks_of_BP": [order.index("mp-1479") + 1, order.index("mp-1008559") + 1]}
    (run / "rule_baselines.json").write_text(json.dumps(rb, indent=2))

    (run / "tier_summary.json").write_text(json.dumps(tier_summary, indent=2))
    write_provenance(run, "analyze_thermal", inputs=[run / "per_material.csv", run / "model_metrics.csv"], seed=SEED,
                     status="post-hoc", note="tier differences, saturation, rule baselines")
    print(json.dumps(tier_summary, indent=1)); print(json.dumps(agree, indent=1)); print(json.dumps(rb, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
