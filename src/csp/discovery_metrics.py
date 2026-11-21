"""Re-implementation of the Matbench Discovery stability-screening metrics.

Written from matbench_discovery/metrics/discovery.py at commit 6d587c1, not
imported, so that agreement with the leaderboard is an independent check.

Leaderboard conventions reproduced here:
  * predictions further than 5 eV/atom from the DFT formation energy are masked
  * reference columns and predictions are rounded to 3 decimals
  * predicted hull distance = DFT hull distance + (predicted - DFT formation energy),
    computed in that order (pred + each_true - e_form_dft)
  * "stable" means hull distance <= 0; a missing prediction counts as "unstable"
  * DAF on unique prototypes divides by the prevalence from UNROUNDED hull distances
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

EACH_TRUE = "e_above_hull_mp2020_corrected_ppd_mp"
E_FORM_DFT = "e_form_per_atom_mp2020_corrected"
UNIQ = "unique_prototype"
MAX_ERR = 5.0


def prepare(wbm: pd.DataFrame, pred: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Mask outliers and round, as the leaderboard does. wbm is indexed by material_id."""
    p = pd.to_numeric(pred.reindex(wbm.index), errors="coerce")
    p = p.mask((p - wbm[E_FORM_DFT]).abs() > MAX_ERR).round(3)
    ref = wbm[[EACH_TRUE, E_FORM_DFT]].round(3)
    return ref, p


def pred_hull(ref: pd.DataFrame, p: pd.Series) -> pd.Series:
    return p.add(ref[EACH_TRUE]).sub(ref[E_FORM_DFT])


def classify(each_true: pd.Series, each_pred: pd.Series, thr: float = 0.0) -> dict:
    actual = each_true <= thr
    model = (each_pred <= thr) & each_pred.notna()
    tp = int((actual & model).sum()); fn = int((actual & ~model).sum())
    fp = int((~actual & model).sum()); tn = int((~actual & ~model).sum())
    n = tp + fn + fp + tn
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    ok = each_true.notna() & each_pred.notna()
    err = (each_true[ok] - each_pred[ok]).to_numpy()
    return {"F1": 2 * prec * rec / (prec + rec) if prec + rec else np.nan,
            "Precision": prec, "Recall": rec, "Accuracy": (tp + tn) / n,
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "DAF": prec / ((tp + fn) / n) if tp + fn else np.nan,
            "MAE": float(np.abs(err).mean()), "RMSE": float(np.sqrt((err ** 2).mean())),
            "R2": float(1 - (err ** 2).sum() / ((each_true[ok] - each_true[ok].mean()) ** 2).sum())}


def leaderboard_metrics(wbm: pd.DataFrame, pred: pd.Series) -> dict:
    ref, p = prepare(wbm, pred)
    each_pred = pred_hull(ref, p)
    uniq = wbm[UNIQ].astype(bool)
    full = classify(ref[EACH_TRUE], each_pred)
    up = classify(ref[EACH_TRUE][uniq], each_pred[uniq])
    prevalence_unrounded = float((wbm.loc[uniq, EACH_TRUE] <= 0).mean())
    up["DAF"] = up["Precision"] / prevalence_unrounded
    full["missing_preds"] = int(p.isna().sum()); up["missing_preds"] = int(p[uniq].isna().sum())
    return {"full_test_set": full, "unique_prototypes": up}


def precision_at_k(each_true: np.ndarray, each_pred: np.ndarray, k: int) -> float:
    """Share of truly stable structures among the k with the lowest predicted hull distance.
    Missing predictions rank last. Predictions are rounded to 3 decimals, so the group tied
    at the cutoff is counted in expectation (as if ties were broken at random)."""
    score = np.where(np.isnan(each_pred), np.inf, each_pred)
    if k >= len(score):
        return float((each_true <= 0).mean())
    v = np.partition(score, k - 1)[k - 1]
    below, tied = score < v, score == v
    stable = each_true <= 0
    return float((stable[below].sum() + (k - below.sum()) * stable[tied].mean()) / k)


def prototype_type(label: str, element_order_invariant: bool = True) -> str | None:
    """Structure type from an AFLOW-style protostructure label such as 'A3B_hP8_194_h_c:Ac-U'.

    The chemistry after ':' is dropped. The letters A, B, ... are assigned to elements in
    alphabetical order, so substituting elements can rename the same structure type
    (A3B_hP8_194_h_c vs AB3_hP8_194_c_h). With element_order_invariant=True the
    (multiplicity, Wyckoff) pairs are sorted so both spellings map to one key.
    """
    if not isinstance(label, str):
        return None
    bare = label.split(":")[0]
    if not element_order_invariant:
        return bare
    parts = bare.split("_")
    formula, pearson, spg, wyck = parts[0], parts[1], parts[2], parts[3:]
    toks = re.findall(r"([A-Z])(\d*)", formula)
    if len(toks) != len(wyck):
        return "UNPARSED:" + bare
    pairs = sorted((int(n or 1), w) for (_, n), w in zip(toks, wyck))
    return f"{pearson}_{spg}_" + "|".join(f"{n}:{w}" for n, w in pairs)
