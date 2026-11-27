"""Initial-structure pilot: relax the rebuilt initial structures with MatRIS-10M-MP (CPU).

Design: modules/csp/INITIAL_STRUCTURE_PILOT.md, Sections 3-4. Same model, settings and failure rule as Stage 2
(src/csp/far_stage2_relax.py: FIRE with FrechetCellFilter, fmax 0.05 eV/A, at most 500 steps); only the starting
structure differs. Every assignment of an entry is relaxed; the entry's prediction is later the lowest final energy
per atom among its assignments (src/csp/init_pilot_decide.py), which uses no DFT result.

Entries are processed in a fixed shuffled order (seed 11, all assignments of an entry together), so the first N
entries give an unbiased timing sample, and output is appended row by row, so an interrupted run resumes.

Usage (repository root):
    data/raw/mlip_venv/bin/python -I src/csp/init_pilot_relax.py results/<run> [--limit-entries N] [--threads T]
        [--worker I --n-workers K]
With K workers, entries are split by balance(): in the shuffled order, each entry goes to the worker with the least
expected work so far (sites^1.6 summed over its assignments, from the timing run; no DFT result). This is operational
only: each structure is relaxed the same way. Worker I writes its own file, MatRIS-10M-MP_initial.wI.csv; the scoring
scripts read all of them.
Writes results/<run>/predictions/MatRIS-10M-MP_initial.csv:
    mat_id, assignment, nsites, e_model (eV, total), n_steps, converged, failed, seconds
and the relaxed structures, for the descriptive comparison with the DFT structures, to
data/raw/alexandria/pilot/final_structures_<run name>.jsonl (one line per relaxation; not committed).
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
sys.path.insert(0, str(ROOT / "src/csp"))
from far_stage2_relax import FMAX, MAX_STEPS, SEED, calculator  # noqa: E402

STRUCTURES = ROOT / "data/raw/alexandria/pilot/initial_structures.json.gz"
MODEL = "MatRIS-10M-MP"


def relax(atoms, calc, tag: str):
    """As far_stage2_relax.relax (same optimiser, filter, fmax and step cap), plus a progress line every 25 steps."""
    from ase.filters import FrechetCellFilter
    from ase.optimize import FIRE
    atoms.calc = calc
    opt = FIRE(FrechetCellFilter(atoms), logfile=None)
    t0 = time.perf_counter()

    def progress():
        n = opt.get_number_of_steps()
        if n and n % 25 == 0:
            print("  step", tag, n, round(time.perf_counter() - t0, 1), flush=True)
    opt.attach(progress, interval=1)
    converged = bool(opt.run(fmax=FMAX, steps=MAX_STEPS))
    return float(atoms.get_potential_energy()), int(opt.get_number_of_steps()), converged


def order(ids: list[str]) -> list[str]:
    ids = sorted(ids)
    return [ids[i] for i in np.random.default_rng(SEED).permutation(len(ids))]


def cost(rec: dict) -> float:
    """Expected relaxation work of an entry: sites^1.6 per assignment (timing run: seconds ~ sites^1.6)."""
    return sum(len(a["structure"]["sites"]) ** 1.6 for a in rec["assignments"])


def balance(ids: list[str], recs: dict, k: int) -> list[list[str]]:
    """Split ids (kept in order) over k workers, each entry to the worker with the least expected work so far."""
    parts, load = [[] for _ in range(k)], [0.0] * k
    for i in ids:
        j = load.index(min(load))
        parts[j].append(i)
        load[j] += cost(recs[i])
    return parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--limit-entries", type=int)
    ap.add_argument("--threads", type=int)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--n-workers", type=int, default=1)
    args = ap.parse_args()
    import torch
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    if args.threads:
        torch.set_num_threads(args.threads)
    warnings.filterwarnings("ignore")
    recs = json.load(gzip.open(STRUCTURES, "rt"))
    ids = order(list(recs))
    if args.limit_entries:
        ids = ids[: args.limit_entries]
    ids = balance(ids, recs, args.n_workers)[args.worker]
    suffix = f".w{args.worker}" if args.n_workers > 1 else ""
    jobs = [(i, k) for i in ids for k in range(len(recs[i]["assignments"]))]
    out = Path(args.run) / "predictions" / f"{MODEL}_initial{suffix}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with out.open() as f:
            done = {(r["mat_id"], int(r["assignment"])) for r in csv.DictReader(f)}
    calc = calculator(MODEL)
    new = not out.exists()
    finals = ROOT / "data/raw/alexandria/pilot" / f"final_structures_{Path(args.run).resolve().name}{suffix}.jsonl"
    with out.open("a", newline="") as f, finals.open("a") as g:
        w = csv.writer(f)
        if new:
            w.writerow(["mat_id", "assignment", "nsites", "e_model", "n_steps", "converged", "failed", "seconds"])
        for n, (mid, k) in enumerate(j for j in jobs if j not in done):
            t0 = time.perf_counter()
            s = Structure.from_dict(recs[mid]["assignments"][k]["structure"])
            atoms = AseAtomsAdaptor.get_atoms(s)
            try:
                e, steps, conv = relax(atoms, calc, f"{mid}/{k}")
                failed = not np.isfinite(e)
                if not failed:
                    g.write(json.dumps({"mat_id": mid, "assignment": k,
                                        "structure": AseAtomsAdaptor.get_structure(atoms).as_dict()}) + "\n")
                    g.flush()
            except Exception as exc:  # noqa: BLE001 - any model error is a failed relaxation
                e, steps, conv, failed = float("nan"), 0, False, True
                print("failed", mid, k, type(exc).__name__, exc, file=sys.stderr, flush=True)
            w.writerow([mid, k, len(s), e, steps, conv, failed, round(time.perf_counter() - t0, 3)])
            f.flush()
            print(MODEL, n, mid, k, len(s), steps, round(time.perf_counter() - t0, 1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
