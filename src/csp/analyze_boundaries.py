"""Bootstrap intervals for the boundary comparisons of a screening run.

For each display model: difference between two bins in precision and recall at the
stability threshold (0 eV/atom), and precision of a 1% budget taken inside each bin.
Cluster bootstrap by chemical system, resampled within each bin (1,000 resamples for
differences, 500 for the within-bin budgets).

Bins come from run_screening.build_bins:
  * novelty_relaxed_bare_label      pre-registered (bare AFLOW-style label of the relaxed structure)
  * novelty_relaxed_invariant_label post-hoc correction: element-order-invariant label
  * novelty_initial_invariant_label post-hoc: label of the INITIAL structure, known at screening time
  * near_hull_true_distance         pre-registered, but defined by the true DFT answer (not actionable)
  * lithium                         pre-registered

Usage:
    .venv/bin/python src/csp/analyze_boundaries.py results/<csp_run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.discovery_metrics import EACH_TRUE, UNIQ, precision_at_k, pred_hull, prepare  # noqa: E402
from csp.fetch_discovery import OUT as RAW  # noqa: E402
from csp.run_screening import BASELINES, build_bins, chemsys, cluster_index, cluster_resample  # noqa: E402
from thermal.provenance import write as write_provenance  # noqa: E402

SEED, NB_DIFF, NB_TOPK = 11, 1000, 500
COMPARISONS = [("novelty_relaxed_bare_label", "new type (0 in MP)", "common type (>=10)", "pre-registered"),
               ("novelty_relaxed_invariant_label", "new type (0 in MP)", "common type (>=10)", "post-hoc"),
               ("novelty_initial_invariant_label", "new type (0 in MP)", "common type (>=10)", "post-hoc"),
               ("near_hull_true_distance", "|hull| <= 0.05", "|hull| > 0.05", "pre-registered; conditions on the answer")]


def pr(et, col):
    a = et <= 0; m = (col <= 0) & ~np.isnan(col)
    tp = (a & m).sum(); fp = (~a & m).sum(); fn = (a & ~m).sum()
    return (tp / (tp + fp) if tp + fp else np.nan), (tp / (tp + fn) if tp + fn else np.nan)


def main() -> int:
    run = Path(sys.argv[1])
    manifest = json.loads((RAW / "MANIFEST.json").read_text())
    wbm = pd.read_csv(RAW / manifest["wbm_summary"]["file"]).set_index("material_id")
    bins_all, _ = build_bins(wbm)
    keep = wbm[UNIQ].astype(bool).to_numpy()
    wbm, bins = wbm[keep], bins_all[keep]
    systems = wbm.formula.map(chemsys).to_numpy()
    mm = pd.read_csv(run / "model_metrics.csv")
    display = mm.model[:10].tolist() + [b for b in BASELINES if b in mm.model.tolist() and b not in mm.model[:10].tolist()]
    files = {m["model"]: m["file"] for m in manifest["models"] if "file" in m}
    rng = np.random.default_rng(SEED)
    rows, topk = [], []
    groups = {}
    for dim in bins.columns:
        for lvl in bins[dim].unique():
            ix = np.where(bins[dim].to_numpy() == lvl)[0]
            groups[(dim, lvl)] = (ix, [ix[c] for c in cluster_index(systems[ix])])
    for m in display:
        p = pd.read_csv(RAW / files[m]).set_index("material_id")["e_form_per_atom"]
        ref, pp = prepare(wbm, p)
        et, col = ref[EACH_TRUE].to_numpy(), pred_hull(ref, pp).to_numpy()
        for dim, a_lbl, b_lbl, status in COMPARISONS:
            (ia, ca), (ib, cb) = groups[(dim, a_lbl)], groups[(dim, b_lbl)]
            pa, ra = pr(et[ia], col[ia]); pb, rb = pr(et[ib], col[ib])
            dp, dr = [], []
            for _ in range(NB_DIFF):
                sa = cluster_resample(ca, rng); sb = cluster_resample(cb, rng)
                x, y = pr(et[sa], col[sa]); u, v = pr(et[sb], col[sb])
                dp.append(x - u); dr.append(y - v)
            rows.append({"model": m, "dimension": dim, "status": status, "a": a_lbl, "b": b_lbl, "n_a": len(ia), "n_b": len(ib),
                         "prevalence_a": float((et[ia] <= 0).mean()), "prevalence_b": float((et[ib] <= 0).mean()),
                         "precision_a": pa, "precision_b": pb, "d_precision": pa - pb,
                         "d_precision_lo": np.nanpercentile(dp, 2.5), "d_precision_hi": np.nanpercentile(dp, 97.5),
                         "recall_a": ra, "recall_b": rb, "d_recall": ra - rb,
                         "d_recall_lo": np.nanpercentile(dr, 2.5), "d_recall_hi": np.nanpercentile(dr, 97.5)})
        for (dim, lvl), (ix, cl) in groups.items():
            k = max(1, int(round(0.01 * len(ix))))
            boots = []
            for _ in range(NB_TOPK):
                s = cluster_resample(cl, rng)
                boots.append(precision_at_k(et[s], col[s], max(1, int(round(0.01 * len(s))))))
            topk.append({"model": m, "dimension": dim, "bin": lvl, "n": len(ix), "k_1pct": k,
                         "prevalence": float((et[ix] <= 0).mean()), "prec_at_1pct": precision_at_k(et[ix], col[ix], k),
                         "lo": np.percentile(boots, 2.5), "hi": np.percentile(boots, 97.5)})
        print(m, flush=True)
    pd.DataFrame(rows).to_csv(run / "boundary_intervals.csv", index=False)
    pd.DataFrame(topk).to_csv(run / "boundary_topk.csv", index=False)
    write_provenance(run, "analyze_boundaries", inputs=[run / "model_metrics.csv", RAW / "MANIFEST.json", RAW / "wbm_summary.csv.gz",
                                                         RAW / "mp_energies.csv.gz", RAW / "mp2023_material_ids.txt"],
                     seed=SEED, status="mixed: see 'status' column of boundary_intervals.csv",
                     note="cluster bootstrap by chemical system; 1,000 resamples for differences, 500 for within-bin budgets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
