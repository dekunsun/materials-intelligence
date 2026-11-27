"""Descriptive numbers for Stage 2 of the far-from-training test (never change decision.json).

Pre-registered as descriptive in modules/csp/FAR_FROM_TRAINING_STAGE2.md, Section 5:
  - per model and cell: median absolute energy error (model - DFT raw energy, eV/atom), median relaxation steps,
    share not converged, failures
  - Somers' D per cell on the Stage 1 data (WBM, post-hoc canonical framework key, full cells), for the 10 Stage 1
    decision models, with the median ratio r against interpolation; and the same for CHGNet and MACE-MP-0, the two
    models present in both stages
Stage 1's interpolation reference is not reweighted here (Somers' D does not depend on the stable share).

Usage (repository root):  .venv/bin/python -I src/csp/far_stage2_describe.py results/<stage2_run> results/<stage1_run>
Writes <stage2_run>/descriptive.json.
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
from csp.far_decide import RAW, decision_models  # noqa: E402
from csp.far_stage2_decide import MODELS, somers_d  # noqa: E402

STAGE1_CELLS = ["interpolation", "structural_extrapolation", "chemical_extrapolation", "double_extrapolation"]


def stage2(run: Path) -> dict:
    s = pd.read_csv(run / "sample.csv").set_index("mat_id")
    out = {}
    for m in MODELS:
        p = pd.read_csv(run / "predictions" / f"{m}.csv").set_index("mat_id").join(s, how="right")
        p["err"] = (p.e_model - p.energy_total) / p.nsites
        out[m] = {c: {"n": int(len(g)), "failed_or_missing": int(g.failed.fillna(True).astype(bool).sum()),
                      "median_abs_error_ev_per_atom": float(g.err.abs().median()),
                      "median_error_ev_per_atom": float(g.err.median()),
                      "median_steps": float(g.n_steps.median()),
                      "share_not_converged": float((g.converged.astype(str) == "False").mean())}
                  for c, g in p.groupby("cell")}
    return out


def stage1(run: Path) -> dict:
    split = pd.read_csv(run / "posthoc_canonical_framework" / "split.csv.gz").set_index("material_id")
    wbm = pd.read_csv(RAW / "wbm_summary.csv.gz").set_index("material_id").loc[split.index]
    files = {m["model"]: m["file"] for m in json.loads((RAW / "MANIFEST.json").read_text())["models"] if "file" in m}
    top, _ = decision_models()
    models = list(dict.fromkeys(top + ["CHGNet", "MACE-MP-0", "Wrenformer"]))
    D = {}
    for m in models:
        ref, p = prepare(wbm, pd.read_csv(RAW / files[m]).set_index("material_id")["e_form_per_atom"])
        pred, true = pred_hull(ref, p).to_numpy(), ref[EACH_TRUE].to_numpy()
        D[m] = {c: somers_d(true[(split.cell == c).to_numpy()] <= 0, pred[(split.cell == c).to_numpy()])
                for c in STAGE1_CELLS}
    r = {c: float(np.median([D[m][c] / D[m]["interpolation"] for m in top])) for c in STAGE1_CELLS[1:]}
    return {"somers_D": D, "median_r_top10": r, "top10": top}


def main(run2: str, run1: str) -> int:
    run2 = Path(run2)
    out = {"what": "Descriptive numbers, Stage 2 (src/csp/far_stage2_describe.py); never change the decision",
           "stage2_per_model_cell": stage2(run2), "stage1_somers_D": stage1(Path(run1))}
    (run2 / "descriptive.json").write_text(json.dumps(out, indent=1))
    for m, v in out["stage2_per_model_cell"].items():
        print(m, {c: (round(x["median_abs_error_ev_per_atom"], 4), x["failed_or_missing"]) for c, x in v.items()})
    print("stage1 median r (Somers' D)", out["stage1_somers_D"]["median_r_top10"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
