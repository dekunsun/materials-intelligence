"""Initial-structure pilot: descriptive numbers (never change decision.json). Section 6 of
modules/csp/INITIAL_STRUCTURE_PILOT.md lists them; this code is written before any result is seen.

  - per predictor: missing predictions
  - MatRIS from initial structures: median steps, share not converged, failed relaxations, median seconds;
    median absolute energy error (chosen assignment, eV/atom) against DFT, next to the DFT-start error
  - share of entries whose chosen relaxed structure does not match the DFT structure (pymatgen StructureMatcher,
    default tolerances)
  - D of the three predictors on subsets: entries with one assignment vs several; entries whose input structure's
    framework key is unknown to MP 2023 vs known (re-assignment by the input rather than the DFT structure)
  (subsets are of the 557 entries with a template; the all-600 sensitivity is in decision.json)

Usage (repository root):  .venv/bin/python -I src/csp/init_pilot_describe.py results/<run> results/<stage2_run>
Writes <run>/descriptive.json.
"""
from __future__ import annotations

import gzip
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/csp/far_stage2_checks"))
from csp.far_stage2_decide import somers_d  # noqa: E402
from csp.init_pilot_collect import OUT  # noqa: E402
from csp.init_pilot_decide import CELL, PREDICTORS  # noqa: E402


def d_on(df: pd.DataFrame, mask) -> dict:
    sub = df[mask]
    return {"n": int(len(sub)), "stable": int(sub.stable.sum()),
            **{k: somers_d(sub.stable.to_numpy(), sub[k].to_numpy()) for k in PREDICTORS}}


def main(run: str, stage2: str) -> int:
    from pymatgen.analysis.structure_matcher import StructureMatcher
    from pymatgen.core import Structure
    from spglib_framework import spglib_framework
    from csp.far_stage2_pool import reference
    warnings.filterwarnings("ignore")
    run, stage2 = Path(run), Path(stage2)
    df = pd.read_csv(run / "entry_predictions.csv", index_col=0)
    s = pd.read_csv(stage2 / "sample.csv").set_index("mat_id")
    s = s[s.cell == CELL]
    mi = pd.concat([pd.read_csv(f) for f in sorted((run / "predictions").glob("MatRIS-10M-MP_initial*.csv"))])
    m2 = pd.read_csv(stage2 / "predictions" / "MatRIS-10M-MP.csv").set_index("mat_id").reindex(s.index)
    ok = mi[~mi.failed.astype(bool) & np.isfinite(mi.e_model)].copy()
    ok["e_atom"] = ok.e_model / ok.nsites
    chosen = ok.loc[ok.groupby("mat_id").e_atom.idxmin()].set_index("mat_id")
    e_dft = (s.energy_total / s.nsites).reindex(chosen.index)
    recs = json.load(gzip.open(OUT / "initial_structures.json.gz", "rt"))
    entries = json.load(gzip.open(OUT / "entries.json.gz", "rt"))["pilot"]
    n_assign = pd.Series({i: len(r["assignments"]) for i, r in recs.items()}).reindex(df.index)

    finals = {}
    for path in sorted(OUT.glob(f"final_structures_{run.resolve().name}*.jsonl")):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                finals[(r["mat_id"], r["assignment"])] = r["structure"]
    sm = StructureMatcher()
    match = {}
    for i, row in chosen.iterrows():
        key = (i, int(row.assignment))
        if key in finals:
            match[i] = bool(sm.fit(Structure.from_dict(finals[key]), Structure.from_dict(entries[i]["structure"])))
    fw_ref = reference()["fw"]
    input_known = {}
    for i, r in recs.items():
        if r["assignments"]:
            k = int(chosen.loc[i, "assignment"]) if i in chosen.index else 0
            fw = spglib_framework(Structure.from_dict(r["assignments"][k]["structure"]))  # already canonical
            input_known[i] = fw in fw_ref
    input_known = pd.Series(input_known).reindex(df.index)

    out = {"what": "Descriptive numbers, initial-structure pilot (src/csp/init_pilot_describe.py); never change the decision",
           "missing": {k: int(df[k].isna().sum()) for k in PREDICTORS},
           "matris_initial": {"relaxations": int(len(mi)), "failed": int(mi.failed.astype(bool).sum()),
                              "median_steps": float(mi.n_steps.median()),
                              "share_not_converged": float((mi.converged.astype(str) == "False").mean()),
                              "share_at_500_steps": float((mi.n_steps >= 500).mean()),
                              "median_seconds": float(mi.seconds.median()), "total_hours": float(mi.seconds.sum() / 3600),
                              "median_abs_error_ev_per_atom": float((chosen.e_atom - e_dft).abs().median()),
                              "median_error_ev_per_atom": float((chosen.e_atom - e_dft).median())},
           "matris_dft_start_median_abs_error_ev_per_atom": float(((m2.e_model - s.energy_total) / s.nsites).abs().median()),
           "share_chosen_relaxed_matches_dft_structure": float(np.mean(list(match.values()))) if match else None,
           "n_compared_structures": len(match),
           "D_by_assignments": {"one": d_on(df, n_assign == 1), "several": d_on(df, n_assign > 1)},
           "D_by_input_framework": {"unknown_to_mp": d_on(df, input_known == False),  # noqa: E712
                                    "known_to_mp": d_on(df, input_known == True)}}  # noqa: E712
    (run / "descriptive.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
