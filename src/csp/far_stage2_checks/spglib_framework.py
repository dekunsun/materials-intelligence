"""spglib-based framework key, validated against MP's protostructure_spglib labels (both canonicalised)."""
import sys, random
import numpy as np, pandas as pd, spglib
from pathlib import Path
from pymatgen.core import Structure
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT / "src"))
from csp.far_split import framework
from csp.far_posthoc_canonical import canonical

def family(n):
    return "a" if n <= 2 else "m" if n <= 15 else "o" if n <= 74 else "t" if n <= 142 else "h" if n <= 194 else "c"

def spglib_framework(struct: Structure, symprec=0.1):
    cell = (struct.lattice.matrix, struct.frac_coords, [s.Z for s in struct.species])
    ds = spglib.get_symmetry_dataset(cell, symprec=symprec)
    if ds is None: return None
    n = ds.number; cen = ds.international[0]
    cen = "C" if cen in "AB" else cen
    pearson = f"{family(n)}{cen}{len(ds.std_types)}"
    eq = np.asarray(ds.equivalent_atoms)
    letters = "".join(sorted(ds.wyckoffs[i] for i in np.unique(eq)))
    return canonical(f"{pearson}_{n}_{letters}")

if __name__ == "__main__":
    R = ROOT / "data/raw/discovery/6d587c184cdb4a4865dc0b15b04a5e6d77ed464f"
    cse = pd.read_json(R / "mp_computed_structure_entries_2023-02-07.json.gz").set_index("material_id")
    me = pd.read_csv(R / "mp_energies.csv.gz").set_index("material_id")
    ids = [i for i in cse.index if i in me.index and isinstance(me.at[i, "protostructure_spglib"], str)]
    random.seed(1); ids = random.sample(ids, 3000)
    agree = 0; bad = []
    for i in ids:
        mine = spglib_framework(Structure.from_dict(cse.at[i, "entry"]["structure"]))
        ref = canonical(framework(me.at[i, "protostructure_spglib"]))
        agree += mine == ref
        if mine != ref and len(bad) < 8: bad.append((i, ref, mine))
    print(f"agreement {agree}/3000 = {agree/3000:.3f}")
    for b in bad: print(" ", b)
