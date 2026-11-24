"""Descriptive sensitivity checks for Stage 1 of the far-from-training stability test.

Pre-registered as descriptive only (modules/csp/FAR_FROM_TRAINING_TEST.md, Section 6): these numbers never change the
decision in decision.json. Written after the decision was computed. Uses the scoring functions of far_decide.py.

Variants, each giving the median r over the 10 decision models and d (lead model minus Wrenformer) per extrapolation cell:
  primary            the pre-registered setting (repeats decision.json point estimates)
  unique_pool        unique-prototype structures only
  relaxed_S2         cells defined by the framework of the RELAXED structure
  S1                 cells defined by the element-order-invariant prototype label (initial structure)
  chemsys_clusters   primary cells, but the bootstrap resamples chemical systems instead of frameworks (95% intervals)
  leave_one_out      structural cell with each framework that holds a stable structure left out in turn (min, max)
Also per-model ratios for CHGNet, MACE-MP-0 and Voronoi RF under the primary setting (from per_model_cells.csv).

Usage (repository root):  .venv/bin/python -I src/csp/far_sensitivity.py results/<run_id>
Writes <run>/sensitivity.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.discovery_metrics import EACH_TRUE, pred_hull, prepare  # noqa: E402
from csp.far_decide import (BASELINE, EXTRAP, N_BOOT, RAW, SEED, cell_nrp, clusters, decision_models,  # noqa: E402
                            ref_nrp)

CELLS = {(True, True): "interpolation", (True, False): "structural_extrapolation",
         (False, True): "chemical_extrapolation", (False, False): "double_extrapolation"}


def stats(E, I, true, preds, nel, top, lead):
    w = pd.Series(nel[E]).value_counts(normalize=True).to_dict()
    v = {m: (cell_nrp(true[E], preds[m][E]), ref_nrp(true[I], preds[m][I], nel[I], w)) for m in top + [BASELINE]}
    return float(np.median([v[m][0] / v[m][1] for m in top])), float(v[lead][0] - v[BASELINE][0])


def main(run: str) -> int:
    run = Path(run)
    split = pd.read_csv(run / "split.csv.gz").set_index("material_id")
    wbm = pd.read_csv(RAW / "wbm_summary.csv.gz").set_index("material_id").loc[split.index]
    files = {m["model"]: m["file"] for m in json.loads((RAW / "MANIFEST.json").read_text())["models"] if "file" in m}
    top, lead = decision_models()
    preds = {}
    for m in top + [BASELINE]:
        ref, p = prepare(wbm, pd.read_csv(RAW / files[m]).set_index("material_id")["e_form_per_atom"])
        preds[m] = pred_hull(ref, p).to_numpy()
    true = ref[EACH_TRUE].to_numpy()
    nel = split.n_elements.to_numpy()
    chem = split.chem_familiar.to_numpy()

    def cells(struct_known, mask=None):
        lab = np.array([CELLS[(c, s)] for c, s in zip(chem, struct_known)])
        if mask is not None:
            lab = np.where(mask, lab, "excluded")
        return lab

    variants = {"primary": cells(split.framework_known.to_numpy()),
                "unique_pool": cells(split.framework_known.to_numpy(), split.unique_prototype.to_numpy()),
                "relaxed_S2": cells(split.framework_relaxed_known.to_numpy()),
                "S1": cells(split.s1_known.to_numpy())}
    out = {"what": "Descriptive sensitivity checks, Stage 1 (src/csp/far_sensitivity.py); never change the decision",
           "variants": {}}
    for name, lab in variants.items():
        I = np.flatnonzero(lab == "interpolation")
        out["variants"][name] = {}
        for c in EXTRAP:
            E = np.flatnonzero(lab == c)
            r, d = stats(E, I, true, preds, nel, top, lead)
            out["variants"][name][c] = {"n": int(len(E)), "stable": int((true[E] <= 0).sum()), "median_r": r, "d": d}

    # chemical-system clusters instead of framework clusters, primary cells
    lab = variants["primary"]; I = np.flatnonzero(lab == "interpolation")
    sysarr = split.chemsys.to_numpy(); rng = np.random.default_rng(SEED)
    out["chemsys_clusters"] = {}
    ci = clusters(sysarr[I])
    for c in EXTRAP:
        E = np.flatnonzero(lab == c); ce = clusters(sysarr[E])
        bs = []
        for _ in range(N_BOOT):
            e = E[np.concatenate([ce[j] for j in rng.integers(0, len(ce), len(ce))])]
            i = I[np.concatenate([ci[j] for j in rng.integers(0, len(ci), len(ci))])]
            bs.append(stats(e, i, true, preds, nel, top, lead))
        bs = np.array(bs)
        out["chemsys_clusters"][c] = {"median_r_95": np.nanpercentile(bs[:, 0], [2.5, 97.5]).tolist(),
                                      "d_95": np.nanpercentile(bs[:, 1], [2.5, 97.5]).tolist()}

    # leave one framework out, structural cell
    E = np.flatnonzero(lab == "structural_extrapolation")
    fw = split.framework.fillna("none").to_numpy()
    with_stable = sorted(set(fw[E][true[E] <= 0]))
    loo = np.array([stats(E[fw[E] != f], I, true, preds, nel, top, lead) for f in with_stable])
    worst = with_stable[int(np.argmin(loo[:, 0]))]
    out["leave_one_framework_out_structural"] = {"frameworks": len(with_stable),
                                                  "median_r_min_max": [float(loo[:, 0].min()), float(loo[:, 0].max())],
                                                  "d_min_max": [float(loo[:, 1].min()), float(loo[:, 1].max())],
                                                  "framework_whose_removal_lowers_r_most": worst}
    pm = pd.read_csv(run / "per_model_cells.csv")
    out["other_models_r_primary"] = {m: {c: round(float(pm[(pm.model == m) & (pm.cell == c)].r.iloc[0]), 3) for c in EXTRAP}
                                     for m in ["CHGNet", "MACE-MP-0", "Voronoi RF", BASELINE]}
    (run / "sensitivity.json").write_text(json.dumps(out, indent=1))
    for name, v in out["variants"].items():
        print(name, {c: (x["n"], x["stable"], round(x["median_r"], 3), round(x["d"], 3)) for c, x in v.items()})
    print("chemsys clusters", out["chemsys_clusters"])
    print("LOFO", out["leave_one_framework_out_structural"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
