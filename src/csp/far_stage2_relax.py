"""Stage 2 of the far-from-training test: relax the sampled Alexandria structures with one model (CPU).

Runs in the separate model environment data/raw/mlip_venv (chgnet, mace-torch, sevenn, matris). Settings follow
Matbench Discovery's for these four models: FIRE with FrechetCellFilter, force tolerance 0.05 eV/A, at most 500
steps, starting here from the DFT-relaxed structure. Checkpoints:
  CHGNet         chgnet 0.3.0 weights            (CHGNet.load(model_name="0.3.0"))
  MACE-MP-0      2023-12-03-mace-128-L1_epoch-199 (mace_mp(model="medium")), float64 as in Matbench Discovery
  SevenNet-0     SevenNet_0__11Jul2024           (SevenNetCalculator("7net-0"))
  MatRIS-10M-MP  MatRIS_10M_MP.pth.tar           (MatRISCalculator(model="matris_10m_mp"))
A relaxation that raises an error or ends with a non-finite energy is recorded as failed. Not converging within 500
steps is not a failure (the final energy is kept), as in Matbench Discovery; it is recorded in `converged`.

Structures are processed in a fixed shuffled order (seed 11), so the first N give an unbiased timing sample, and the
output is appended row by row, so an interrupted run resumes where it stopped.

Usage (repository root):
    data/raw/mlip_venv/bin/python -I src/csp/far_stage2_relax.py results/<run> <model> [--limit N] [--threads T]
Writes results/<run>/predictions/<model>.csv: mat_id, e_model (eV, total), n_steps, converged, failed, seconds.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STRUCTURES = ROOT / "data/raw/alexandria/sample_structures.json.gz"
MODELS = ["CHGNet", "MACE-MP-0", "SevenNet-0", "MatRIS-10M-MP"]
FMAX, MAX_STEPS, SEED = 0.05, 500, 11


def calculator(model: str):
    import os
    import certifi
    # The python.org interpreter has no system CA bundle; verify weight downloads against certifi's bundle instead.
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    if model == "CHGNet":
        from chgnet.model import CHGNet
        from chgnet.model.dynamics import CHGNetCalculator
        return CHGNetCalculator(model=CHGNet.load(model_name="0.3.0"), use_device="cpu")
    if model == "MACE-MP-0":
        from mace.calculators import mace_mp
        return mace_mp(model="medium", default_dtype="float64", device="cpu")
    if model == "SevenNet-0":
        # e3nn 0.4.4 (pinned by mace-torch) loads its own constants file, shipped inside the installed package, with
        # torch.load's old default; torch >= 2.6 refuses that by default. Allow it in this process only. Files loaded
        # this way come from the installed packages, the same source as the code that runs.
        os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
        from sevenn.calculator import SevenNetCalculator
        return SevenNetCalculator("7net-0", device="cpu")
    if model == "MatRIS-10M-MP":
        from matris.applications.base import MatRISCalculator
        return MatRISCalculator(model="matris_10m_mp", task="efs", device="cpu")
    raise ValueError(model)


def relax(atoms, calc):
    from ase.filters import FrechetCellFilter
    from ase.optimize import FIRE
    atoms.calc = calc
    opt = FIRE(FrechetCellFilter(atoms), logfile=None)
    converged = bool(opt.run(fmax=FMAX, steps=MAX_STEPS))
    return float(atoms.get_potential_energy()), int(opt.get_number_of_steps()), converged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("model", choices=MODELS)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--threads", type=int)
    ap.add_argument("--structures", default=str(STRUCTURES), help="for timing tests only")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="mat_ids to leave for a separate run (operational only: e.g. one that ran out of memory)")
    args = ap.parse_args()
    import torch
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    if args.threads:
        torch.set_num_threads(args.threads)
    warnings.filterwarnings("ignore")
    recs = json.load(gzip.open(args.structures, "rt"))
    ids = sorted(recs)
    ids = [ids[i] for i in np.random.default_rng(SEED).permutation(len(ids))]
    if args.limit:
        ids = ids[:args.limit]
    ids = [i for i in ids if i not in set(args.exclude)]
    out = Path(args.run) / "predictions" / f"{args.model}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with out.open() as f:
            done = {r["mat_id"] for r in csv.DictReader(f)}
    calc = calculator(args.model)
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["mat_id", "e_model", "n_steps", "converged", "failed", "seconds"])
        for k, mid in enumerate(i for i in ids if i not in done):
            t0 = time.perf_counter()
            try:
                atoms = AseAtomsAdaptor.get_atoms(Structure.from_dict(recs[mid]["structure"]))
                e, n, conv = relax(atoms, calc)
                failed = not np.isfinite(e)
            except Exception as exc:  # noqa: BLE001 - any model error is a failed relaxation
                e, n, conv, failed = float("nan"), 0, False, True
                print("failed", mid, type(exc).__name__, exc, file=sys.stderr, flush=True)
            w.writerow([mid, e, n, conv, failed, round(time.perf_counter() - t0, 3)])
            f.flush()
            if k % 50 == 0:
                print(args.model, k, mid, round(time.perf_counter() - t0, 2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
