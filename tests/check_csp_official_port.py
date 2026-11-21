"""Independent check written by a reviewing agent on 2026-11-21 and kept as a test.

Loads the official discovery metric functions (matbench_discovery/metrics/discovery.py
at the pinned commit) with small stubs instead of the full package, and compares, for
every model, the predicted hull distance of every structure with src/csp/discovery_metrics.py.
Expect: "models whose hull distances differ: []". Four older models (BOWSR, MEGNet, Voronoi RF,
Wrenformer) list ~520 ids not in WBM; both pipelines drop them on reindexing, so they are reported
separately as information, not as failures.

Usage: .venv/bin/python tests/check_csp_official_port.py
"""
import sys, json, pathlib, importlib.util, types
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from csp.discovery_metrics import prepare, pred_hull
SRC = ROOT/"data/raw/mbd_src/matbench-discovery"
# load the official functions without importing package (avoid heavy deps): exec source with stubs
src = (SRC/"matbench_discovery/metrics/discovery.py").read_text()
mod = types.ModuleType("offdisc")
fake_pkg = types.ModuleType("matbench_discovery"); fake_pkg.STABILITY_THRESHOLD = 0
fake_data = types.ModuleType("matbench_discovery.data"); fake_data.MAX_E_FORM_ERROR_THRESHOLD = 5.0
class MbdKey:
    each_true="e_above_hull_mp2020_corrected_ppd_mp"; e_form_dft="e_form_per_atom_mp2020_corrected"; uniq_proto="unique_prototype"; missing_preds="missing_preds"
fake_enums = types.ModuleType("matbench_discovery.enums"); fake_enums.MbdKey=MbdKey; fake_enums.Model=object
class TestSubset: full_test_set="full_test_set"; uniq_protos="unique_prototypes"
fake_enums.TestSubset=TestSubset
sys.modules.update({"matbench_discovery":fake_pkg,"matbench_discovery.data":fake_data,"matbench_discovery.enums":fake_enums})
exec(compile(src, "offdisc", "exec"), mod.__dict__)
D = ROOT/"data/raw/discovery/6d587c184cdb4a4865dc0b15b04a5e6d77ed464f"
man = json.loads((D/"MANIFEST.json").read_text())
wbm = pd.read_csv(D/"wbm_summary.csv.gz").set_index("material_id")
print("wbm rows", len(wbm), "dup ids", wbm.index.duplicated().sum(), "uniq", wbm.unique_prototype.astype(bool).sum(),
      "each_true NaN", wbm[MbdKey.each_true].isna().sum(), "e_form NaN", wbm[MbdKey.e_form_dft].isna().sum())
uniq = wbm.unique_prototype.astype(bool)
prev = float((wbm.loc[uniq, MbdKey.each_true] <= 0).mean())
print("prevalence unrounded", prev, "rounded", float((wbm.loc[uniq, MbdKey.each_true].round(3) <= 0).mean()))
issues = []
for m in man["models"]:
    df = pd.read_csv(D/m["file"])
    dup = df.material_id.duplicated().sum(); unk = (~df.material_id.isin(wbm.index)).sum()
    nonnum = pd.to_numeric(df.e_form_per_atom, errors="coerce").isna().sum() - df.e_form_per_atom.isna().sum()
    s = df.set_index("material_id")["e_form_per_atom"]
    ref, p = prepare(wbm, s); ours = pred_hull(ref, p)
    try:
        mref, mp = mod.prepare_model_predictions(wbm, s)
        off = mod.pred_hull_dist(mp, mref[MbdKey.each_true], mref[MbdKey.e_form_dft])
        same = np.array_equal(ours.to_numpy(), off.to_numpy(), equal_nan=True)
        met = mod.calc_discovery_metrics(mref, mp, uniq_proto_prevalence=prev)
    except Exception as e:
        same = f"official raised {e!r}"[:120]
    if dup or unk or nonnum or same is not True:
        issues.append((m["model"], int(dup), int(unk), int(nonnum), same))
print("models whose hull distances differ:", [i for i in issues if i[4] is not True])
print("informational (extra ids / duplicates / non-numeric, hull distances identical):", [i[:4] for i in issues if i[4] is True])
