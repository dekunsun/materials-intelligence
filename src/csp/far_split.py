"""Split WBM into the four cells of the far-from-training stability test (modules/csp/FAR_FROM_TRAINING_TEST.md).

Pre-registered with that document. Computes no model metric; it only labels every WBM structure.

Axes, both on the INITIAL (pre-relaxation) structure, against the training reference:
  chemistry C1  familiar if the chemical system (set of elements) appears at least once in the reference
  structure S2  known if the framework key appears at least once in the reference. Framework key = Pearson symbol
                + space group + multiset of all Wyckoff letters, ignoring which element sits on which site.
Reference: the MP 2023-02-07 snapshot (154,718 ids, labels from mp_energies.csv.gz `protostructure_spglib`), plus any
extra reference labels in data/raw/mptrj/mptrj_only_reference.csv (MPtrj materials missing from the snapshot), if
that file exists. Descriptive extras: C2 (an element pair never seen together), S1 (element-order-invariant label),
S2 on the relaxed structure, element count, WBM step, unique-prototype flag.

Usage (repository root):
    .venv/bin/python -I src/csp/far_split.py results/<run_id>
Writes <run>/split.csv.gz and <run>/split_summary.json.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.discovery_metrics import EACH_TRUE, UNIQ  # noqa: E402
from csp.run_screening import RAW, chemsys, mp2023_ids, prototype_type  # noqa: E402

EXTRA_REF = ROOT / "data/raw/mptrj/mptrj_only_reference.csv"   # columns: material_id, formula, protostructure_spglib
CELLS = {(True, True): "interpolation", (True, False): "structural_extrapolation",
         (False, True): "chemical_extrapolation", (False, False): "double_extrapolation"}


def framework(label) -> str | None:
    """'A2BC_cF16_225_c_a_b:Ag-Ba-La' -> 'cF16_225_abc'. None for a missing label."""
    if not isinstance(label, str):
        return None
    parts = label.split(":")[0].split("_")
    letters = []
    for group in parts[3:]:
        for num, ch in re.findall(r"(\d*)([a-zA-Z])", group):
            letters += [ch] * (int(num) if num else 1)
    return f"{parts[1]}_{parts[2]}_" + "".join(sorted(letters))


def reference() -> tuple[pd.DataFrame, dict]:
    mp = pd.read_csv(RAW / "mp_energies.csv.gz")
    mp = mp[mp.material_id.isin(mp2023_ids())][["material_id", "formula", "protostructure_spglib"]]
    info = {"mp_snapshot_rows": int(len(mp))}
    if EXTRA_REF.exists():
        extra = pd.read_csv(EXTRA_REF)[["material_id", "formula", "protostructure_spglib"]]
        info["extra_reference_rows"] = int(len(extra))
        info["extra_reference_sha256"] = hashlib.sha256(EXTRA_REF.read_bytes()).hexdigest()
        mp = pd.concat([mp, extra], ignore_index=True)
    else:
        info["extra_reference_rows"] = 0
    return mp.dropna(subset=["formula"]), info


def main(run: str) -> int:
    out = Path(run)
    out.mkdir(parents=True, exist_ok=True)
    ref, info = reference()
    ref_sys = set(ref.formula.map(chemsys))
    ref_pairs = {p for s in ref_sys for p in itertools.combinations(s.split("-"), 2)}
    ref_frames = set(ref.protostructure_spglib.dropna().map(framework))
    ref_types = set(ref.protostructure_spglib.dropna().map(lambda x: prototype_type(x, True)))

    wbm = pd.read_csv(RAW / "wbm_summary.csv.gz").set_index("material_id")
    sysw = wbm.formula.map(chemsys)
    d = pd.DataFrame(index=wbm.index)
    d["chemsys"] = sysw
    d["n_elements"] = sysw.str.count("-") + 1
    d["chem_familiar"] = sysw.isin(ref_sys)
    d["c2_familiar"] = sysw.map(lambda s: all(p in ref_pairs for p in itertools.combinations(s.split("-"), 2)))
    d["framework"] = wbm.protostructure_spglib_initial_structure.map(framework)
    d["framework_known"] = d.framework.isin(ref_frames)
    d["s1_known"] = wbm.protostructure_spglib_initial_structure.map(lambda x: prototype_type(x, True)).isin(ref_types)
    d["framework_relaxed"] = wbm.protostructure_spglib.map(framework)
    d["framework_relaxed_known"] = d.framework_relaxed.isin(ref_frames)
    d["cell"] = [CELLS[(c, f)] for c, f in zip(d.chem_familiar, d.framework_known)]
    d["unique_prototype"] = wbm[UNIQ].astype(bool)
    d["wbm_step"] = d.index.str.split("-").str[1].astype(int)
    d["stable"] = wbm[EACH_TRUE].round(3) <= 0
    d.to_csv(out / "split.csv.gz")

    summary = {"what": "WBM split for the far-from-training stability test (no model metrics)", "reference": info,
               "reference_chemical_systems": len(ref_sys), "reference_frameworks": len(ref_frames), "cells": {}}
    for pool, sub in [("full", d), ("unique_prototypes", d[d.unique_prototype])]:
        rows = {}
        for cell, g in sub.groupby("cell"):
            rows[cell] = {"n": int(len(g)), "stable": int(g.stable.sum()), "stable_share": round(float(g.stable.mean()), 4),
                          "frameworks": int(g.framework.nunique()),
                          "frameworks_with_stable": int(g.loc[g.stable, "framework"].nunique()),
                          "n_elements_mix": {int(k): round(float(v), 4) for k, v in g.n_elements.value_counts(normalize=True).sort_index().items()}}
        summary["cells"][pool] = rows
    summary["split_sha256"] = hashlib.sha256((out / "split.csv.gz").read_bytes()).hexdigest()
    (out / "split_summary.json").write_text(json.dumps(summary, indent=1))
    for cell, r in summary["cells"]["full"].items():
        print(f"{cell:26s} n={r['n']:>7,} stable={r['stable']:>6,} share={r['stable_share']:.3f} "
              f"frameworks={r['frameworks']} with_stable={r['frameworks_with_stable']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
