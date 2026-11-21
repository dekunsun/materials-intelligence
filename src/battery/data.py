"""Load OBELiX into a pool of unique compositions with composition-only features.

Why composition-only: 278 of 599 OBELiX entries have no matching CIF, and the
point of the experiment is the selection policy, not the best property model.
Every method below sees exactly the same features, so the comparison is fair.

Duplicates: the same composition can appear several times (different papers,
different measurements). One "experiment" on a composition returns the median
log10 conductivity of its measurements. A composition group goes to the test
split if any of its entries is in OBELiX's official test split, so the same
material can never sit on both sides.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "4eaac889809dd489e3bae468c45d5c0e02b9147a"
RAW = ROOT / "data" / "raw" / "obelix" / COMMIT

# Anion / framework elements worth flagging explicitly. Chosen before looking
# at any results: the common solid-electrolyte chemistries (oxide, sulfide,
# halide, phosphate, nitride, borohydride families).
FLAG_ELEMENTS = ["O", "S", "Se", "P", "Cl", "Br", "I", "F", "N", "B", "Si", "Ge", "Zr", "La", "Ti", "Al"]


@dataclass
class Pool:
    keys: list[str]            # canonical composition key per row
    X: np.ndarray              # features, standardized later per campaign
    y: np.ndarray              # median log10 ionic conductivity (S/cm)
    split: np.ndarray          # "train" or "test"
    n_measurements: np.ndarray
    feature_names: list[str]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_key(formula: str) -> str:
    """Fractional composition rounded to 3 decimals, sorted by element."""
    frac = Composition(formula).fractional_composition
    return " ".join(f"{el.symbol}{amt:.3f}" for el, amt in sorted(frac.items(), key=lambda kv: kv[0].symbol))


def _prop(el: Element, name: str) -> float:
    v = getattr(el, name, None)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def featurize(formula: str) -> dict[str, float]:
    comp = Composition(formula).fractional_composition
    els = list(comp.keys())
    w = np.array([comp[e] for e in els])
    feats: dict[str, float] = {"li_frac": float(comp["Li"]) if Element("Li") in comp else 0.0,
                               "n_elements": float(len(els))}
    for prop in ["X", "atomic_radius", "atomic_mass", "row", "group"]:
        vals = np.array([_prop(e, prop) for e in els])
        ok = ~np.isnan(vals)
        mean = float(np.sum(w[ok] * vals[ok]) / np.sum(w[ok])) if ok.any() else 0.0
        var = float(np.sum(w[ok] * (vals[ok] - mean) ** 2) / np.sum(w[ok])) if ok.any() else 0.0
        feats[f"{prop}_mean"] = mean
        feats[f"{prop}_std"] = var ** 0.5
        feats[f"{prop}_max"] = float(np.nanmax(vals)) if ok.any() else 0.0
        feats[f"{prop}_min"] = float(np.nanmin(vals)) if ok.any() else 0.0
    for sym in FLAG_ELEMENTS:
        feats[f"frac_{sym}"] = float(comp[sym]) if Element(sym) in comp else 0.0
    return feats


def family_of(key: str) -> str:
    """Coarse chemistry family from the canonical key: oxide > sulfide > halide > other.

    Fixed before any campaign ran. Oxygen wins, so oxyhalides and oxysulfides count as oxides.
    """
    els = {tok.rstrip("0123456789.") for tok in key.split()}
    if "O" in els:
        return "oxide"
    if els & {"S", "Se"}:
        return "sulfide"
    if els & {"Cl", "Br", "I", "F"}:
        return "halide"
    return "other"


def load_pool() -> tuple[Pool, dict]:
    df = pd.read_csv(RAW / "processed.csv")
    test_ids = set(pd.read_csv(RAW / "test_idx.csv").ID)
    df["key"] = df["Composition"].map(canonical_key)
    df["log_ic"] = np.log10(df["Ionic conductivity (S cm-1)"])
    df["is_test"] = df["ID"].isin(test_ids)

    groups = df.groupby("key", sort=True)
    agg = groups.agg(log_ic=("log_ic", "median"), n=("ID", "size"),
                     any_test=("is_test", "any"), all_test=("is_test", "all"),
                     formula=("Composition", "first")).reset_index()
    mixed = int(((agg.any_test) & (~agg.all_test)).sum())

    rows = [featurize(f) for f in agg.formula]
    names = list(rows[0].keys())
    X = np.array([[r[n] for n in names] for r in rows], dtype=float)

    pool = Pool(keys=agg.key.tolist(), X=X, y=agg.log_ic.to_numpy(),
                split=np.where(agg.any_test, "test", "train"),
                n_measurements=agg.n.to_numpy(), feature_names=names)
    info = {"entries": int(len(df)), "unique_compositions": int(len(agg)),
            "groups_split_across_official_train_test": mixed,
            "train_compositions": int((pool.split == "train").sum()),
            "test_compositions": int((pool.split == "test").sum()),
            "processed_csv_sha256": file_sha256(RAW / "processed.csv"),
            "test_idx_sha256": file_sha256(RAW / "test_idx.csv")}
    return pool, info
