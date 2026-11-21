"""Stability screening (D2A): re-score Matbench Discovery and test it against a validation-budget decision.

Re-scoring level: metrics recomputed from each model's published formation-energy
predictions (level 1, "re-score"). No structure relaxation is re-run.

Writes results/<run_id>/:
  config.json             design. The "pre_registered" block is unchanged from the first run
                          (csp_screening_20261121T190651Z, written before any prediction was scored);
                          "post_hoc_additions" lists what was added after an independent review.
  env.json                provenance: package versions, SHA-256 of every input file and every src/**/*.py
  leaderboard_check.csv   our metrics vs the published values, per model and subset
  model_metrics.csv       per model: F1, precision at each budget, wasted share of a 1% budget
  rank_agreement.json     Spearman between model rankings by F1 and by precision@1%, cluster bootstrap
  topk_curves.csv         precision@K per budget for display models, cluster bootstrap intervals
  boundaries.csv          per display model x bin: n, prevalence, precision, recall, F1
  predicted_bands.csv     per display model x band of PREDICTED hull distance: n, share truly stable,
                          and how many of the model's 1%-budget picks fall in each band
  misses.csv              per display model: false positives in the 1% budget and their true hull distances
  novelty_reference.json  bin sizes for every novelty definition, relabelling during relaxation

Usage:
    .venv/bin/python src/csp/run_screening.py
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.discovery_metrics import (EACH_TRUE, UNIQ, leaderboard_metrics, precision_at_k,  # noqa: E402
                                   pred_hull, prepare, prototype_type)
from csp.fetch_discovery import OUT as RAW  # noqa: E402
from thermal.fetch_kappa import REPO_COMMIT  # noqa: E402
from thermal.provenance import record  # noqa: E402

PRE_REGISTERED = {
    "question": "AI produces many candidate crystal structures. With a fixed budget of validation calculations, which structures are worth validating, and does the leaderboard metric pick the model that fills that budget with the most truly stable structures?",
    "data": f"Matbench Discovery @ {REPO_COMMIT}: WBM summary (256,963 structures; 215,488 unique prototypes), every model with a discovery prediction file",
    "reproduction_level": "re-score from published formation-energy predictions; no relaxation re-run",
    "truth": "DFT (MP2020-corrected) energy above the MP convex hull; a computational reference, not experiment",
    "leaderboard_match_tolerance": {"rates_and_errors": 6e-4, "counts": 0},
    "decision_setting": "unique-prototype test set as the candidate pool; a validation budget of K structures chosen by lowest predicted hull distance",
    "k_fractions": [0.001, 0.003, 0.01, 0.03, 0.1],
    "primary_k_fraction": 0.01,
    "hypotheses_stated_before_running": {
        "H1": "Among models, the ranking by F1 differs from the ranking by precision@1% (Spearman < 0.9).",
        "H2": "For each model, precision@K as K shrinks from 10% to 0.1% either keeps rising, plateaus or falls. 'Falls' (Goodhart-like) is defined as precision@0.1% below precision@1% with the bootstrap interval of the difference below 0. No direction is assumed.",
        "H3": "Precision and recall are lower for candidates whose structure type (prototype label without elements) is rare or absent in the 2023 Materials Project snapshot.",
    },
    "boundaries": {
        "lithium": "composition contains Li vs not",
        "structure_type_novelty": "count of the bare prototype label (protostructure_spglib before ':') among Materials Project entries in the 2023-02-07 snapshot used by the benchmark: 0, 1-9, >=10",
        "near_hull": "|DFT hull distance| <= 0.05 eV/atom vs further away",
    },
    "display_models": "the 10 best by unique-prototype F1, plus older baselines present in the data (Voronoi RF, CGCNN, MEGNet, BOWSR, CHGNet, M3GNet, MACE-MP-0)",
    "bootstrap": "structures resampled with replacement, 500 resamples, K taken as a fraction of the resample; seed 2026",
    "limits": ["WBM candidates come from element substitution on known MP structures, so most are near known prototypes",
               "truth is DFT, not synthesis or measurement",
               "precision@K treats every validation as equal cost"],
}
POST_HOC = [
    "Structure-type novelty also computed with an element-order-invariant label (the bare label renames the same type when substitution changes the alphabetical order of elements), and from the INITIAL (pre-relaxation) structure, which is known at screening time. The pre-registered bare relaxed-label version is kept.",
    "The pre-registered near-hull bin uses the TRUE DFT hull distance, which is unknown before validation. Added: bands of PREDICTED hull distance per model, where the 1%-budget picks fall, and the true hull distance of each false positive.",
    "Bootstrap changed to a cluster bootstrap by chemical system (WBM structures come in correlated substitution families); intervals are conditional on this set of models.",
    "Wasted share of a 1% budget (1 - precision) reported per model.",
    "Better-half Spearman (models with F1 at or above the median) is exploratory, not a pre-registered hypothesis.",
    "Base rates reported with both the rounded reference (leaderboard classification convention) and unrounded hull distances.",
]
BASELINES = ["Voronoi RF", "CGCNN", "MEGNet", "BOWSR", "CHGNet", "M3GNet", "MACE-MP-0"]
SEED, NBOOT = 2026, 500
BANDS = [(-np.inf, -0.05, "pred <= -0.05"), (-0.05, 0.0, "-0.05 < pred <= 0"), (0.0, 0.05, "0 < pred <= 0.05"), (0.05, np.inf, "pred > 0.05")]


def mp2023_ids() -> set[str]:
    """Material ids in the 2023-02-07 MP snapshot used by the benchmark (cached as a text file)."""
    cache = RAW / "mp2023_material_ids.txt"
    if not cache.exists():
        with gzip.open(RAW / "mp_computed_structure_entries_2023-02-07.json.gz", "rt") as f:
            col = json.load(f)["material_id"]
        cache.write_text("\n".join(sorted(col.values() if isinstance(col, dict) else col)))
    return set(cache.read_text().split())


def mp2023_prototype_counts(element_order_invariant: bool = False) -> tuple[pd.Series, int, int]:
    """Structure-type counts among MP entries present in the 2023-02-07 snapshot. Labels come from the
    2025 MP energies file restricted to those ids (the snapshot itself has structures, not labels)."""
    ids = mp2023_ids()
    mp = pd.read_csv(RAW / "mp_energies.csv.gz")
    mp = mp[mp.material_id.isin(ids)]
    types = mp.protostructure_spglib.dropna().map(lambda x: prototype_type(x, element_order_invariant))
    return types.value_counts(), len(ids), len(mp)


def chemsys(formula: str) -> str:
    return "-".join(sorted(set(re.findall(r"[A-Z][a-z]?", formula))))


def build_bins(wbm: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Boundary bins for every structure. Returns the bins and reference counts."""
    labels = ["new type (0 in MP)", "rare type (1-9)", "common type (>=10)"]
    out, ref = {}, {}
    for name, col, inv in [("novelty_relaxed_bare_label", "protostructure_spglib", False),
                           ("novelty_relaxed_invariant_label", "protostructure_spglib", True),
                           ("novelty_initial_invariant_label", "protostructure_spglib_initial_structure", True)]:
        counts, n_ids, n_mp = mp2023_prototype_counts(inv)
        nov = wbm[col].map(lambda x: prototype_type(x, inv)).map(counts).fillna(0)
        out[name] = pd.cut(nov, [-1, 0, 9, np.inf], labels=labels).astype(str)
        ref[name] = {"distinct_types_in_mp2023": int(len(counts))}
    ref["mp2023_ids"] = n_ids
    li = wbm.formula.str.contains(r"\bLi\d", regex=True) | wbm.formula.str.contains(r"\bLi\b", regex=True)
    out["lithium"] = pd.Series(np.where(li, "contains Li", "no Li"), index=wbm.index)
    out["near_hull_true_distance"] = pd.Series(np.where(wbm[EACH_TRUE].abs() <= 0.05, "|hull| <= 0.05", "|hull| > 0.05"), index=wbm.index)
    return pd.DataFrame(out, index=wbm.index), ref


def cluster_index(groups: np.ndarray) -> list[np.ndarray]:
    order = np.argsort(groups, kind="stable")
    _, starts = np.unique(groups[order], return_index=True)
    return np.split(order, starts[1:])


def cluster_resample(clusters: list[np.ndarray], rng) -> np.ndarray:
    pick = rng.integers(0, len(clusters), len(clusters))
    return np.concatenate([clusters[i] for i in pick])


def f1(et, col):
    a = et <= 0; m = (col <= 0) & ~np.isnan(col)
    tp = (a & m).sum(); fp = (~a & m).sum(); fn = (a & ~m).sum()
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("csp_screening_%Y%m%dT%H%M%SZ")
    out = ROOT / "results" / run_id
    out.mkdir(parents=True)
    (out / "config.json").write_text(json.dumps({"pre_registered": PRE_REGISTERED, "post_hoc_additions": POST_HOC,
        "first_run": "csp_screening_20261121T190651Z"}, indent=2))
    manifest = json.loads((RAW / "MANIFEST.json").read_text())
    ids = mp2023_ids()   # make sure the cache exists before hashing inputs
    model_files = [RAW / m["file"] for m in manifest["models"] if "file" in m]
    inputs = [RAW / "MANIFEST.json", RAW / "wbm_summary.csv.gz", RAW / "mp_energies.csv.gz", RAW / "mp2023_material_ids.txt",
              RAW / "mp_computed_structure_entries_2023-02-07.json.gz", *model_files]
    (out / "env.json").write_text(json.dumps(record("run_screening", inputs=inputs, seed=SEED,
        note="pre-registered design plus post-hoc additions listed in config.json"), indent=2, default=str))

    wbm = pd.read_csv(RAW / manifest["wbm_summary"]["file"]).set_index("material_id")
    uniq = wbm[UNIQ].astype(bool).to_numpy()
    bins, novref = build_bins(wbm)

    preds, check = {}, []
    for m in manifest["models"]:
        if "error" in m:
            check.append({"model": m["model"], "status": "download failed"}); continue
        df = pd.read_csv(RAW / m["file"]).set_index("material_id")
        preds[m["model"]] = df["e_form_per_atom"]
        mine = leaderboard_metrics(wbm, df["e_form_per_atom"])
        for subset in ("full_test_set", "unique_prototypes"):
            pub = (m["published"] or {}).get(subset) or {}
            row, ok = {"model": m["model"], "subset": subset}, True
            for k, v in mine[subset].items():
                row[f"ours_{k}"] = v
                if k in pub and pub[k] is not None:
                    row[f"pub_{k}"] = pub[k]
                    tol = 0 if k in ("TP", "FP", "TN", "FN", "missing_preds") else PRE_REGISTERED["leaderboard_match_tolerance"]["rates_and_errors"]
                    ok &= abs(v - pub[k]) <= tol + 1e-12
            row["status"] = "match" if ok else "MISMATCH"
            check.append(row)
    chk = pd.DataFrame(check); chk.to_csv(out / "leaderboard_check.csv", index=False)
    print(chk.status.value_counts().to_dict(), flush=True)

    ref, _ = prepare(wbm, next(iter(preds.values())))
    models = list(preds)
    P = np.column_stack([pred_hull(*prepare(wbm, preds[m])).to_numpy() for m in models])
    pool = np.where(uniq)[0]
    et, Pp = ref[EACH_TRUE].to_numpy()[pool], P[pool]
    et_unrounded = wbm[EACH_TRUE].to_numpy()[pool]
    col_of = {m: j for j, m in enumerate(models)}
    fr = PRE_REGISTERED["k_fractions"]; pk = PRE_REGISTERED["primary_k_fraction"]

    mm = []
    for m in models:
        c = Pp[:, col_of[m]]
        r = {"model": m, "f1_uniq": f1(et, c), "missing_uniq": int(np.isnan(c).sum())}
        for f in fr:
            r[f"prec@{f:g}"] = precision_at_k(et, c, max(1, int(round(f * len(pool)))))
        r["wasted_share_1pct"] = 1 - r[f"prec@{pk:g}"]
        mm.append(r)
    mmdf = pd.DataFrame(mm).sort_values("f1_uniq", ascending=False)
    mmdf["f1_rank"] = np.arange(1, len(mmdf) + 1)
    mmdf["prevalence_rounded_ref"] = float((et <= 0).mean())
    mmdf["prevalence_unrounded_ref"] = float((et_unrounded <= 0).mean())
    mmdf.to_csv(out / "model_metrics.csv", index=False)
    display = mmdf.model[:10].tolist() + [b for b in BASELINES if b in models and b not in mmdf.model[:10].tolist()]

    # cluster bootstrap by chemical system
    systems = wbm.formula.iloc[pool].map(chemsys).to_numpy()
    clusters = cluster_index(systems)
    rng = np.random.default_rng(SEED)
    half = (mmdf.f1_uniq >= mmdf.f1_uniq.median()).to_numpy()
    order = mmdf.model.tolist()
    base = {"all": spearmanr(mmdf.f1_uniq, mmdf[f"prec@{pk:g}"]).statistic,
            "better_half_exploratory": spearmanr(mmdf.f1_uniq[half], mmdf[f"prec@{pk:g}"][half]).statistic}
    boot = {k: [] for k in base}
    curves = {m: {f: [] for f in fr} for m in display}
    for b in range(NBOOT):
        idx = cluster_resample(clusters, rng)
        e_b, P_b = et[idx], Pp[idx]
        kk = {f: max(1, int(round(f * len(idx)))) for f in fr}
        f1s = np.array([f1(e_b, P_b[:, col_of[m]]) for m in order])
        pks = np.array([precision_at_k(e_b, P_b[:, col_of[m]], kk[pk]) for m in order])
        boot["all"].append(spearmanr(f1s, pks).statistic)
        boot["better_half_exploratory"].append(spearmanr(f1s[half], pks[half]).statistic)
        for m in display:
            for f in fr:
                curves[m][f].append(pks[order.index(m)] if f == pk else precision_at_k(e_b, P_b[:, col_of[m]], kk[f]))
        if b % 50 == 0:
            print(f"bootstrap {b}/{NBOOT}", flush=True)
    ra = {k: {"point": float(base[k]), "ci95": [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]} for k, v in boot.items()}
    ra.update({"n_models": len(mmdf), "n_better_half": int(half.sum()), "primary_k_fraction": pk, "n_clusters_chemsys": len(clusters),
               "note": "cluster bootstrap over chemical systems; intervals are conditional on this set of 73 models (several are near-duplicate variants)"})
    (out / "rank_agreement.json").write_text(json.dumps(ra, indent=2))

    rows = []
    for m in display:
        point = mmdf.set_index("model").loc[m]
        for f in fr:
            v = np.array(curves[m][f])
            rows.append({"model": m, "k_fraction": f, "k": int(round(f * len(pool))), "precision": point[f"prec@{f:g}"],
                         "lo": np.percentile(v, 2.5), "hi": np.percentile(v, 97.5)})
        d = np.array(curves[m][0.001]) - np.array(curves[m][0.01])
        rows.append({"model": m, "k_fraction": "diff_0.1%_minus_1%", "precision": point["prec@0.001"] - point["prec@0.01"],
                     "lo": np.percentile(d, 2.5), "hi": np.percentile(d, 97.5)})
    pd.DataFrame(rows).to_csv(out / "topk_curves.csv", index=False)

    # boundaries (point values; intervals in analyze_boundaries.py)
    bpool = bins.iloc[pool]
    brow = []
    for dim in bins.columns:
        for lvl in sorted(bpool[dim].unique()):
            sel = (bpool[dim] == lvl).to_numpy()
            for m in display:
                c = Pp[sel, col_of[m]]; a = et[sel] <= 0; mp_ = (c <= 0) & ~np.isnan(c)
                tp, fp, fn = int((a & mp_).sum()), int((~a & mp_).sum()), int((a & ~mp_).sum())
                brow.append({"dimension": dim, "bin": lvl, "n": int(sel.sum()), "prevalence": float(a.mean()), "model": m,
                             "precision": tp / (tp + fp) if tp + fp else np.nan, "recall": tp / (tp + fn) if tp + fn else np.nan,
                             "f1": 2 * tp / (2 * tp + fp + fn) if tp else 0.0})
    pd.DataFrame(brow).to_csv(out / "boundaries.csv", index=False)

    # predicted-distance bands and misses of the 1% budget (actionable at screening time)
    k1 = max(1, int(round(pk * len(pool))))
    prow, mrow = [], []
    for m in display:
        c = Pp[:, col_of[m]]
        score = np.where(np.isnan(c), np.inf, c)
        cut = np.partition(score, k1 - 1)[k1 - 1]
        picked = score < cut
        tied = np.where(score == cut)[0]
        picked[tied[: k1 - picked.sum()]] = True   # deterministic fill of the tied group, for counting only
        for lo, hi, name in BANDS:
            band = (c > lo) & (c <= hi)
            prow.append({"model": m, "band": name, "n": int(band.sum()), "share_truly_stable": float((et[band] <= 0).mean()) if band.any() else np.nan,
                         "picks_in_band_1pct": int((band & picked).sum()), "share_of_picks": float((band & picked).sum() / k1),
                         "share_truly_stable_among_picks": float((et[band & picked] <= 0).mean()) if (band & picked).any() else np.nan})
        fp = picked & (et > 0)
        d = et_unrounded[fp]
        mrow.append({"model": m, "k": k1, "false_positives": int(fp.sum()), "median_true_hull_fp": float(np.median(d)) if len(d) else np.nan,
                     "share_fp_le_0.025": float((d <= 0.025).mean()) if len(d) else np.nan,
                     "share_fp_le_0.05": float((d <= 0.05).mean()) if len(d) else np.nan, "max_true_hull_fp": float(d.max()) if len(d) else np.nan})
    pd.DataFrame(prow).to_csv(out / "predicted_bands.csv", index=False)
    pd.DataFrame(mrow).to_csv(out / "misses.csv", index=False)

    rel = wbm.protostructure_spglib.iloc[pool].map(lambda x: prototype_type(x, True))
    ini = wbm.protostructure_spglib_initial_structure.iloc[pool].map(lambda x: prototype_type(x, True))
    new_rel = (bpool.novelty_relaxed_invariant_label == "new type (0 in MP)").to_numpy()
    novref.update({k: bpool[k].value_counts().to_dict() for k in bins.columns},
                  relabelled_during_relaxation_all=int((rel != ini).sum()),
                  relabelled_during_relaxation_among_new_relaxed_type=int((rel != ini)[new_rel].sum()),
                  new_relaxed_type_with_initial_type_in_mp=int((bpool.novelty_initial_invariant_label != "new type (0 in MP)").to_numpy()[new_rel].sum()),
                  n_new_relaxed_type=int(new_rel.sum()))
    (out / "novelty_reference.json").write_text(json.dumps(novref, indent=2))
    print(json.dumps(ra, indent=1)); print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
