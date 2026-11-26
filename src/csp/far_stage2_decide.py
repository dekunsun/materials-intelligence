"""Stage 2 of the far-from-training test: score the four models and apply the pre-registered rules.

Inputs (in <run>/): sample.csv (src/csp/far_stage2_sample.py) and predictions/<model>.csv
(src/csp/far_stage2_relax.py; columns mat_id, e_model, failed).

Predicted hull distance = Alexandria hull distance + (model energy - DFT raw energy) / sites. The energy corrections
are the same for both energies of one composition, so they cancel. A failed relaxation is ranked last.

Score per model and cell: Somers' D = 2 * AUC - 1 for separating stable (e_hull <= 0) from unstable entries,
ranking by predicted hull distance (lower = more stable). 0 is random, 1 is perfect.
r = D(extrapolation cell) / D(interpolation cell). Decision statistics: the median r of the four models, and the
median D of the four models in the cell. 95% intervals: cluster bootstrap over frameworks (each cell and the
interpolation reference resampled separately), 1,000 resamples, seed 11.

Rules, checked in order, on the structural-extrapolation cell (decides D10):
  too_small  fewer than 50 stable entries in the cell's sample, or fewer than 20 frameworks holding one
  fails      upper(median r) < 0.5, or upper(median D in the cell) < 0.2
  holds      lower(median r) >= 0.8 and lower(median D in the cell) > 0.2
  partial    otherwise
The analysis is repeated without the m3gnet and orbital sources. If one of the two holds and the other fails, the
outcome is partial; otherwise the main outcome stands. The double-extrapolation cell is scored the same way and
reported, but does not decide.

Usage (repository root):  .venv/bin/python -I src/csp/far_stage2_decide.py results/<run>
Writes <run>/decision.json and <run>/per_model_cells.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

MODELS = ["CHGNet", "MACE-MP-0", "SevenNet-0", "MatRIS-10M-MP"]
EXCLUDED_SOURCES = ["m3gnet", "orbital"]
CELLS = ["structural_extrapolation", "double_extrapolation"]
MIN_STABLE, MIN_FRAMEWORKS = 50, 20
R_FAIL, R_HOLD, D_MIN = 0.5, 0.8, 0.2
N_BOOT, SEED = 1000, 11


def somers_d(stable: np.ndarray, pred: np.ndarray) -> float:
    """2*AUC-1 where a lower prediction should mean stable; ties count half; NaN predictions rank last."""
    score = -np.where(np.isnan(pred), np.inf, pred)
    n1, n0 = int(stable.sum()), int((~stable).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = rankdata(score)
    auc = (ranks[stable].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return float(2 * auc - 1)


def outcome(n_stable: int, fw_stable: int, r_lo: float, r_hi: float, d_lo: float, d_hi: float) -> str:
    if n_stable < MIN_STABLE or fw_stable < MIN_FRAMEWORKS:
        return "too_small"
    if r_hi < R_FAIL or d_hi < D_MIN:
        return "fails"
    if r_lo >= R_HOLD and d_lo > D_MIN:
        return "holds"
    return "partial"


def combine(main: str, without_sources: str) -> str:
    return "partial" if {main, without_sources} == {"holds", "fails"} else main


def clusters(keys: np.ndarray) -> list[np.ndarray]:
    _, inv = np.unique(keys, return_inverse=True)
    return [np.flatnonzero(inv == j) for j in range(inv.max() + 1)]


def stats(E, I, stable, preds):
    dE = np.array([somers_d(stable[E], preds[m][E]) for m in MODELS])
    dI = np.array([somers_d(stable[I], preds[m][I]) for m in MODELS])
    return float(np.median(dE / dI)), float(np.median(dE)), dE, dI


def analyse(s: pd.DataFrame, preds_all: dict) -> dict:
    s = s.reset_index(drop=True)
    stable = (s.e_hull <= 0).to_numpy()
    fw = s.framework.to_numpy()
    preds = {m: preds_all[m].reindex(s.mat_id).to_numpy() for m in MODELS}
    I = np.flatnonzero(s.cell == "interpolation")
    ci = clusters(fw[I])
    rng = np.random.default_rng(SEED)
    out = {}
    for cell in CELLS:
        E = np.flatnonzero(s.cell == cell)
        ce = clusters(fw[E])
        r, d, dE, dI = stats(E, I, stable, preds)
        bs = []
        for _ in range(N_BOOT):
            e = E[np.concatenate([ce[j] for j in rng.integers(0, len(ce), len(ce))])]
            i = I[np.concatenate([ci[j] for j in rng.integers(0, len(ci), len(ci))])]
            bs.append(stats(e, i, stable, preds)[:2])
        bs = np.array(bs)
        r_lo, r_hi = np.nanpercentile(bs[:, 0], [2.5, 97.5])
        d_lo, d_hi = np.nanpercentile(bs[:, 1], [2.5, 97.5])
        n_stable, fw_stable = int(stable[E].sum()), len(set(fw[E][stable[E]]))
        out[cell] = {"n": int(len(E)), "stable": n_stable, "frameworks": len(ce), "frameworks_with_stable": fw_stable,
                     "median_r": r, "median_r_95": [float(r_lo), float(r_hi)],
                     "median_D": d, "median_D_95": [float(d_lo), float(d_hi)],
                     "D_cell": dict(zip(MODELS, dE.round(4).tolist())),
                     "D_interpolation": dict(zip(MODELS, dI.round(4).tolist())),
                     "outcome": outcome(n_stable, fw_stable, r_lo, r_hi, d_lo, d_hi)}
    return out


def main(run: str) -> int:
    run = Path(run)
    s = pd.read_csv(run / "sample.csv")
    preds = {}
    for m in MODELS:
        p = pd.read_csv(run / "predictions" / f"{m}.csv").set_index("mat_id")
        p = p.join(s.set_index("mat_id")[["e_hull", "nsites", "energy_total"]], how="right")
        pred = p.e_hull + (p.e_model - p.energy_total) / p.nsites
        preds[m] = pred.where(~p.failed.fillna(True).astype(bool))
    main_res = analyse(s, preds)
    sub_res = analyse(s[~s.source.isin(EXCLUDED_SOURCES)], preds)
    final = combine(main_res["structural_extrapolation"]["outcome"], sub_res["structural_extrapolation"]["outcome"])
    dec = {"what": "Stage 2 decision (src/csp/far_stage2_decide.py); structural cell decides",
           "outcome": final, "main": main_res, f"without_{'_'.join(EXCLUDED_SOURCES)}": sub_res,
           "failed_relaxations": {m: int(preds[m].isna().sum()) for m in MODELS}}
    (run / "decision.json").write_text(json.dumps(dec, indent=1))
    rows = []
    for name, res in [("all_sources", main_res), ("without_m3gnet_orbital", sub_res)]:
        for cell, v in res.items():
            for m in MODELS:
                rows.append({"analysis": name, "cell": cell, "model": m, "D_cell": v["D_cell"][m],
                             "D_interpolation": v["D_interpolation"][m], "r": v["D_cell"][m] / v["D_interpolation"][m]})
    pd.DataFrame(rows).to_csv(run / "per_model_cells.csv", index=False)
    print(json.dumps({"outcome": final, "structural": {k: main_res["structural_extrapolation"][k] for k in
                      ["median_r", "median_r_95", "median_D", "median_D_95", "outcome"]}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
