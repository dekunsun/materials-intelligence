"""Initial-structure pilot: Wrenformer, the template-like baseline (CPU, no relaxation).

Design: modules/csp/INITIAL_STRUCTURE_PILOT.md, Section 4. Matbench Discovery's Wrenformer is an ensemble of 10; only one
member's checkpoint is public (the model card's checkpoint_url, wandb run 2kozbp4q, ensemble member 2, trained on MP
2022-08-13 formation energies). So this is a single checkpoint, a weaker baseline than the ensemble.

Runs in data/raw/aviary_venv with aviary v0.1.0 (the version on the model card) imported from its source folder
data/raw/aviary_src/aviary-0.1.0 (nothing installed from it). Two changes from that environment, both outside aviary:
  - wandb and torch.utils.tensorboard are replaced by empty modules; aviary.core imports them for training only.
  - the checkpoint is loaded with torch's weights_only loader. Its pickle names only tensors, OrderedDict and two
    aviary classes (RobustL1Loss, Normalizer; checked with pickletools), so no pickled code runs.

Usage (repository root):
    data/raw/aviary_venv/bin/python -I src/csp/init_pilot_wrenformer.py validate results/<run>
        predicts WBM from its initial-structure Wyckoff labels and compares with the published ensemble predictions
    data/raw/aviary_venv/bin/python -I src/csp/init_pilot_wrenformer.py pilot results/<run>
        labels every rebuilt initial structure (data/raw/alexandria/pilot/initial_structures.json.gz) with aviary
        v0.1.0's get_aflow_label_from_spglib, as Matbench Discovery labelled WBM's initial structures, and predicts;
        writes results/<run>/predictions/Wrenformer_initial.csv: mat_id, assignment, label, e_form_per_atom
        (a structure whose label cannot be made gets no prediction)
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AVIARY = ROOT / "data/raw/aviary_src/aviary-0.1.0"
CHECKPOINT = ROOT / "data/raw/wrenformer/checkpoint.pth"
DISCOVERY = ROOT / "data/raw/discovery/6d587c184cdb4a4865dc0b15b04a5e6d77ed464f"
N_VALIDATE, SEED = 5000, 11


def _import_aviary():
    for name in ["wandb", "torch.utils.tensorboard"]:
        mod = types.ModuleType(name)
        mod.SummaryWriter = None
        sys.modules[name] = mod
    sys.path.insert(0, str(AVIARY))
    import aviary.wrenformer.data as data
    from aviary.wrenformer.model import Wrenformer
    return data, Wrenformer


def load_model():
    import torch
    data, Wrenformer = _import_aviary()
    import aviary.core
    import aviary.losses
    torch.serialization.add_safe_globals([aviary.losses.RobustL1Loss, aviary.core.Normalizer])
    ck = torch.load(CHECKPOINT, weights_only=True, map_location="cpu")
    model = Wrenformer(**ck["model_params"])
    model.load_state_dict(ck["model_state"])  # strict: every weight must match
    model.eval()
    norm = ck["normalizer_dict"]["formation_energy_per_atom"]
    return data, model, norm


def predict(labels: pd.Series) -> pd.Series:
    """labels: Wyckoff labels indexed by id. Returns predicted formation energy (eV/atom, MP2020 convention)."""
    import torch
    data, model, norm = load_model()
    df = pd.DataFrame({"label": labels.to_numpy()}, index=labels.index)
    loader = data.df_to_in_mem_dataloader(df, input_col="label", embedding_type="wyckoff", device="cpu",
                                          batch_size=256, shuffle=False)
    out = []
    with torch.no_grad():
        for inputs, _, ids in loader:
            pred = model(*inputs)[0]  # robust head: (mean, log std); keep the mean
            mean = pred[:, 0] if pred.ndim == 2 else pred
            out.append(pd.Series(norm.denorm(mean).numpy(), index=ids))
    return pd.concat(out).reindex(labels.index)


def validate(run: Path) -> int:
    wbm = pd.read_csv(DISCOVERY / "wbm_summary.csv.gz").set_index("material_id")
    ens = pd.read_csv(DISCOVERY / "Wrenformer.csv.gz").set_index("material_id")["e_form_per_atom"]
    ids = wbm.dropna(subset=["protostructure_spglib_initial_structure"]).sample(N_VALIDATE, random_state=SEED).index
    p = predict(wbm.loc[ids, "protostructure_spglib_initial_structure"])
    dft = wbm.loc[ids, "e_form_per_atom_mp2020_corrected"]
    res = {"n": int(p.notna().sum()), "what": "single checkpoint vs published 10-model ensemble, WBM initial labels",
           "median_abs_vs_ensemble": float((p - ens.loc[ids]).abs().median()),
           "mean_abs_vs_ensemble": float((p - ens.loc[ids]).abs().mean()),
           "corr_vs_ensemble": float(np.corrcoef(p, ens.loc[ids])[0, 1]),
           "mae_single_vs_dft": float((p - dft).abs().mean()), "mae_ensemble_vs_dft": float((ens.loc[ids] - dft).abs().mean())}
    run.mkdir(parents=True, exist_ok=True)
    (run / "wrenformer_validation.json").write_text(json.dumps(res, indent=1))
    print(res)
    return 0


def pilot(run: Path) -> int:
    import gzip
    import warnings
    from pymatgen.core import Structure
    _import_aviary()
    from aviary.wren.utils import get_aflow_label_from_spglib
    warnings.filterwarnings("ignore")
    recs = json.load(gzip.open(ROOT / "data/raw/alexandria/pilot/initial_structures.json.gz", "rt"))
    rows = []
    for mid, r in sorted(recs.items()):
        for k, a in enumerate(r["assignments"]):
            try:
                label = get_aflow_label_from_spglib(Structure.from_dict(a["structure"]), errors="annotate")
            except Exception as exc:  # noqa: BLE001 - no label, no prediction
                label = f"invalid {type(exc).__name__}"
            rows.append({"mat_id": mid, "assignment": k, "label": label})
    df = pd.DataFrame(rows)
    ok = ~df.label.str.startswith("invalid")
    df["e_form_per_atom"] = np.nan
    if ok.any():
        df.loc[ok, "e_form_per_atom"] = predict(df.loc[ok, "label"]).to_numpy()
    out = run / "predictions" / "Wrenformer_initial.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print({"structures": len(df), "labelled": int(ok.sum()), "predicted": int(df.e_form_per_atom.notna().sum())})
    return 0


def main() -> int:
    if sys.argv[1] == "validate":
        return validate(Path(sys.argv[2]))
    if sys.argv[1] == "pilot":
        return pilot(Path(sys.argv[2]))
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
