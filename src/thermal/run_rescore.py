"""Thermal module: re-score kappa-103 and test it against a screening decision.

Re-scoring level: we recompute metrics from each model's published predictions
(level 1, "re-score"). We do not re-run any phonon calculation.

Writes results/<run_id>/:
  config.json             design, written before any prediction file is scored
  env.json                package versions, input hashes (from MANIFEST.json)
  per_material.csv        one row per model x material: k_dft, k_pred, SRD, SRE, SRME, censored
  leaderboard_check.csv   our SRME/SRE/SRD/failure rate vs the published values
  model_metrics.csv       per model: overall metrics, per-tier errors, screening metrics
  rank_agreement.json     how far the SRME ranking of models agrees with screening rankings,
                          with bootstrap intervals over materials

Usage:
    .venv/bin/python src/thermal/run_rescore.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from thermal.fetch_kappa import OUT as RAW, REPO_COMMIT  # noqa: E402
from thermal.kappa_metrics import score_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

DESIGN = {
    "question": "Does the leaderboard metric for lattice thermal conductivity (kappa_SRME) pick the models that would best find high-kappa materials for heat spreading?",
    "data": f"Matbench Discovery @ {REPO_COMMIT}: phononDB PBE (no NAC) reference, 103 binaries, 300 K; every model with a kappa-103 prediction file",
    "reproduction_level": "re-score from published predictions; no phonon calculation re-run",
    "leaderboard_match_tolerance": 5e-4,
    "tiers_W_per_mK": {"high": ">= 100 (17 materials)", "mid": "10 to 100", "low": "< 10",
                       "beyond_copper": ">= 400 (5 materials: BAs x2, BN x2, zinc-blende BP)"},
    "tier_note": "Tiers were fixed after looking at the DFT reference values but before scoring any prediction file. 100 W/mK is a round number near the conductivity of common packaging ceramics; 400 W/mK is roughly copper.",
    "screening_metrics": ["recall@5 and recall@10: share of the DFT top-k materials (by kappa) that the model also ranks in its top k",
                          "spearman_log: Spearman correlation of log kappa over all 103",
                          "sre_high: mean SRE over the 17 high-tier materials",
                          "srd_high: mean SRD over the high tier (sign = systematic over/under-prediction)"],
    "rank_agreement": "Spearman correlation between the model ranking by kappa_SRME and the ranking by each screening metric; 95% percentile bootstrap over materials (2000 resamples, materials resampled within tier so each resample keeps 17 high-tier materials)",
    "censoring": "As on the leaderboard: SRME = 2 for imaginary modes, broken symmetry or missing values. SRE/SRD are not censored for imaginary modes (leaderboard behaviour), only for missing kappa (SRD = -2). Missing k_pred ranks last in screening.",
    "limits": ["DFT (PBE, three-phonon, no NAC) is the reference, not experiment",
               "103 simple binaries; diamond and Si are absent; some entries are polymorphs that are not the commercial phase",
               "intrinsic lattice kappa only; device heat flow depends on interfaces, thickness, defects and temperature"],
}


def boot_rank_agreement(pm: pd.DataFrame, models: list[str], tiers: pd.Series, rng, n=2000) -> dict:
    """Resample materials within tier; recompute per-model SRME mean and high-tier SRE, Spearman log."""
    mats = tiers.index.to_numpy()
    by_tier = {t: mats[tiers.to_numpy() == t] for t in tiers.unique()}
    srme = pm.pivot(index="material_id", columns="model", values="srme")[models]
    sre = pm.pivot(index="material_id", columns="model", values="sre")[models]
    lk_pred = np.log10(pm.pivot(index="material_id", columns="model", values="k_pred")[models].clip(lower=1e-3).fillna(1e-3))
    lk_true = np.log10(pm.drop_duplicates("material_id").set_index("material_id").k_dft)
    res = {"srme_vs_sre_high": [], "srme_vs_spearman_log": []}
    for _ in range(n):
        pick = np.concatenate([rng.choice(v, size=len(v), replace=True) for v in by_tier.values()])
        hi = pick[np.isin(pick, by_tier["high"])]
        a = srme.loc[pick].mean()
        b = sre.loc[hi].mean()
        c = lk_pred.loc[pick].apply(lambda col: spearmanr(col.to_numpy(), lk_true.loc[pick].to_numpy()).statistic)
        res["srme_vs_sre_high"].append(spearmanr(a, b).statistic)
        res["srme_vs_spearman_log"].append(spearmanr(a, -c).statistic)
    return {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in res.items()}


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("thermal_%Y%m%dT%H%M%SZ")
    out = ROOT / "results" / run_id
    out.mkdir(parents=True)
    (out / "config.json").write_text(json.dumps(DESIGN, indent=2, ensure_ascii=False))
    manifest = json.loads((RAW / "MANIFEST.json").read_text())
    from thermal.provenance import record
    (out / "env.json").write_text(json.dumps({**record("run_rescore", inputs=[RAW / "MANIFEST.json"], seed=2026),
                                              "manifest": manifest}, indent=2, ensure_ascii=False))

    ref = pd.read_json(RAW / manifest["reference"]["file"]).set_index("material_id")
    k = ref.kappa_tot_avg.map(lambda v: float(np.ravel(v)[0]))
    tiers = pd.Series(np.where(k >= 100, "high", np.where(k >= 10, "mid", "low")), index=ref.index)
    top = {kk: set(k.sort_values(ascending=False).index[:kk]) for kk in (5, 10)}

    rows, mm, check = [], [], []
    for m in manifest["models"]:
        if "error" in m:
            check.append({"model": m["model"], "status": "download failed: " + m["error"]}); continue
        pred = pd.read_json(RAW / m["file"]).set_index("material_id")
        s = score_model(pred, ref)
        s["model"] = m["model"]; rows.append(s.reset_index())
        pub = m["published"]
        ours = {"κ_SRME": s.srme.mean(), "κ_SRE": s.sre.mean(), "κ_SRD": s.srd.mean(), "κ_failure_rate": s.censored.mean()}
        diffs = {f"diff_{kk}": (ours[kk] - pub[kk]) if pub.get(kk) is not None else np.nan for kk in ours}
        check.append({"model": m["model"], **{f"ours_{kk}": v for kk, v in ours.items()},
                      **{f"pub_{kk}": pub.get(kk) for kk in ours}, **diffs,
                      "status": "match" if all(abs(v) <= DESIGN["leaderboard_match_tolerance"] for v in diffs.values() if not np.isnan(v)) else "MISMATCH"})
        rank = s.k_pred.fillna(-1).sort_values(ascending=False).index
        lk = np.log10(s.k_pred.clip(lower=1e-3).fillna(1e-3))
        rec = {"model": m["model"], "training_set": str(m.get("training_set")), "srme": s.srme.mean(),
               "sre": s.sre.mean(), "srd": s.srd.mean(), "failure_rate": s.censored.mean(),
               "recall@5": len(set(rank[:5]) & top[5]) / 5, "recall@10": len(set(rank[:10]) & top[10]) / 10,
               "spearman_log": spearmanr(lk, np.log10(s.k_dft)).statistic,
               "n_pred_ge_400": int((s.k_pred >= 400).sum()),
               "precision_ge_400": float(((s.k_pred >= 400) & (s.k_dft >= 400)).sum() / max((s.k_pred >= 400).sum(), 1))}
        for t in ["high", "mid", "low"]:
            g = s[tiers == t]
            rec[f"sre_{t}"], rec[f"srd_{t}"], rec[f"srme_{t}"], rec[f"censored_{t}"] = g.sre.mean(), g.srd.mean(), g.srme.mean(), g.censored.mean()
        mm.append(rec)
        print(f"{m['model']:28s} SRME ours {ours['κ_SRME']:.4f} pub {pub['κ_SRME']}", flush=True)

    pm = pd.concat(rows); pm["tier"] = pm.material_id.map(tiers)
    pm.to_csv(out / "per_material.csv", index=False)
    pd.DataFrame(check).to_csv(out / "leaderboard_check.csv", index=False)
    mdf = pd.DataFrame(mm).sort_values("srme"); mdf.to_csv(out / "model_metrics.csv", index=False)

    ag = {f"srme_vs_{c}": float(spearmanr(mdf.srme, mdf[c] if c.startswith(("sre", "srme")) else -mdf[c]).statistic)
          for c in ["sre_high", "srme_high", "spearman_log", "recall@5", "recall@10"]}
    ci = boot_rank_agreement(pm, mdf.model.tolist(), tiers, np.random.default_rng(2026))
    (out / "rank_agreement.json").write_text(json.dumps({"point": ag, "bootstrap_95": ci,
        "note": "positive = models that rank better on SRME also rank better on the other metric"}, indent=2))
    print(json.dumps(ag, indent=1)); print(ci); print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
