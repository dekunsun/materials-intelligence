"""Initial-structure pilot: put Alexandria DFT energies on Wrenformer's formation-energy scale, and check it.

Design: modules/csp/INITIAL_STRUCTURE_PILOT.md, Section 4. Wrenformer was trained on MP formation energies (MP2020
corrections, MP elemental references). For an Alexandria entry:
  e_form = (E_raw + MP2020 correction - sum_i n_i mu_i) / N
where E_raw is Alexandria's uncorrected total energy (data.energy_total), the correction comes from pymatgen's
MaterialsProject2020Compatibility for a plain GGA calculation (GGA+U systems are not in the sample; POTCAR check off,
since Alexandria entries carry no POTCAR record), and mu_i is the energy per atom of the lowest-energy MP 2023 GGA
entry of element i.

Check (stop rule of Section 4): on validation entries (Alexandria entries outside the pilot whose reduced formula,
space group and number of sites match exactly one MP 2023 GGA entry), the median |e_form(Alexandria) - e_form(MP)|
must be below 10 meV/atom. MP's own e_form is recomputed with the same references, and must reproduce MP's
published formation_energy_per_atom (a check on the references).

Usage (repository root):  .venv/bin/python -I src/csp/init_pilot_eform.py results/<run>
Writes <run>/eform_validation.json.
"""
from __future__ import annotations

import gzip
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.fetch_discovery import OUT as RAW  # noqa: E402
from csp.init_pilot_collect import OUT  # noqa: E402
from csp.run_screening import mp2023_ids  # noqa: E402

THRESHOLD = 0.010  # eV/atom


def mp_table() -> pd.DataFrame:
    mp = pd.read_csv(RAW / "mp_energies.csv.gz", keep_default_na=False, na_values=[""])
    return mp[mp.material_id.isin(mp2023_ids()) & (mp.energy_type == "GGA") & mp.n_sites.notna()]


def elemental_refs(mp: pd.DataFrame) -> dict:
    from pymatgen.core import Composition
    one = mp[mp.formula.map(lambda f: len(Composition(f).elements) == 1)]
    one = one.assign(el=one.formula.map(lambda f: Composition(f).elements[0].symbol))
    return one.groupby("el").energy_per_atom.min().to_dict()


def eform_alexandria(entry: dict, refs: dict) -> float:
    from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
    from pymatgen.entries.computed_entries import ComputedStructureEntry
    from pymatgen.core import Structure
    e = ComputedStructureEntry(Structure.from_dict(entry["structure"]), entry["data"]["energy_total"],
                               parameters={"run_type": "GGA", "is_hubbard": False, "hubbards": {}})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        e = MaterialsProject2020Compatibility(check_potcar=False).process_entry(e)
    if e is None:
        return float("nan")
    comp = e.composition
    return (e.energy - sum(n * refs[el.symbol] for el, n in comp.items())) / comp.num_atoms


def main(run: str) -> int:
    from pymatgen.core import Composition
    run = Path(run)
    mp = mp_table()
    refs = elemental_refs(mp)
    mp["red"] = mp.formula.map(lambda f: Composition(f).reduced_formula)
    mp["spg"] = mp.protostructure_spglib.str.split("_").str[2].astype(int)
    mp["e_form_recomputed"] = [
        e - sum(n * refs[el.symbol] for el, n in Composition(f).items()) / Composition(f).num_atoms
        for f, e in zip(mp.formula, mp.energy_per_atom)]
    ref_check = float((mp.e_form_recomputed - mp.formation_energy_per_atom).abs().median())
    key = mp.groupby(["red", "spg", "n_sites"])
    unique = key.filter(lambda g: len(g) == 1).set_index(["red", "spg", "n_sites"])
    val = json.load(gzip.open(OUT / "entries.json.gz", "rt"))["validation"]
    rows = []
    for i, e in val.items():
        k = (Composition(e["composition"]).reduced_formula, int(e["data"]["spg"]), int(e["data"]["nsites"]))
        if k not in unique.index:
            continue
        m = unique.loc[k]
        rows.append({"mat_id": i, "mp_id": m.material_id, "e_form_alex": eform_alexandria(e, refs),
                     "e_form_mp": m.e_form_recomputed, "n_elements": len(Composition(e["composition"]).elements)})
    df = pd.DataFrame(rows)
    df["diff"] = df.e_form_alex - df.e_form_mp
    med = float(df["diff"].abs().median())
    res = {"what": "Alexandria e_form on MP2020 / MP-reference scale vs MP 2023 (src/csp/init_pilot_eform.py)",
           "reference_check_median_abs_ev": ref_check, "n_matched": int(len(df)),
           "n_correction_failed": int(df.e_form_alex.isna().sum()),
           "median_abs_diff_ev": med, "median_diff_ev": float(df["diff"].median()),
           "share_abs_diff_below_10mev": float((df["diff"].abs() < 0.01).mean()),
           "quantiles_abs_diff_ev": {str(q): float(df["diff"].abs().quantile(q)) for q in [0.25, 0.5, 0.75, 0.9, 0.95]},
           "threshold_ev": THRESHOLD, "passes": med < THRESHOLD}
    run.mkdir(parents=True, exist_ok=True)
    (run / "eform_validation.json").write_text(json.dumps(res, indent=1))
    df.to_csv(run / "eform_validation.csv", index=False)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
