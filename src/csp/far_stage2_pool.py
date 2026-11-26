"""Stage 2 of the far-from-training test: label every Alexandria PBE entry with its cell (no model, no scoring).

For each entry of the 58 shards in data/raw/alexandria/, record:
  chem_familiar    its chemical system appears in the MP 2023 snapshot (Stage 1's chemical axis)
  framework        spglib framework key, canonicalised over equivalent origin choices
                   (src/csp/far_stage2_checks/spglib_framework.py; 99.4% agreement with MP's labels on 3,000 structures)
  framework_known  that key appears among the MP 2023 snapshot's canonicalised framework keys
  plus_u           GGA+U system (Co, Cr, Fe, Mn, Mo, Ni, V or W together with O or F): excluded, raw energies differ from MP
  in_wbm           same reduced formula, space group and number of sites as a WBM entry: excluded
  source           first part of `location`, the generating workflow; used for the source strata
  e_hull, stable   Alexandria's own hull distance, and e_hull <= 0
Only labels and truth are stored, not structures; sampled structures are re-read from the shards later.

Usage (repository root):
    .venv/bin/python -I src/csp/far_stage2_pool.py [--workers 4]
Writes data/raw/alexandria/pool/shard_XXXXX.csv.gz (one per shard, skipped if present) and
data/raw/alexandria/pool/pool.csv.gz (all shards).
"""
from __future__ import annotations

import argparse
import bz2
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/csp/far_stage2_checks"))
ALEX = ROOT / "data/raw/alexandria"
OUT = ALEX / "pool"
U_METALS = {"Co", "Cr", "Fe", "Mn", "Mo", "Ni", "V", "W"}
_REF = {}


def reference():
    """MP 2023 chemical systems and framework keys, and WBM (formula, space group, sites) keys; built once per worker."""
    if not _REF:
        from pymatgen.core import Composition
        from csp.far_posthoc_canonical import canonical
        from csp.far_split import framework
        from csp.run_screening import RAW, chemsys, mp2023_ids
        mp = pd.read_csv(RAW / "mp_energies.csv.gz")
        mp = mp[mp.material_id.isin(mp2023_ids())]
        wbm = pd.read_csv(RAW / "wbm_summary.csv.gz")
        _REF["sys"] = set(mp.formula.dropna().map(chemsys))
        _REF["fw"] = set(mp.protostructure_spglib.dropna().map(framework).map(canonical))
        _REF["wbm"] = set(zip(wbm.formula.map(lambda f: Composition(f).reduced_formula),
                              wbm.protostructure_spglib.str.split("_").str[2].astype(int), wbm.n_sites.astype(int)))
    return _REF


def label_shard(i: int) -> str:
    dest = OUT / f"shard_{i:05d}.csv.gz"
    if dest.exists():
        return f"{dest.name} exists"
    from pymatgen.core import Composition, Structure
    from spglib_framework import spglib_framework
    ref = reference()
    rows = []
    for e in json.load(bz2.open(ALEX / f"alexandria_{i:05d}.json.bz2"))["entries"]:
        d = e["data"]
        el = set(d["elements"])
        fw = spglib_framework(Structure.from_dict(e["structure"]))
        rows.append({"mat_id": d["mat_id"], "shard": i, "formula": Composition(e["composition"]).reduced_formula,
                     "spg": d["spg"], "nsites": d["nsites"], "n_elements": len(el),
                     "source": d["location"].split("/")[0],
                     "year": d["run_timestamp"]["string"][:4] if d.get("run_timestamp") else None,
                     "chem_familiar": "-".join(sorted(el)) in ref["sys"],
                     "framework": fw, "framework_known": fw in ref["fw"],
                     "plus_u": bool(el & U_METALS) and bool(el & {"O", "F"}),
                     "e_hull": d["e_above_hull"], "stable": d["e_above_hull"] <= 0})
    df = pd.DataFrame(rows)
    df["in_wbm"] = [k in ref["wbm"] for k in zip(df.formula, df.spg, df.nsites)]
    tmp = dest.with_suffix(".tmp")
    df.to_csv(tmp, index=False, compression="gzip")
    tmp.rename(dest)  # a shard file exists only when complete
    return f"{dest.name} {len(df)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    shards = sorted(int(p.name[11:16]) for p in ALEX.glob("alexandria_*.json.bz2"))
    assert len(shards) == 58, f"expected 58 shards, found {len(shards)}"
    with Pool(args.workers, maxtasksperchild=4) as pool:
        for msg in pool.imap_unordered(label_shard, shards):
            print(msg, flush=True)
    df = pd.concat([pd.read_csv(OUT / f"shard_{i:05d}.csv.gz") for i in shards], ignore_index=True)
    assert df.mat_id.is_unique, "duplicate mat_id across shards"
    df.to_csv(OUT / "pool.csv.gz", index=False)
    print("entries", len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
