"""Are Alexandria's raw PBE energies on the same footing as MP's? Match entries with the same reduced formula,
space group and number of sites, and compare uncorrected energy per atom (Alexandria shard 0 vs MP 2023 snapshot)."""
import bz2, json, sys
import numpy as np, pandas as pd
from pymatgen.core import Composition
from pymatgen.symmetry.groups import SpaceGroup
R = "data/raw/discovery/6d587c184cdb4a4865dc0b15b04a5e6d77ed464f/"
cse = pd.read_json(R + "mp_computed_structure_entries_2023-02-07.json.gz")
print("CSE columns", list(cse.columns)[:6], len(cse))
col = [c for c in cse.columns if "entry" in c][0]
def unc(e):
    n = sum(e["composition"].values()); return (e["energy"]) / n, e.get("correction", 0) / n, e.get("parameters", {}).get("run_type")
cse[["e_unc", "corr_pa", "run_type"]] = cse[col].apply(lambda e: pd.Series(unc(e)))
me = pd.read_csv(R + "mp_energies.csv.gz").set_index("material_id")
cse = cse.set_index("material_id").join(me[["formula", "spacegroup_symbol", "n_sites"]], how="inner")
def sgnum(s):
    try: return SpaceGroup(s).int_number
    except Exception: return None
cse = cse.dropna(subset=["formula", "spacegroup_symbol"]); cse["spg"] = cse.spacegroup_symbol.map(sgnum)
cse["rf"] = cse.formula.map(lambda f: Composition(f).reduced_formula)
mpkey = cse.dropna(subset=["spg"]).groupby(["rf", "spg", "n_sites"]).agg(e_mp=("e_unc", "min"), run_type=("run_type", "first"))
ents = json.load(bz2.open("data/raw/alexandria/alexandria_00000.json.bz2"))["entries"]
rows = [(Composition(e["composition"]).reduced_formula, e["data"]["spg"], float(e["data"]["nsites"]), e["data"]["energy_total"] / e["data"]["nsites"], e["data"]["location"].split("/")[0]) for e in ents]
al = pd.DataFrame(rows, columns=["rf", "spg", "n_sites", "e_alex", "source"]).groupby(["rf", "spg", "n_sites"]).agg(e_alex=("e_alex", "min"), source=("source", "first"))
j = al.join(mpkey, how="inner")
j["diff_meV"] = (j.e_alex - j.e_mp) * 1000
print("matched (formula, space group, n_sites):", len(j))
for rt, g in j.groupby("run_type"):
    d = g.diff_meV; print(f"  {rt:8s} n={len(g):5d} median {d.median():8.2f} meV/atom | |diff|<5: {np.mean(d.abs()<5):.2f} | |diff|<20: {np.mean(d.abs()<20):.2f}")
print(j.sort_values("diff_meV").head(3).to_string()); print(j.sort_values("diff_meV").tail(3).to_string())
