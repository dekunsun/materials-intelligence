"""Generate 20 EquiCSP candidates for each of the 11 ABC2D6 targets from one trained run.

Runs in the EquiCSP environment (torch 1.9, data/raw/equicsp_venv) with PROJECT_ROOT pointing at the
EquiCSP checkout. It changes no model code: it builds the model from the run's hparams.yaml as
EquiCSP's scripts/eval_utils.load_model does, loads the named checkpoint (the validation-selected one; the
upstream helper would load last.ckpt by default), and calls the model's own sample() with the upstream
default step_lr of 5e-6 (scripts/sample.py and scripts/evaluate.py) and its 1,000 diffusion steps.

Inputs are explicit primitive-cell element counts, as in the paper's protocol: T180 queries.csv, with the
resolved 20-atom Sr4Tm2Nb2O12 input for mp-557387 (ablation/PROTOCOL.md). These match the compositions of
the paper's released candidates for both arms.

Seeding (pre-registration amendment A1): before each target, torch, numpy and random are seeded with the
run's training seed, so each target's 20 draws do not depend on the order targets are run in.

Usage: PROJECT_ROOT=<EquiCSP checkout> python sample.py <run_dir> <checkpoint file name> <out_dir> <seed> [device]
Writes <out_dir>/<material_id>/equicsp_0001.cif ... equicsp_0020.cif and <out_dir>/sample_meta.json.
"""
import hashlib
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, os.environ["PROJECT_ROOT"])

import numpy as np  # noqa: E402
import torch  # noqa: E402
import hydra  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402
from pymatgen.core import Composition, Lattice, Structure  # noqa: E402
from pymatgen.io.cif import CifWriter  # noqa: E402
from torch_geometric.data import Batch, Data  # noqa: E402

from equicsp.common.data_utils import chemical_symbols  # noqa: E402

# EquiCSP's diff_utils loads its precomputed normalisation tables with torch.load and no map_location; they
# were saved from a GPU, so on a CPU-only machine every torch.load is mapped to the CPU. Values are unchanged;
# the module moves them to the sampling device afterwards.
_torch_load = torch.load
torch.load = lambda f, *a, **k: _torch_load(f, *a, **{"map_location": "cpu", **k})

# CSPDiffusion.__init__ builds a lattice-permutation table with device='cuda' (used in training, not in
# sample()). Without a GPU that tensor is put on the CPU instead; nothing else changes.
if not torch.cuda.is_available():
    _torch_tensor = torch.tensor
    torch.tensor = lambda *a, **k: _torch_tensor(*a, **{**k, "device": "cpu"} if k.get("device") == "cuda" else k)

N_CANDIDATES = 20
STEP_LR = 5e-6
INPUTS = {  # material_id -> explicit primitive-cell counts
    "mp-6231": "Ba2Er1Sb1O6", "mp-19093": "Ba2U1Ni1O6", "mp-19274": "Ba1Pr1Mn2O6", "mp-6389": "Na2La4Ru2O12",
    "mp-16307": "Sr2Mg1Ir1O6", "mp-557387": "Sr4Tm2Nb2O12", "mp-6603": "Sr4Ce2Ir2O12", "mp-1215245": "Zr1Ti1Ni2H6",
    "mp-10321": "La4Zn2Rh2O12", "mp-12449": "Li2Pr4Os2O12", "mp-556434": "Ag2Bi2P4S12",
}


def cpu_name():
    try:
        import subprocess
        return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        return platform.processor() or platform.machine()


def lattices_to_params(lattices):
    # Same as EquiCSP scripts/eval_utils.lattices_to_params_shape.
    lengths = torch.sqrt(torch.sum(lattices ** 2, dim=-1))
    angles = torch.zeros_like(lengths)
    for i in range(3):
        j, k = (i + 1) % 3, (i + 2) % 3
        angles[..., i] = torch.clamp(torch.sum(lattices[..., j, :] * lattices[..., k, :], dim=-1)
                                     / (lengths[..., j] * lengths[..., k]), -1., 1.)
    return lengths, torch.arccos(angles) * 180.0 / np.pi


def load(run_dir: Path, ckpt_name: str, device: str):
    # Read hparams.yaml directly (Hydra 1.1's compose() rejects this saved file's hydra/config schema).
    cfg = OmegaConf.load(run_dir / "hparams.yaml")
    model = hydra.utils.instantiate(cfg.model, optim=cfg.optim, data=cfg.data, logging=cfg.logging, _recursive_=False)
    state = torch.load(run_dir / ckpt_name, map_location="cpu")["state_dict"]
    missing, unexpected = model.load_state_dict(state, strict=False)
    model.lattice_scaler = torch.load(run_dir / "lattice_scaler.pt")
    model.scaler = torch.load(run_dir / "prop_scaler.pt")
    return model.to(device).eval(), {"missing_keys": list(missing), "unexpected_keys": list(unexpected)}


def main(run_dir, ckpt_name, out_dir, seed, device="cpu"):
    run_dir, out_dir, seed = Path(run_dir).resolve(), Path(out_dir), int(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    model, keys = load(run_dir, ckpt_name, device)
    meta = {"run_dir": str(run_dir), "checkpoint": ckpt_name,
            "checkpoint_sha256": hashlib.sha256((run_dir / ckpt_name).read_bytes()).hexdigest(),
            "load_state_dict": keys, "seed": seed, "step_lr": STEP_LR, "n_candidates": N_CANDIDATES,
            "diffusion_steps": int(model.beta_scheduler.timesteps), "device": device,
            "device_name": torch.cuda.get_device_name(0) if device.startswith("cuda") else cpu_name(),
            "torch_threads": torch.get_num_threads(),
            "torch": torch.__version__, "python": platform.python_version(), "targets": {}}
    only = os.environ.get("G0_ONLY", "").split(",") if os.environ.get("G0_ONLY") else None  # for timing tests
    for mid, formula in INPUTS.items():
        if only and mid not in only:
            continue
        torch.manual_seed(seed); np.random.seed(seed); random.seed(seed)
        comp = Composition(formula)
        types = [chemical_symbols.index(el.symbol) for el, n in comp.items() for _ in range(int(n))]
        data = [Data(atom_types=torch.LongTensor(types), num_atoms=len(types), num_nodes=len(types)) for _ in range(N_CANDIDATES)]
        batch = Batch.from_data_list(data).to(device)
        t0 = time.time()
        out, _ = model.sample(batch, step_lr=STEP_LR)
        secs = time.time() - t0
        lengths, angles = lattices_to_params(out["lattices"].cpu())
        frac, atoms, nat = out["frac_coords"].cpu().numpy(), out["atom_types"].cpu().numpy(), out["num_atoms"].cpu().tolist()
        d = out_dir / mid
        d.mkdir(exist_ok=True)
        start, n_ok, bad = 0, 0, []
        for i, n in enumerate(nat):
            try:
                s = Structure(Lattice.from_parameters(*(lengths[i].tolist() + angles[i].tolist())),
                              [chemical_symbols[int(z)] for z in atoms[start:start + n]], frac[start:start + n])
                assert s.composition == comp, f"composition {s.composition} != {comp}"
                CifWriter(s).write_file(d / f"equicsp_{i + 1:04d}.cif")
                n_ok += 1
            except Exception as e:  # recorded, not hidden: missing generation is reported explicitly
                bad.append({"candidate": i + 1, "error": repr(e)})
            start += n
        meta["targets"][mid] = {"input": formula, "n_atoms": len(types), "written": n_ok, "failed": bad,
                                "sample_seconds": round(secs, 1)}
        print(mid, meta["targets"][mid], flush=True)
    (out_dir / "sample_meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:])
