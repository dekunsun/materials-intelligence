"""Initial-structure pilot: score and apply the pre-registered rules (modules/csp/INITIAL_STRUCTURE_PILOT.md, 5-6).

Inputs:
  <stage2_run>/sample.csv, <stage2_run>/predictions/MatRIS-10M-MP.csv     Stage 2, from DFT-relaxed structures
  <run>/predictions/MatRIS-10M-MP_initial.csv                             src/csp/init_pilot_relax.py
  <run>/predictions/Wrenformer_initial.csv                                src/csp/init_pilot_wrenformer.py
  data/raw/alexandria/pilot/entries.json.gz                               src/csp/init_pilot_collect.py

Predicted hull distance for each of the 600 double-extrapolation entries (lower = more stable):
  MatRIS, DFT start      e_hull + (E_model - E_DFT_raw) / sites                         (as Stage 2)
  MatRIS, initial start  e_hull + (min over assignments of E_model / sites) - E_DFT_raw / sites_DFT
  Wrenformer             e_hull + (min over assignments of predicted e_form) - e_form_DFT
                         e_form_DFT on Wrenformer's scale (MP2020 corrections, MP elemental references;
                         src/csp/init_pilot_eform.py)
Failed relaxations and structures without a label are skipped when taking the minimum; an entry with nothing left
is a missing prediction and ranks last.

Entries scored (decided 2026-11-27, before any score): the main analysis uses the entries whose prototype template is
in the Alexandria library (557 of 600; the 43 others come from sources newer than the library), all three predictors
on the same entries. Sensitivity, reported but never changing the outcome: all 600, the 43 without a template ranked
last for both initial-structure predictors.

Statistics: Somers' D (src/csp/far_stage2_decide.py) for each predictor; p = D(initial) / D(DFT start);
d = D(initial) - D(Wrenformer). 95% intervals: cluster bootstrap over the DFT framework key, 1,000 resamples,
seed 11, the three D values computed on the same resample.
Rules, in order:
  fails    upper(D initial) < 0.2, or upper(d) < 0
  holds    lower(p) >= 0.8 and lower(D initial) > 0.2 and lower(d) > 0
  partial  otherwise
Repeated without the m3gnet and orbital sources (on entries with a template); if one analysis holds and the other
fails, the outcome is partial; otherwise the main outcome stands (combine() from Stage 2).

Usage (repository root):  .venv/bin/python -I src/csp/init_pilot_decide.py results/<run> results/<stage2_run>
Writes <run>/decision.json and <run>/entry_predictions.csv.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.far_stage2_decide import EXCLUDED_SOURCES, clusters, combine, somers_d  # noqa: E402
from csp.init_pilot_collect import OUT  # noqa: E402

CELL = "double_extrapolation"
D_MIN, P_HOLD = 0.2, 0.8
N_BOOT, SEED = 1000, 11
PREDICTORS = ["matris_dft_start", "matris_initial", "wrenformer"]


def outcome(d_init_lo, d_init_hi, p_lo, dd_lo, dd_hi) -> str:
    if d_init_hi < D_MIN or dd_hi < 0:
        return "fails"
    if p_lo >= P_HOLD and d_init_lo > D_MIN and dd_lo > 0:
        return "holds"
    return "partial"


def predictions(run: Path, stage2: Path) -> pd.DataFrame:
    from csp.init_pilot_eform import eform_alexandria, elemental_refs, mp_table
    s = pd.read_csv(stage2 / "sample.csv")
    s = s[s.cell == CELL].set_index("mat_id")
    e_dft_atom = s.energy_total / s.nsites
    m2 = pd.read_csv(stage2 / "predictions" / "MatRIS-10M-MP.csv").set_index("mat_id").reindex(s.index)
    dft_start = (s.e_hull + (m2.e_model - s.energy_total) / s.nsites).where(~m2.failed.fillna(True).astype(bool))
    mi = pd.concat([pd.read_csv(f) for f in sorted((run / "predictions").glob("MatRIS-10M-MP_initial*.csv"))])
    mi = mi[~mi.failed.astype(bool) & np.isfinite(mi.e_model)]
    e_init = (mi.e_model / mi.nsites).groupby(mi.mat_id).min().reindex(s.index)
    wf = pd.read_csv(run / "predictions" / "Wrenformer_initial.csv").dropna(subset=["e_form_per_atom"])
    wren = wf.groupby("mat_id").e_form_per_atom.min().reindex(s.index)
    entries = json.load(gzip.open(OUT / "entries.json.gz", "rt"))["pilot"]
    recs = json.load(gzip.open(OUT / "initial_structures.json.gz", "rt"))
    has_template = pd.Series({i: bool(recs.get(i, {}).get("assignments")) for i in s.index})
    refs = elemental_refs(mp_table())
    e_form_dft = pd.Series({i: eform_alexandria(entries[i], refs) for i in s.index})
    return pd.DataFrame({"source": s.source, "framework": s.framework, "e_hull": s.e_hull,
                         "stable": s.e_hull <= 0, "has_template": has_template, "e_form_dft_mp2020": e_form_dft,
                         "matris_dft_start": dft_start, "matris_initial": s.e_hull + e_init - e_dft_atom,
                         "wrenformer": s.e_hull + wren - e_form_dft})


def with_template(df: pd.DataFrame) -> pd.DataFrame:
    """The main analysis: entries whose initial structure could be rebuilt from a library template."""
    return df[df.has_template.astype(bool)]


def scores(df: pd.DataFrame, idx: np.ndarray) -> tuple[float, float, float]:
    st = df.stable.to_numpy()[idx]
    d = {k: somers_d(st, df[k].to_numpy()[idx]) for k in PREDICTORS}
    return d["matris_dft_start"], d["matris_initial"], d["wrenformer"]


def analyse(df: pd.DataFrame) -> dict:
    df = df.reset_index(drop=True)
    allidx = np.arange(len(df))
    cl = clusters(df.framework.to_numpy())
    d_dft, d_init, d_wren = scores(df, allidx)
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(N_BOOT):
        idx = np.concatenate([cl[j] for j in rng.integers(0, len(cl), len(cl))])
        a, b, c = scores(df, idx)
        bs.append((b, b / a, b - c))
    bs = np.array(bs)
    (di_lo, di_hi), (p_lo, p_hi), (dd_lo, dd_hi) = [np.nanpercentile(bs[:, j], [2.5, 97.5]) for j in range(3)]
    return {"n": int(len(df)), "stable": int(df.stable.sum()), "frameworks": len(cl),
            "missing": {k: int(df[k].isna().sum()) for k in PREDICTORS},
            "D_matris_dft_start": d_dft, "D_matris_initial": d_init, "D_wrenformer": d_wren,
            "D_initial_95": [float(di_lo), float(di_hi)],
            "p": d_init / d_dft, "p_95": [float(p_lo), float(p_hi)],
            "d": d_init - d_wren, "d_95": [float(dd_lo), float(dd_hi)],
            "outcome": outcome(di_lo, di_hi, p_lo, dd_lo, dd_hi)}


def main(run: str, stage2: str) -> int:
    run, stage2 = Path(run), Path(stage2)
    df = predictions(run, stage2)
    df.to_csv(run / "entry_predictions.csv")
    main_df = with_template(df)
    main_res = analyse(main_df)
    sub_res = analyse(main_df[~main_df.source.isin(EXCLUDED_SOURCES)])
    final = combine(main_res["outcome"], sub_res["outcome"])
    dec = {"what": "Initial-structure pilot decision (src/csp/init_pilot_decide.py), double-extrapolation cell",
           "outcome": final, "main_with_template": main_res, f"without_{'_'.join(EXCLUDED_SOURCES)}": sub_res,
           "sensitivity_all_600_missing_rank_last": analyse(df)}
    (run / "decision.json").write_text(json.dumps(dec, indent=1))
    print(json.dumps(dec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
