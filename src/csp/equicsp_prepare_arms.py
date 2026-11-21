"""Prepare EquiCSP training data for every arm of the CSP random-removal control.

Runs in the separate EquiCSP environment (Python 3.8, torch 1.9.0; see
src/csp/requirements-equicsp.txt), not in the project's main .venv.

Step 1 preprocesses the full MP-20 train/val/test once with EquiCSP's own
`preprocess` (Niggli reduction, CrystalNN graphs; same settings as its
conf/data/mp_20.yaml). This is CPU-only and slow, so it runs locally, not on a
rented GPU.

Step 2 writes, for each arm, the filtered CSVs and the filtered preprocessed
caches (same order as the CSV), so a training machine only has to load them:

    data/raw/equicsp_data/<arm>/{train,val,test}.csv and {train,val,test}_ori.pt

Arms: ABC2D6 and PEROV use the paper's released removed-ID lists; R1-R3 use our
committed lists in results/csp_random_control_20261121T223433Z/splits/. The test
split is never filtered.

Usage (from the repository root):
    data/raw/equicsp_venv/bin/python -I src/csp/equicsp_prepare_arms.py --workers 10
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "equicsp_src"  # EquiCSP at commit d7921c3
RAW = ROOT / "data" / "raw" / "csp_ablation"
OUT = ROOT / "data" / "raw" / "equicsp_data"
SPLITS = ROOT / "results" / "csp_random_control_20261121T223433Z" / "splits"
os.environ.setdefault("PROJECT_ROOT", str(SRC))
sys.path.insert(0, str(SRC))

import pandas as pd  # noqa: E402
import torch  # noqa: E402
from equicsp.common.data_utils import preprocess  # noqa: E402

# Settings from EquiCSP conf/data/mp_20.yaml
SETTINGS = dict(niggli=True, primitive=False, graph_method="crystalnn", prop_list=["formation_energy_per_atom"],
                use_space_group=False, tol=0.1)


def removed_ids(arm: str, part: str) -> set[str]:
    if arm in ("ABC2D6", "PEROV"):
        f = RAW / "benchmark" / "ablation" / "removed_ids" / f"{arm}_{part}.csv"
    else:
        f = SPLITS / f"{arm}_{part}_removed.csv"
    return set(pd.read_csv(f)["material_id"])


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--arms", nargs="+", default=["ABC2D6", "PEROV", "R1", "R2", "R3"])
    args = ap.parse_args()

    full = OUT / "full"; full.mkdir(parents=True, exist_ok=True)
    timing = {}
    for part in ("train", "val", "test"):
        cache = full / f"{part}_ori.pt"
        if not cache.exists():
            t0 = time.time()
            data = preprocess(str(RAW / "mp_20" / f"{part}.csv"), args.workers, **SETTINGS)
            torch.save(data, cache)
            timing[part] = round(time.time() - t0, 1)
            print(f"preprocessed {part}: {len(data)} structures in {timing[part]} s", flush=True)

    manifest = {"equicsp_commit": "d7921c37260f05386fde021d29e0724f995ee9c3", "settings": SETTINGS,
                "torch": torch.__version__, "preprocess_seconds": timing, "arms": {}}
    for arm in args.arms:
        d = OUT / arm; d.mkdir(exist_ok=True)
        manifest["arms"][arm] = {}
        for part in ("train", "val", "test"):
            df = pd.read_csv(RAW / "mp_20" / f"{part}.csv")
            cached = torch.load(full / f"{part}_ori.pt")
            assert [c["mp_id"] for c in cached] == list(df["material_id"]), f"{part}: cache order differs from CSV"
            drop = removed_ids(arm, part) if part != "test" else set()
            keep = ~df["material_id"].isin(drop)
            df[keep].to_csv(d / f"{part}.csv", index=False)
            torch.save([c for c, k in zip(cached, keep) if k], d / f"{part}_ori.pt")
            manifest["arms"][arm][part] = {"rows": int(keep.sum()), "removed": len(drop),
                                           "csv_sha256": sha256(d / f"{part}.csv")}
        print(arm, {p: v["rows"] for p, v in manifest["arms"][arm].items()}, flush=True)
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
