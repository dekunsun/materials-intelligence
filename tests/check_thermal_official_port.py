"""Independent check written by a reviewing agent on 2026-11-21 and kept as a test.

Ports the official per-material logic (phonons.py, schema.py at commit 6d587c1; the official code
needs Python 3.14 syntax, so it cannot be imported here) and compares it row by row with a run's
per_material.csv. Expect: max d_srd 0, max d_srme 0, 0 censor flag disagreements.

Usage: .venv/bin/python tests/check_thermal_official_port.py data/raw/kappa/<commit> results/<thermal_run_id>
"""

import json, sys
import numpy as np, pandas as pd

RAW = sys.argv[1]; RUN = sys.argv[2]
KMAX = 2.0
VOIGT = np.array(((0, 5, 4), (5, 1, 3), (4, 3, 2)))

def miss(v):
    m = pd.isna(v); return isinstance(m, (bool, np.bool_)) and bool(m)
def is_set(v): return not miss(v) and bool(v)
def v6(t):
    try: a = np.asarray(t, dtype=float)
    except (TypeError, ValueError): return t
    if a.ndim == 0 or a.shape[-1] != 6: return t
    return a[..., VOIGT]
def normalize(df):
    rows = []
    for r in df.to_dict(orient="records"):
        for k in ("kappa_tot_rta", "kappa_p_rta", "kappa_c", "mode_kappa_tot_rta"):
            if k in r: r[k] = v6(r[k])
        r.setdefault("errors", [])
        if is_set(r["errors"]) or is_set(r.get("conductivity_skipped")):
            r["kappa_tot_rta"] = np.nan; r["mode_kappa_tot_rta"] = np.nan; r["mode_weights"] = np.nan
        rows.append(r)
    return pd.DataFrame(rows, index=df.index).set_index("material_id")
def fin(v, nonneg=False):
    try: a = np.asarray(v, dtype=float)
    except (TypeError, ValueError): return None
    if a.size == 0 or np.any(~np.isfinite(a)): return None
    if nonneg and np.any(a < 0): return None
    return a
def single(v):
    a = fin(v, True)
    return None if a is None or a.size != 1 else float(a.ravel()[0])
def kavg(k):
    try:
        a = np.asarray(k, dtype=float)
        if a.ndim == 0: raise ValueError
        if a.shape[-2:] == (3, 3): return np.trace(a, axis1=-2, axis2=-1) / 3
        if a.shape[-1] == 6: return a[..., :3].mean(-1)
        if a.shape[-1:] == (3,): return a.mean(-1)
        raise ValueError
    except (ValueError, TypeError):
        return np.array([np.nan])
def modek(row):
    for key in ("mode_kappa_tot_avg", "mode_kappa_tot_rta"):
        if key not in row.index: continue
        mk = row[key]
        if key == "mode_kappa_tot_rta": mk = kavg(mk)
        if (v := fin(mk)) is not None: return v
    return None
def srme1(p, t):
    tt = np.atleast_1d(fin(t["kappa_tot_avg"], True)); fail = np.full(tt.shape, np.nan)
    tm = modek(t); pmk = modek(p)
    if pmk is None: return fail
    pt = fin(p.get("kappa_tot_avg"), True); w = fin(p.get("mode_weights"), True)
    if pt is None or np.atleast_1d(pt).shape != tt.shape or w is None or w.sum() <= 0 or pmk.shape != tm.shape: return fail
    pt = np.atleast_1d(pt)
    me = np.atleast_1d(np.abs(pmk - tm).sum(axis=tuple(range(1, pmk.ndim))) / w.sum())
    if me.shape != tt.shape: return fail
    den = pt + tt
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(den == 0, np.where(me == 0, 0, KMAX), KMAX * me / den)
    ok = np.isfinite(s) & (s >= 0) & (s <= KMAX)
    return np.where(ok, s, np.nan)

ref = normalize(pd.read_json(f"{RAW}/reference_phononDB_PBE_noNAC.json.gz"))
man = json.load(open(f"{RAW}/MANIFEST.json"))
pm = pd.read_csv(f"{RUN}/per_material.csv").set_index(["model", "material_id"])
worst = []
for m in man["models"]:
    p = normalize(pd.read_json(f"{RAW}/{m['file']}"))
    missing = set(ref.index) - set(p.index)
    p = p.reindex(ref.index)  # official would raise on missing IDs; we mimic leaderboard by NaN rows
    p["kappa_tot_avg"] = p["kappa_tot_rta"].map(kavg)
    for mid in ref.index:
        rp, rt = p.loc[mid], ref.loc[mid]
        tv = single(rt["kappa_tot_avg"]); pv = single(rp["kappa_tot_avg"])
        srd = -KMAX if pv is None else (0.0 if pv + tv == 0 else KMAX * (pv - tv) / (pv + tv))
        try: r = np.ravel(srme1(rp, rt))
        except (KeyError, TypeError, ValueError, ZeroDivisionError): r = np.array([np.nan])
        h = rp.get("has_imag_ph_modes"); cens = not pd.isna(h) and bool(h)
        rs = rp.get("final_spg_num")
        if not cens and not pd.isna(rs) and rs:
            i = rp.get("init_spg_num"); e = rt.get("init_spg_num") if pd.isna(i) else i
            cens = not pd.isna(e) and rs != e
        valid = not cens and r.size == 1 and np.isfinite(r[0])
        s = float(r[0]) if valid else KMAX
        o = pm.loc[(m["model"], mid)]
        worst.append({"model": m["model"], "mid": mid, "d_srd": abs(o.srd - srd), "d_srme": abs(o.srme - s),
                      "d_cens": bool(o.censored) != (not valid), "n_missing_ids": len(missing),
                      "dup_ids": int(pd.read_json(f"{RAW}/{m['file']}").material_id.duplicated().sum()) if mid == ref.index[0] else 0})
w = pd.DataFrame(worst)
print("rows", len(w), "max d_srd", w.d_srd.max(), "max d_srme", w.d_srme.max(), "censor flag disagreements", w.d_cens.sum())
print("models with missing ids:", w.groupby("model").n_missing_ids.first().loc[lambda s: s > 0].to_dict())
print("dup ids:", w.groupby("model").dup_ids.sum().loc[lambda s: s > 0].to_dict())
print(w.sort_values("d_srme", ascending=False).head(5))
