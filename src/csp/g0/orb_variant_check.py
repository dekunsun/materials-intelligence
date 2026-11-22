"""Which ORB-v3 model did the paper relax and rank with? The paper says only "ORB-v3". Its exported
candidates are the relaxed structures in ascending ORB-v3 energy per atom (MANIFEST rank_basis), so under the
model it used (a) residual forces should be near the 0.01 eV/A threshold and (b) energy per atom should rise
with rank. This evaluates each periodic ORB-v3 model on released candidates and reports both.
Usage: python -I orb_variant_check.py <released group dir> <out.json> [mid ...]"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from ase.io import read
from orb_models.forcefield import pretrained
from orb_models.forcefield.calculator import ORBCalculator

VARIANTS = ["orb_v3_conservative_inf_omat", "orb_v3_conservative_20_omat", "orb_v3_direct_inf_omat", "orb_v3_direct_20_omat",
            "orb_v3_conservative_inf_mpa", "orb_v3_conservative_20_mpa", "orb_v3_direct_inf_mpa", "orb_v3_direct_20_mpa"]
nat = lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.name)]


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


root, out, mids = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
res = {}
for v in VARIANTS:
    calc = ORBCalculator(getattr(pretrained, v)(device="cpu", precision="float32-highest"), device="cpu")
    per = {}
    for mid in mids:
        e, f = [], []
        for p in sorted((root / mid).glob("*.cif"), key=nat):
            a = read(p)
            a.calc = calc
            e.append(a.get_potential_energy() / len(a))
            f.append(float(np.abs(a.get_forces()).max()))
        per[mid] = {"spearman_energy_vs_rank": round(spearman(np.arange(len(e)), e), 3),
                    "n_rank_inversions": int(sum(e[i + 1] < e[i] - 1e-6 for i in range(len(e) - 1))),
                    "median_max_force": round(float(np.median(f)), 4), "max_max_force": round(max(f), 4)}
    res[v] = per
    print(v, json.dumps(per), flush=True)
json.dump(res, open(out, "w"), indent=1)
