"""Initial-structure pilot, step 2: rebuild an initial structure for each pilot entry from its prototype template.

Design: modules/csp/INITIAL_STRUCTURE_PILOT.md, Section 3. For each of the 600 double-extrapolation entries:
  1. Read the template data/raw/alexandria/prototypes/prototypes/<n>/<anonymous formula>/<prototype_id>.cif. Its sites
     carry placeholder species Xxa, Xxb, ...; the cell and positions come from the structure the template was made from.
  2. Put the entry's elements on the placeholders by matching reduced counts (element with count 2 on the placeholder
     with count 2). Elements with the same count can go either way: every assignment is listed, assignments that give
     the same structure (pymatgen StructureMatcher) are merged, and if more than 6 remain, 6 are drawn with seed 11.
  3. Scale the cell with pymatgen's DLSVolumePredictor (data-mined bond lengths; scaling kept within 0.5-1.5 of the
     template volume). If it raises, the template volume is kept and this is recorded.
Nothing from the entry's DFT result (structure, energy, hull distance) is read here except its composition.
An entry whose template is missing or whose counts do not match the template is a failed rebuild.

Usage (repository root):  .venv/bin/python -I src/csp/init_pilot_build.py [--limit N]
Writes data/raw/alexandria/pilot/initial_structures.json.gz:
  {mat_id: {"status": "ok" | reason, "assignments": [{"map": {placeholder: element}, "volume_scaled": bool,
            "structure": dict}]}}
and data/raw/alexandria/pilot/build_summary.json.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import sys
import warnings
from collections import Counter
from functools import reduce
from math import gcd
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.init_pilot_collect import OUT, template_path  # noqa: E402

MAX_ASSIGNMENTS, SEED = 6, 11


def reduced_counts(counts: dict) -> dict:
    g = reduce(gcd, [int(round(v)) for v in counts.values()])
    return {k: int(round(v)) // g for k, v in counts.items()}


def assignments(placeholders: dict, elements: dict) -> list[dict] | str:
    """All maps placeholder -> element that preserve reduced counts, or a reason string if none exists."""
    if sorted(placeholders.values()) != sorted(elements.values()):
        return "counts differ from template"
    by_count_p, by_count_e = {}, {}
    for p, n in placeholders.items():
        by_count_p.setdefault(n, []).append(p)
    for e, n in elements.items():
        by_count_e.setdefault(n, []).append(e)
    groups = [[dict(zip(by_count_p[n], perm)) for perm in itertools.permutations(sorted(by_count_e[n]))]
              for n in sorted(by_count_p)]
    return [reduce(lambda a, b: {**a, **b}, combo, {}) for combo in itertools.product(*groups)]


def build(mat_id: str, entry: dict) -> dict:
    from pymatgen.analysis.structure_matcher import StructureMatcher
    from pymatgen.analysis.structure_prediction.volume_predictor import DLSVolumePredictor
    from pymatgen.core import Composition, Structure
    path = template_path(entry["data"]["prototype_id"])
    if not path.exists():
        return {"status": "template missing", "assignments": []}
    tmpl = Structure.from_file(path)
    ph = reduced_counts(Counter(s.specie.symbol for s in tmpl))
    el = reduced_counts(Composition(entry["composition"]).get_el_amt_dict())
    maps = assignments(ph, el)
    if isinstance(maps, str):
        return {"status": maps, "assignments": []}
    filled = []
    for m in maps:
        s = tmpl.copy()
        s.replace_species({sp: m[sp.symbol] for sp in tmpl.composition.elements})
        filled.append((m, s))
    if len(filled) > 1:  # merge assignments that give the same structure
        sm, kept = StructureMatcher(), []
        for m, s in filled:
            if not any(sm.fit(s, t) for _, t in kept):
                kept.append((m, s))
        filled = kept
    if len(filled) > MAX_ASSIGNMENTS:
        pick = sorted(np.random.default_rng(SEED).choice(len(filled), MAX_ASSIGNMENTS, replace=False))
        filled = [filled[i] for i in pick]
    out = []
    for m, s in filled:
        try:
            s2, scaled = DLSVolumePredictor().get_predicted_structure(s), True
        except Exception:  # noqa: BLE001 - keep the template volume, recorded
            s2, scaled = s, False
        out.append({"map": m, "volume_scaled": scaled, "structure": s2.as_dict()})
    return {"status": "ok", "assignments": out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    warnings.filterwarnings("ignore")
    entries = json.load(gzip.open(OUT / "entries.json.gz", "rt"))["pilot"]
    ids = sorted(entries)[: args.limit] if args.limit else sorted(entries)
    res = {}
    for k, i in enumerate(ids):
        res[i] = build(i, entries[i])
        if k % 100 == 0:
            print(k, i, res[i]["status"], len(res[i]["assignments"]), flush=True)
    n_assign = Counter(len(r["assignments"]) for r in res.values() if r["status"] == "ok")
    summary = {"entries": len(res), "status": dict(Counter(r["status"] for r in res.values())),
               "assignments_per_entry": {str(k): v for k, v in sorted(n_assign.items())},
               "total_assignments": sum(len(r["assignments"]) for r in res.values()),
               "not_volume_scaled": sum(not a["volume_scaled"] for r in res.values() for a in r["assignments"])}
    if not args.limit:
        with gzip.open(OUT / "initial_structures.json.gz", "wt") as f:
            json.dump(res, f)
        (OUT / "build_summary.json").write_text(json.dumps(summary, indent=1))
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
