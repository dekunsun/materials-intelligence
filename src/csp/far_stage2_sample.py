"""Stage 2 of the far-from-training test: draw the class-stratified sample and extract its structures (no model).

Pool: data/raw/alexandria/pool/pool.csv.gz (src/csp/far_stage2_pool.py), minus GGA+U systems, minus WBM overlaps,
minus entries without a framework key.
Cells: interpolation (familiar chemistry, known framework), structural_extrapolation (familiar chemistry, unfamiliar
framework), double_extrapolation (both unfamiliar). The chemical cell is not sampled.

Per cell, drawn at random with a fixed seed:
  stable     N_STABLE entries with e_hull <= 0 (all of them if fewer)
  unstable   N_UNSTABLE_PER_BIN entries in each of the near-hull bins (0, 0.025], (0.025, 0.05], (0.05, 0.075],
             (0.075, 0.1] eV/atom. Using only near-hull entries, in equal numbers per bin, gives every cell the same
             distribution of how far the unstable entries sit above the hull, so cells differ only in the model error.
The interpolation cell is drawn to match the structural cell's mix of element counts (2, 3, 4, ...), separately for
stable and unstable entries, so the reference has the same chemical complexity as the cell it is compared with.

Usage (repository root):
    .venv/bin/python -I src/csp/far_stage2_sample.py <out_dir>
Writes <out_dir>/sample.csv (labels; committed) and data/raw/alexandria/sample_structures.json.gz (structures and
DFT raw energies for the sampled entries; regenerable, not committed).
"""
from __future__ import annotations

import bz2
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ALEX = ROOT / "data/raw/alexandria"
SEED = 11
N_STABLE = 300
N_UNSTABLE_PER_BIN = 75
BINS = [0.0, 0.025, 0.05, 0.075, 0.1]
CELLS = {(True, True): "interpolation", (True, False): "structural_extrapolation",
         (False, True): "chemical_extrapolation", (False, False): "double_extrapolation"}
SAMPLED = ["interpolation", "structural_extrapolation", "double_extrapolation"]


def eligible(pool: pd.DataFrame) -> pd.DataFrame:
    # unstable entries above 0.1 eV/atom are not sampled
    p = pool[~pool.plus_u & ~pool.in_wbm & pool.framework.notna() & (pool.e_hull <= BINS[-1])].copy()
    p["cell"] = [CELLS[(c, f)] for c, f in zip(p.chem_familiar, p.framework_known)]
    bin_index = np.searchsorted(BINS, p.e_hull.to_numpy(), side="left") - 1  # (0, 0.025] -> 0, ..., (0.075, 0.1] -> 3
    p["stratum"] = np.where(p.e_hull <= 0, "stable", np.char.add("bin", bin_index.astype(str)))
    return p


def draw(group: pd.DataFrame, n: int, rng) -> pd.DataFrame:
    return group if len(group) <= n else group.iloc[rng.choice(len(group), n, replace=False)]


def draw_matched(group: pd.DataFrame, target_mix: pd.Series, n: int, rng) -> pd.DataFrame:
    """Draw n entries from `group` with element counts in the proportions of `target_mix`."""
    parts = []
    for k, share in target_mix.items():
        sub = group[group.n_elements == k]
        parts.append(draw(sub, int(round(share * n)), rng))
    return pd.concat(parts)


def main(out: str) -> int:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    p = eligible(pd.read_csv(ALEX / "pool/pool.csv.gz").sort_values("mat_id", kind="stable").reset_index(drop=True))
    want = {"stable": N_STABLE, **{f"bin{i}": N_UNSTABLE_PER_BIN for i in range(4)}}
    picked = []
    for cell in ["structural_extrapolation", "double_extrapolation"]:
        for stratum, n in want.items():
            picked.append(draw(p[(p.cell == cell) & (p.stratum == stratum)], n, rng))
    struct = pd.concat(picked[:5])
    for stratum, n in want.items():
        s = struct[struct.stratum == stratum]
        mix = s.n_elements.value_counts(normalize=True).sort_index()
        picked.append(draw_matched(p[(p.cell == "interpolation") & (p.stratum == stratum)], mix, len(s), rng))
    sample = pd.concat(picked).sort_values(["cell", "stratum", "mat_id"])
    print(sample.groupby(["cell", "stratum"]).size().unstack().to_string())

    keep = set(sample.mat_id)
    recs = {}
    for shard in sorted(sample.shard.unique()):
        for e in json.load(bz2.open(ALEX / f"alexandria_{int(shard):05d}.json.bz2"))["entries"]:
            d = e["data"]
            if d["mat_id"] in keep:
                recs[d["mat_id"]] = {"structure": e["structure"], "energy_total": d["energy_total"],
                                     "nsites": d["nsites"], "e_hull": d["e_above_hull"]}
    assert set(recs) == keep, "some sampled entries were not found in the shards"
    sample["energy_total"] = sample.mat_id.map(lambda m: recs[m]["energy_total"])  # DFT raw energy, eV
    sample.to_csv(out / "sample.csv", index=False)
    with gzip.open(ALEX / "sample_structures.json.gz", "wt") as f:
        json.dump(recs, f)
    print("structures", len(recs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
