"""Feasibility for Stage 2 (counts only, no model): cells of Alexandria shard 0 against the MP 2023 snapshot."""
import bz2, json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(Path(__file__).resolve().parent))
from pymatgen.core import Structure, Composition
from csp.far_split import framework
from csp.far_posthoc_canonical import canonical
from csp.run_screening import RAW, chemsys, mp2023_ids
from spglib_framework import spglib_framework
mp = pd.read_csv(RAW / "mp_energies.csv.gz"); mp = mp[mp.material_id.isin(mp2023_ids())]
mp_sys = set(mp.formula.dropna().map(chemsys)); mp_fw = set(mp.protostructure_spglib.dropna().map(framework).map(canonical))
wbm = pd.read_csv(RAW / "wbm_summary.csv.gz")
wbm_keys = set(zip(wbm.formula.map(lambda f: Composition(f).reduced_formula), wbm.protostructure_spglib.str.split("_").str[2].astype(int), wbm.n_sites))
U = {"Co","Cr","Fe","Mn","Mo","Ni","V","W"}
rows = []
for e in json.load(bz2.open(ROOT / "data/raw/alexandria/alexandria_00000.json.bz2"))["entries"]:
    d = e["data"]; s = Structure.from_dict(e["structure"]); el = set(d["elements"])
    fw = spglib_framework(s)
    rows.append({"source": d["location"].split("/")[0], "year": d["run_timestamp"]["string"][:4] if d.get("run_timestamp") else None,
                 "chem_familiar": "-".join(sorted(el)) in mp_sys, "framework_known": fw in mp_fw, "framework": fw,
                 "plus_u": bool(el & U) and bool(el & {"O", "F"}), "n_elements": len(el), "nsites": d["nsites"],
                 "in_wbm": (Composition(e["composition"]).reduced_formula, d["spg"], float(d["nsites"])) in wbm_keys,
                 "stable": d["e_above_hull"] <= 0, "e_hull": d["e_above_hull"]})
df = pd.DataFrame(rows); df.to_csv(str(ROOT / "data/raw/alexandria/shard0_cells.csv.gz"), index=False)
df["cell"] = df.chem_familiar.map({True: "chemF", False: "chemU"}) + "/" + df.framework_known.map({True: "fwK", False: "fwU"})
print("in WBM (formula+spg+nsites):", int(df.in_wbm.sum()), "| +U:", int(df.plus_u.sum()), "| framework None:", int(df.framework.isna().sum()))
k = df[~df.in_wbm & ~df.plus_u]
print("\nexcluding WBM matches and +U systems:", len(k))
print(k.groupby("cell").agg(n=("stable", "size"), stable=("stable", "sum"), frameworks=("framework", "nunique"),
      fw_with_stable=("framework", lambda x: x[k.loc[x.index, "stable"]].nunique()), share_ehull_le_0_1=("e_hull", lambda x: (x <= 0.1).mean())).round(3).to_string())
print("\nstructural cell (chemF/fwU) by source:")
s = k[k.cell == "chemF/fwU"]; print(s.groupby("source").agg(n=("stable", "size"), stable=("stable", "sum")).sort_values("n", ascending=False).to_string())
