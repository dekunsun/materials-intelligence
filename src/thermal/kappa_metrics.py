"""Re-implementation of the Matbench Discovery kappa-103 metrics, written from
the formulas in matbench_discovery/metrics/phonons.py (commit 6d587c1) rather
than imported, so that agreement with the leaderboard is an independent check.

Per material (300 K, one temperature):
  kappa      = mean of the diagonal of the conductivity tensor (Voigt xx, yy, zz)
  SRD        = 2 (k_pred - k_dft) / (k_pred + k_dft)      in [-2, 2]
  SRE        = |SRD|
  SRME       = 2 * sum_modes |k_pred,i - k_dft,i| / sum(mode_weights) / (k_pred + k_dft)
  censored   : SRME set to the worst value, 2, when the prediction has imaginary
               modes, its relaxed space group differs from the initial one, or the
               numbers are missing / non-finite.

Note: the leaderboard censors SRME for imaginary modes but NOT SRE/SRD; it only
assigns SRD = -2 when the predicted kappa itself is missing. We reproduce that
exactly for the leaderboard check, and keep a separate flag so analyses can
choose to exclude censored materials.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

KMAX = 2.0


def _arr(v):
    try:
        a = np.asarray(v, dtype=float)
    except (TypeError, ValueError):
        return None
    if a.size == 0 or not np.all(np.isfinite(a)):
        return None
    return a


def kappa_avg(v) -> float:
    """Directional average at the single temperature; NaN (scored as a failure) otherwise."""
    a = _arr(v)
    if a is None:
        return np.nan
    if a.shape[-2:] == (3, 3):
        k = np.trace(a, axis1=-2, axis2=-1) / 3
    elif a.shape[-1] == 6:
        k = a[..., :3].mean(-1)
    elif a.shape[-1] == 3:
        k = a.mean(-1)
    else:
        return np.nan
    k = np.ravel(k)
    return float(k[0]) if k.size == 1 else np.nan   # several temperatures: official scores SRD -2


def mode_kappa(row: pd.Series):
    if "mode_kappa_tot_avg" in row.index and (a := _arr(row["mode_kappa_tot_avg"])) is not None:
        return a
    if "mode_kappa_tot_rta" in row.index and (a := _arr(row["mode_kappa_tot_rta"])) is not None:
        if a.shape[-2:] == (3, 3):          # full tensor per mode (newer files)
            return np.trace(a, axis1=-2, axis2=-1) / 3
        if a.shape[-1] == 6:
            return a[..., :3].mean(-1)
        if a.shape[-1] == 3:
            return a.mean(-1)
        return None
    return None


def score_model(pred: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    """pred and ref indexed by material_id; returns one row per reference material."""
    missing = set(ref.index) - set(pred.index)
    if missing:   # the official evaluator refuses incomplete prediction files
        raise ValueError(f"prediction file lacks {len(missing)} reference materials")
    out = []
    for mid, rt in ref.iterrows():
        k_true = float(np.ravel(rt["kappa_tot_avg"])[0])
        rec = {"material_id": mid, "name": rt["name"], "spg": int(rt["init_spg_num"]), "k_dft": k_true}
        rp = pred.loc[mid] if mid in pred.index else None
        if rp is not None:
            def _is_set(v):
                miss = pd.isna(v)
                return not (isinstance(miss, (bool, np.bool_)) and bool(miss)) and bool(v)
            errs = rp.get("errors") if "errors" in rp.index else None
            skipped = rp.get("conductivity_skipped") if "conductivity_skipped" in rp.index else None
            if (errs is not None and _is_set(errs)) or (skipped is not None and _is_set(skipped)):
                # leaderboard drops kappa for these records; flags stay, as in the official code
                rp = rp.copy()
                for col in ("kappa_tot_rta", "mode_kappa_tot_rta", "mode_kappa_tot_avg", "mode_weights"):
                    if col in rp.index:
                        rp[col] = np.nan
        k_pred = kappa_avg(rp["kappa_tot_rta"]) if rp is not None and "kappa_tot_rta" in rp.index else np.nan
        if not (k_pred >= 0):
            k_pred = np.nan
        rec["k_pred"] = k_pred
        srd = -KMAX if np.isnan(k_pred) else (0.0 if k_pred + k_true == 0 else KMAX * (k_pred - k_true) / (k_pred + k_true))
        rec["srd"], rec["sre"] = srd, abs(srd)
        # SRME
        srme = np.nan
        if rp is not None and not np.isnan(k_pred):
            mp, mt = mode_kappa(rp), mode_kappa(rt)
            w = _arr(rp.get("mode_weights"))
            if w is not None and np.any(w < 0):
                w = None
            if mp is not None and mt is not None and w is not None and w.sum() > 0 and mp.shape == mt.shape:
                micro = np.abs(mp - mt).sum() / w.sum()
                den = k_pred + k_true
                srme = (0.0 if micro == 0 else KMAX) if den == 0 else KMAX * micro / den
        imag = rp is not None and "has_imag_ph_modes" in rp.index and not pd.isna(rp["has_imag_ph_modes"]) and bool(rp["has_imag_ph_modes"])
        spg_broken = False
        if rp is not None and "final_spg_num" in rp.index and not pd.isna(rp["final_spg_num"]) and rp["final_spg_num"]:
            init = rp["init_spg_num"] if "init_spg_num" in rp.index and not pd.isna(rp["init_spg_num"]) else rt["init_spg_num"]
            spg_broken = int(rp["final_spg_num"]) != int(init)
        censored = imag or spg_broken or not (np.isfinite(srme) and 0 <= srme <= KMAX)
        rec["srme"] = KMAX if censored else float(srme)
        rec["censored"], rec["imag_modes"], rec["spg_broken"] = censored, imag, spg_broken
        out.append(rec)
    return pd.DataFrame(out).set_index("material_id")
