"""Initial-structure pilot, step 1: collect what the pilot needs from the Alexandria shards (no model, no scoring).

Design: modules/csp/INITIAL_STRUCTURE_PILOT.md. Two sets of entries are read from the 58 PBE shards:
  pilot       the 600 double-extrapolation entries of the Stage 2 sample (results/<stage2_run>/sample.csv):
              prototype_id, composition, raw energy, and the full entry (for the MP2020 corrections later)
  validation  for the formation-energy check of Section 4: Alexandria entries outside GGA+U systems whose reduced
              formula, space group and number of sites match an MP 2023 GGA entry; 2,000 drawn with seed 11

Also reports prototype coverage: whether every pilot prototype_id has a template in data/raw/alexandria/prototypes/.

Usage (repository root):  .venv/bin/python -I src/csp/init_pilot_collect.py results/<stage2_run> [--workers 4]
Writes data/raw/alexandria/pilot/entries.json.gz and data/raw/alexandria/pilot/coverage.json.
"""
from __future__ import annotations

import argparse
import bz2
import gzip
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
ALEX = ROOT / "data/raw/alexandria"
PROTO = ALEX / "prototypes/prototypes"
OUT = ALEX / "pilot"
N_VALIDATION, SEED = 2000, 11
_WANT: set[str] = set()


def template_path(prototype_id: str) -> Path:
    """prototypes/<number of elements>/<anonymous formula>/<prototype_id>.cif, as the archive is laid out."""
    anon = prototype_id.split("_")[0]
    n_el = sum(c.isupper() for c in anon)
    return PROTO / str(n_el) / anon / f"{prototype_id}.cif"


def validation_ids(pool: pd.DataFrame) -> list[str]:
    from pymatgen.core import Composition
    from csp.fetch_discovery import OUT as RAW
    from csp.run_screening import mp2023_ids
    mp = pd.read_csv(RAW / "mp_energies.csv.gz", keep_default_na=False, na_values=[""])  # "NaN" is sodium nitride
    mp = mp[mp.material_id.isin(mp2023_ids()) & (mp.energy_type == "GGA") & mp.n_sites.notna()]
    keys = set(zip(mp.formula.map(lambda f: Composition(f).reduced_formula),
                   mp.protostructure_spglib.str.split("_").str[2].astype(int), mp.n_sites.astype(int)))
    cand = pool[~pool.plus_u & (pool.n_elements >= 2)]
    cand = cand[[k in keys for k in zip(cand.formula, cand.spg, cand.nsites)]]
    return sorted(cand.sample(min(N_VALIDATION, len(cand)), random_state=SEED).mat_id)


def read_shard(i: int) -> dict:
    out = {}
    for e in json.load(bz2.open(ALEX / f"alexandria_{i:05d}.json.bz2"))["entries"]:
        if e["data"]["mat_id"] in _WANT:
            out[e["data"]["mat_id"]] = e
    return out


def init(want):
    _WANT.update(want)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage2_run")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    s = pd.read_csv(Path(args.stage2_run) / "sample.csv")
    pilot = s[s.cell == "double_extrapolation"]
    assert len(pilot) == 600, len(pilot)
    pool = pd.read_csv(ALEX / "pool/pool.csv.gz", keep_default_na=False, na_values=[""])
    val = [i for i in validation_ids(pool) if i not in set(pilot.mat_id)]
    want = set(pilot.mat_id) | set(val)
    shards = sorted(set(pool.set_index("mat_id").loc[sorted(want), "shard"].astype(int)))
    found = {}
    with Pool(args.workers, initializer=init, initargs=(want,), maxtasksperchild=4) as p:
        for k, part in enumerate(p.imap_unordered(read_shard, shards)):
            found.update(part)
            print("shard", k + 1, "of", len(shards), len(found), flush=True)
    assert want <= set(found), "some entries were not found in the shards"
    OUT.mkdir(exist_ok=True)
    rec = {"pilot": {i: found[i] for i in sorted(pilot.mat_id)}, "validation": {i: found[i] for i in val}}
    with gzip.open(OUT / "entries.json.gz", "wt") as f:
        json.dump(rec, f)
    protos = {i: e["data"]["prototype_id"] for i, e in rec["pilot"].items()}
    missing = sorted(i for i, pid in protos.items() if not template_path(pid).exists())
    cov = {"pilot_entries": len(protos), "distinct_prototypes": len(set(protos.values())),
           "missing_template": len(missing), "missing_ids": missing, "validation_entries": len(val)}
    (OUT / "coverage.json").write_text(json.dumps(cov, indent=1))
    print({k: v for k, v in cov.items() if k != "missing_ids"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
