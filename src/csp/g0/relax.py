"""Relax and rank CSP candidates with ORB-v3, following the paper's export protocol (arXiv:2609.26502 v2,
"Relaxation, ranking and energy evaluation"): relax every candidate with ORB-v3 (500 steps, force threshold
0.01 eV/A), rank by ORB-v3 energy per atom (ascending), export the 20 best as rank01..rank20.

Not stated by the paper, so chosen here and recorded in the output:
- ORB-v3 model: orb_v3_conservative_inf_omat. On the paper's released ABC2D6-arm candidates it gives the
  smallest residual forces and the energy order closest to the released rank order of the eight periodic ORB-v3
  models (src/csp/g0/orb_variant_check.py). This is an inference, not a confirmation.
- Optimiser: ASE FIRE on a FrechetCellFilter (positions and cell relaxed together), 500 steps, fmax 0.01 eV/A.
- Precision float32-highest, CPU.
A candidate whose relaxation raises an exception keeps its unrelaxed structure and is flagged; none is dropped.

Usage: python -I relax.py <raw_dir> <out_dir> [material_id ...]
  raw_dir/<mid>/equicsp_*.cif  ->  out_dir/<mid>/rank01_<candidate>.cif ... and out_dir/<mid>/relax_report.json
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from ase.filters import FrechetCellFilter
from ase.io import read, write
from ase.optimize import FIRE
from orb_models.forcefield import pretrained
from orb_models.forcefield.calculator import ORBCalculator

MODEL, FMAX, STEPS, DEVICE = "orb_v3_conservative_inf_omat", 0.01, 500, "cpu"
nat = lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.name)]


def main(raw_dir, out_dir, mids=None):
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    calc = ORBCalculator(getattr(pretrained, MODEL)(device=DEVICE, precision="float32-highest"), device=DEVICE)
    for d in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        if mids and d.name not in mids:
            continue
        rows, relaxed = [], {}
        for p in sorted(d.glob("*.cif"), key=nat):
            a = read(p)
            n_atoms = len(a)
            a.calc = calc
            t0, err, steps = time.time(), None, None
            try:
                opt = FIRE(FrechetCellFilter(a), logfile=None)
                opt.run(fmax=FMAX, steps=STEPS)
                steps = opt.get_number_of_steps()
            except Exception as e:  # keep the candidate, flag it
                err = repr(e)
                a = read(p)
                a.calc = calc
            e_pa = float(a.get_potential_energy() / n_atoms)
            fmax = float(np.linalg.norm(a.get_forces(), axis=1).max())
            relaxed[p.stem] = a
            rows.append({"candidate": p.stem, "energy_per_atom_eV": e_pa, "max_force_eV_per_A": round(fmax, 5),
                         "steps": steps, "converged": err is None and fmax <= FMAX, "error": err,
                         "seconds": round(time.time() - t0, 1)})
        rows.sort(key=lambda r: r["energy_per_atom_eV"])
        o = out_dir / d.name
        o.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(rows[:20], 1):
            r["rank"] = i
            write(o / f"rank{i:02d}_{r['candidate']}.cif", relaxed[r["candidate"]], format="cif")
        (o / "relax_report.json").write_text(json.dumps({"model": MODEL, "fmax": FMAX, "max_steps": STEPS,
                                                         "optimizer": "ASE FIRE + FrechetCellFilter", "device": DEVICE,
                                                         "candidates": rows}, indent=1))
        print(d.name, f"{sum(r['converged'] for r in rows)}/{len(rows)} converged,",
              f"{sum(r['seconds'] for r in rows):.0f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or None)
