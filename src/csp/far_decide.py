"""Score the cells of the far-from-training stability test and apply the pre-registered rules
(modules/csp/FAR_FROM_TRAINING_TEST.md, Sections 3, 5 and 6).

Written and committed before any per-cell model metric was computed.

Per model and cell:
  R-precision  share of truly stable among the k structures predicted most stable, k = DFT-stable count in the cell
               (csp.discovery_metrics.precision_at_k: missing predictions rank last, ties counted in expectation)
  NRp          (R-precision - p) / (1 - p), p = the cell's stable share
  reference    the interpolation cell reweighted to the extrapolation cell's element-count mix: R-precision and p are
               computed per element-count stratum of the interpolation cell (k = stable count of that stratum) and
               averaged with the extrapolation cell's stratum weights; NRp_ref = (Rp_w - p_w) / (1 - p_w)
  r            NRp_cell / NRp_ref, per model; the statistic is the median of r over the 10 decision models
  d            NRp(lead model) - NRp(Wrenformer), same cell
Intervals: cluster bootstrap by framework key, frameworks resampled within each cell (the extrapolation cell and the
interpolation cell independently), 1,000 resamples, seed 11, percentile 95%.

Rules, checked in order, for each extrapolation cell (D10 uses structural_extrapolation only):
  1 too_small  fewer than 50 DFT-stable structures or fewer than 20 frameworks with a stable structure
  2 fails      upper(median r) < 0.5  or  upper(d) < 0.10
  3 holds      lower(median r) >= 0.8 and lower(d) > 0.10
  4 partial    otherwise

Usage (repository root):
    .venv/bin/python -I src/csp/far_decide.py results/<run_id>          # needs <run>/split.csv.gz from far_split.py
Writes <run>/decision.json and <run>/per_model_cells.csv.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.discovery_metrics import EACH_TRUE, precision_at_k, pred_hull, prepare  # noqa: E402
from csp.run_screening import RAW  # noqa: E402

MBD = ROOT / "data/raw/mbd_src/matbench-discovery"
METRICS = ROOT / "results/csp_screening_20261121T192919Z/model_metrics.csv"
N_DECISION, SEED, N_BOOT = 10, 11, 1000
BASELINE, OLD_MODELS, DESCRIPTIVE_BASELINE = "Wrenformer", ["CHGNet", "MACE-MP-0"], "Voronoi RF"
EXTRAP = ["structural_extrapolation", "chemical_extrapolation", "double_extrapolation"]
MIN_STABLE, MIN_FRAMEWORKS = 50, 20
R_FAIL, R_HOLD, D_MARGIN = 0.5, 0.8, 0.10


def compliant_models() -> dict[str, bool]:
    ds = yaml.safe_load(open(MBD / "matbench_discovery/datasets.yml"))
    ok = {k: bool(v.get("compliant")) for k, v in ds.items()}
    out = {}
    for f in sorted((MBD / "models").glob("*/*.yml")):
        y = yaml.safe_load(open(f))
        tr = y.get("training_sets") or []
        out[y["model_name"]] = bool(tr) and all(ok.get(t, False) for t in tr)
    return out


def decision_models() -> tuple[list[str], str]:
    comp = compliant_models()
    mm = pd.read_csv(METRICS)
    mm = mm[mm.model.map(comp).fillna(False).astype(bool)]
    mm = mm.sort_values(["f1_uniq", "model"], ascending=[False, True])
    top = mm.model.head(N_DECISION).tolist()
    return top, top[0]


def nrp(rp: float, p: float) -> float:
    return (rp - p) / (1 - p) if p < 1 else np.nan


def rprec(true: np.ndarray, pred: np.ndarray) -> tuple[float, float]:
    k = int((true <= 0).sum())
    return (precision_at_k(true, pred, k) if k else np.nan), float((true <= 0).mean())


def cell_nrp(true, pred) -> float:
    rp, p = rprec(true, pred)
    return nrp(rp, p)


def ref_nrp(true_i, pred_i, nel_i, weights: dict[int, float]) -> float:
    rp_w = p_w = 0.0
    for s, w in weights.items():
        m = nel_i == s
        if w == 0 or not m.any():
            continue
        rp, p = rprec(true_i[m], pred_i[m])
        rp_w += w * rp
        p_w += w * p
    total = sum(w for s, w in weights.items() if (nel_i == s).any())
    return nrp(rp_w / total, p_w / total)


def clusters(fw: np.ndarray) -> list[np.ndarray]:
    order = np.argsort(fw, kind="stable")
    _, starts = np.unique(fw[order], return_index=True)
    return np.split(order, starts[1:])


def outcome(cell_stable: int, cell_fw_stable: int, r_lo: float, r_hi: float, d_lo: float, d_hi: float) -> str:
    if cell_stable < MIN_STABLE or cell_fw_stable < MIN_FRAMEWORKS:
        return "too_small"
    if r_hi < R_FAIL or d_hi < D_MARGIN:
        return "fails"
    if r_lo >= R_HOLD and d_lo > D_MARGIN:
        return "holds"
    return "partial"


def main(run: str) -> int:
    run = Path(run)
    split = pd.read_csv(run / "split.csv.gz").set_index("material_id")
    wbm = pd.read_csv(RAW / "wbm_summary.csv.gz").set_index("material_id").loc[split.index]
    manifest = json.loads((RAW / "MANIFEST.json").read_text())
    files = {m["model"]: m["file"] for m in manifest["models"] if "file" in m}
    top, lead = decision_models()
    names = top + [BASELINE] + OLD_MODELS + [DESCRIPTIVE_BASELINE]
    preds = {}
    for m in dict.fromkeys(names):
        ref, p = prepare(wbm, pd.read_csv(RAW / files[m]).set_index("material_id")["e_form_per_atom"])
        preds[m] = pred_hull(ref, p).to_numpy()
    true = ref[EACH_TRUE].to_numpy()

    cell = split.cell.to_numpy()
    fw = split.framework.fillna("none").to_numpy()
    nel = split.n_elements.to_numpy()
    I = np.flatnonzero(cell == "interpolation")
    rng = np.random.default_rng(SEED)
    result = {"what": "Far-from-training stability test, Stage 1 (WBM): pre-registered decision (src/csp/far_decide.py)",
              "decision_models": top, "lead_model": lead, "baseline": BASELINE,
              "inputs": {"split_sha256": hashlib.sha256((run / "split.csv.gz").read_bytes()).hexdigest(),
                         "model_metrics_sha256": hashlib.sha256(METRICS.read_bytes()).hexdigest()},
              "thresholds": {"min_stable": MIN_STABLE, "min_frameworks_with_stable": MIN_FRAMEWORKS,
                             "r_fail_upper": R_FAIL, "r_hold_lower": R_HOLD, "d_margin": D_MARGIN},
              "cells": {}}
    rows = []
    for c in EXTRAP:
        E = np.flatnonzero(cell == c)
        st = true[E] <= 0
        weights = pd.Series(nel[E]).value_counts(normalize=True).to_dict()
        point = {}
        for m in names:
            a, b = cell_nrp(true[E], preds[m][E]), ref_nrp(true[I], preds[m][I], nel[I], weights)
            point[m] = (a, b)
            rows.append({"cell": c, "model": m, "role": "decision" if m in top else ("baseline" if m == BASELINE else "descriptive"),
                         "nrp_cell": a, "nrp_interp_ref": b, "r": a / b if b else np.nan})
        r_med = float(np.median([point[m][0] / point[m][1] for m in top]))
        d = point[lead][0] - point[BASELINE][0]
        ce, ci = clusters(fw[E]), clusters(fw[I])
        bs_r, bs_d = [], []
        for _ in range(N_BOOT):
            e = E[np.concatenate([ce[j] for j in rng.integers(0, len(ce), len(ce))])]
            i = I[np.concatenate([ci[j] for j in rng.integers(0, len(ci), len(ci))])]
            w = pd.Series(nel[e]).value_counts(normalize=True).to_dict()
            vals = {m: (cell_nrp(true[e], preds[m][e]), ref_nrp(true[i], preds[m][i], nel[i], w)) for m in top + [BASELINE]}
            bs_r.append(np.median([vals[m][0] / vals[m][1] for m in top]))
            bs_d.append(vals[lead][0] - vals[BASELINE][0])
        r_lo, r_hi = np.nanpercentile(bs_r, [2.5, 97.5])
        d_lo, d_hi = np.nanpercentile(bs_d, [2.5, 97.5])
        n_st, n_fw = int(st.sum()), int(len(set(fw[E][st])))
        result["cells"][c] = {"n": int(len(E)), "stable": n_st, "frameworks_with_stable": n_fw,
                              "median_r": r_med, "median_r_95": [float(r_lo), float(r_hi)],
                              "d_lead_minus_baseline": d, "d_95": [float(d_lo), float(d_hi)],
                              "outcome": outcome(n_st, n_fw, r_lo, r_hi, d_lo, d_hi)}
        print(f"{c:26s} median r {r_med:.3f} [{r_lo:.3f}, {r_hi:.3f}]  d {d:.3f} [{d_lo:.3f}, {d_hi:.3f}]  "
              f"-> {result['cells'][c]['outcome']}")
    result["d10_stage1"] = {"cell": "structural_extrapolation", "outcome": result["cells"]["structural_extrapolation"]["outcome"],
                            "note": "Stage 1 alone does not change D10 (pre-registered); it updates the evidence only."}
    pd.DataFrame(rows).to_csv(run / "per_model_cells.csv", index=False)
    (run / "decision.json").write_text(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
