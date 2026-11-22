"""Score CSP candidates against T180 references with the paper's ablation rule (benchmark_deep_csp
scripts/ablation_t180_scores.py at commit 631c765): StructureMatcher(ltol 0.2, stol 0.3, angle_tol 5,
primitive_cell, scale, no supercell) against the reference's primitive cell (tolerance 0.01).
fit = some candidate among the first 20 matches; consensus = some candidate matches AND has the
reference's space group (spglib via pymatgen, symprec 0.1); rank = position of the first match.

Usage: python -I score.py <cands_root> <ref_cif_dir> <out.csv>
  cands_root/<material_id>/*.cif, read in natural-sort order (rank01..rank20 or candidate_0001..).
"""
import re
import sys
import warnings
from pathlib import Path

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

warnings.filterwarnings("ignore")
TARGETS = ["mp-6231", "mp-19093", "mp-19274", "mp-6389", "mp-16307", "mp-557387", "mp-6603", "mp-1215245",
           "mp-10321", "mp-12449", "mp-556434"]  # the 11 ABC2D6 targets of T180 (ablation_family_targets.json)
M = StructureMatcher(ltol=.2, stol=.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=False)


def nat(p):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.name)]


def sg(s, sp=0.1):
    try:
        return SpacegroupAnalyzer(s, symprec=sp).get_space_group_number()
    except Exception:
        return None


def score(files, gt, gsg):
    fit = cons = False
    rank = None
    n_read = 0
    for i, p in enumerate(files[:20], 1):
        try:
            s = Structure.from_file(p)
        except Exception:
            continue
        n_read += 1
        if M.fit(gt, s):
            if not fit:
                fit, rank = True, i
            if sg(s) == gsg:
                cons = True
    return fit, cons, rank, n_read


def main(root, refdir, out):
    rows = []
    for mid in TARGETS:
        gt = Structure.from_file(Path(refdir) / f"{mid}.cif").get_primitive_structure(tolerance=0.01)
        files = sorted((Path(root) / mid).glob("*.cif"), key=nat)
        fit, cons, rank, n_read = score(files, gt, sg(gt))
        rows.append(dict(material_id=mid, n_files=len(files), n_read=n_read, fit=fit, consensus=cons, first_match_rank=rank,
                         ref_spacegroup=sg(gt)))
        print(rows[-1], flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(out, index=False)
    print(f"fit {int(d.fit.sum())} / 11, consensus {int(d.consensus.sum())} / 11")


if __name__ == "__main__":
    main(*sys.argv[1:4])
