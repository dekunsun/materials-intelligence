"""Random-removal control for the CSP paper's perovskite-framework result.

Question. Wei et al. (arXiv:2609.26502 v2) retrained EquiCSP without the
perovskite frameworks and its consensus recovery of the 11 1:1:2:6 targets fell
from 8 to 3. Did it fall because specific template information was removed, or
just because the model had less training data?

What the paper's released arms already allow (step 1, descriptive, no training):
the ABC2D6 arm and the perovskite-framework (PEROV) arm were trained with the
same recipe (seed 42, 106,000 steps, validation-selected checkpoint) and scored
on the same 11 targets. PEROV removes the ABC2D6 family plus 1,268 training and
410 validation structures whose framework matches a perovskite target. So
ABC2D6 vs PEROV is the cleanest existing contrast: it removes the paper's
checkpoint-selection confound (its baseline is the upstream checkpoint), but it
still mixes "which structures" with "how many" and with run-to-run noise.

What it does not allow, and what the control adds (step 2): arms R1-R3 remove
the same ABC2D6 family plus the same NUMBER of extra structures (1,268 train,
410 val) drawn at random from structures that are not perovskite frameworks.
PEROV and R then have identical training-set sizes and identical family
removal; they differ only in which extra structures are gone. This script only
builds and hashes the splits. Training is a separate, paid step (see
modules/csp/RANDOM_REMOVAL_CONTROL.md) and is not run here.

The decision rules are written to config.json before anything else and are
committed to git before any training run.

Usage:
    .venv/bin/python -I src/csp/random_removal_control.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from thermal.provenance import write as write_provenance  # noqa: E402

RAW = ROOT / "data" / "raw" / "csp_ablation"
ABL = RAW / "benchmark" / "ablation"

PRE_REGISTERED = {
    "question": "Is EquiCSP's loss of 1:1:2:6 consensus recoveries after perovskite-framework removal specific to those "
                "structures, or would removing the same number of random structures cause it too?",
    "model": "EquiCSP, recipe of the paper's ablation/PROTOCOL.md: 106,000 optimizer steps, effective batch 256 "
             "(64 x 4 accumulation), FP32, validation-selected checkpoint; never initialised from a published checkpoint",
    "targets": "the 11 ABC2D6 targets of T180 (benchmark_deep_csp data/testsets/v3.1), 20 candidates each",
    "arms": {
        "ABC2D6": "remove the ABC2D6 family (1,551 train / 487 val), as released by the paper",
        "PEROV": "ABC2D6 family plus 1,268 train / 410 val perovskite-framework structures, as released by the paper",
        "R1-R3": "ABC2D6 family plus 1,268 train / 410 val drawn uniformly at random, without replacement, from the "
                 "structures left after the ABC2D6 removal that are not in the PEROV lists; one draw per arm",
    },
    "runs": [
        {"arm": "ABC2D6", "seed": 42, "role": "runner check (paper: consensus 8 of 11)"},
        {"arm": "PEROV", "seed": 42, "role": "runner check (paper: consensus 3 of 11) and PEROV run 1"},
        {"arm": "PEROV", "seed": 43, "role": "PEROV run 2"},
        {"arm": "PEROV", "seed": 44, "role": "PEROV run 3"},
        {"arm": "R1", "seed": 42, "role": "random run 1"},
        {"arm": "R2", "seed": 43, "role": "random run 2"},
        {"arm": "R3", "seed": 44, "role": "random run 3"},
    ],
    "optional_runs": [{"arm": "ABC2D6", "seed": 43}, {"arm": "ABC2D6", "seed": 44}],
    "draw_seeds": {"R1": 2026112101, "R2": 2026112102, "R3": 2026112103},
    "primary_metric": "consensus: number of the 11 targets for which one candidate passes StructureMatcher "
                      "(ltol 0.2, stol 0.3, angle_tol 5) and has the target's space group (symprec 0.1)",
    "secondary_metric": "fit: number of the 11 targets matched by at least one of the 20 candidates",
    "decision_rules": {
        "G0_runner": "Our ABC2D6 seed-42 and PEROV seed-42 runs must give consensus within 1 of the paper's 8 and 3. "
                     "If either misses, stop: audit the runner before attributing anything (no further runs are spent).",
        "template_specific": "Supported if every R run beats every PEROV run on consensus AND mean(R) - mean(PEROV) >= 3.",
        "data_amount": "Supported if mean(R) - mean(PEROV) <= 1: removing the same number of random structures "
                       "does about as much damage.",
        "not_reproduced": "If mean(PEROV) >= 6, the 8 -> 3 drop does not survive repeated seeds; report that and stop.",
        "otherwise": "Inconclusive. Report all runs; no further runs without a new written decision.",
        "note": "With 3 vs 3 runs the smallest exact one-sided permutation p-value is 1/20 = 0.05; we report "
                "counts per run and per target and do not claim more than that.",
    },
    "cost_gate": "Before any full run: one smoke run of 1,000 steps on the rented GPU to measure time per step, "
                 "then report the projected cost of all runs and wait for the owner's go-ahead.",
    "limits": [
        "Random draws are not matched on composition or number of species to the perovskite structures; the control "
        "tests 'these structures' against 'any structures of the same count', nothing finer.",
        "11 targets: one target is 9 percentage points.",
        "One model (EquiCSP), one family (perovskite frameworks).",
    ],
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ids(path: Path) -> set[str]:
    return set(pd.read_csv(path)["material_id"])


def step1_existing_arms(run: Path) -> dict:
    """Descriptive: recompute the paper's summary from its per-target file and pair ABC2D6 with PEROV."""
    per = pd.read_csv(ABL / "ablation_per_target.csv")
    summ = pd.read_csv(ABL / "ablation_summary.csv")
    rows = []
    for (algo, arm), g in per.groupby(["algo", "arm"]):
        rows.append({"algo": algo, "arm": arm, "n": len(g), "base_fit": int(g.base_fit.sum()), "base_cons": int(g.base_cons.sum()),
                     "abl_fit": int(g.abl_fit.sum()), "abl_cons": int(g.abl_cons.sum())})
    recomputed = pd.DataFrame(rows).merge(summ, on=["algo", "arm"], suffixes=("", "_released"))
    cols = ["n", "base_fit", "base_cons", "abl_fit", "abl_cons"]
    mism = [(r.algo, r.arm, c) for r in recomputed.itertuples() for c in cols if getattr(r, c) != getattr(r, c + "_released")]

    e = per[per.algo == "equicsp"]
    a = e[e.arm == "ABC2D6"].set_index("material_id")
    p = e[e.arm == "PEROV"].set_index("material_id")
    pair = pd.DataFrame({"base_fit": a.base_fit, "base_cons": a.base_cons,
                         "abc2d6_fit": a.abl_fit, "abc2d6_cons": a.abl_cons,
                         "perov_fit": p.abl_fit.reindex(a.index), "perov_cons": p.abl_cons.reindex(a.index)})
    pair.index.name = "material_id"
    pair.to_csv(run / "existing_arms_paired.csv")
    out = {
        "status": "post-hoc (the counts were read before this script was written)",
        "summary_recomputed_from_per_target": not mism, "mismatches": mism,
        "equicsp_targets": len(pair),
        "consensus": {"baseline": int(pair.base_cons.sum()), "ABC2D6": int(pair.abc2d6_cons.sum()), "PEROV": int(pair.perov_cons.sum())},
        "fit": {"baseline": int(pair.base_fit.sum()), "ABC2D6": int(pair.abc2d6_fit.sum()), "PEROV": int(pair.perov_fit.sum())},
        "ABC2D6_to_PEROV_consensus_lost": sorted(pair.index[pair.abc2d6_cons & ~pair.perov_cons]),
        "ABC2D6_to_PEROV_consensus_gained": sorted(pair.index[~pair.abc2d6_cons & pair.perov_cons]),
        "ABC2D6_to_PEROV_fit_lost": sorted(pair.index[pair.abc2d6_fit & ~pair.perov_fit]),
        "ABC2D6_to_PEROV_fit_gained": sorted(pair.index[~pair.abc2d6_fit & pair.perov_fit]),
        "baseline_to_ABC2D6_fit_gained": sorted(pair.index[~pair.base_fit & pair.abc2d6_fit]),
        "reading": "ABC2D6 and PEROV share recipe, seed and checkpoint selection, so this contrast is free of the paper's "
                   "checkpoint-selection confound. It is not free of training-set size (PEROV has 1,268 fewer training "
                   "structures) or of run-to-run noise (one run per arm; ABC2D6 alone moved fit from 8 to 10).",
    }
    return out


def step2_splits(run: Path) -> dict:
    train = pd.read_csv(RAW / "mp_20" / "train.csv", usecols=["material_id"])["material_id"]
    val = pd.read_csv(RAW / "mp_20" / "val.csv", usecols=["material_id"])["material_id"]
    out_dir = run / "splits"; out_dir.mkdir()
    result = {"mp20_train": len(train), "mp20_val": len(val), "arms": {}}
    for part, full in (("train", train), ("val", val)):
        fam = ids(ABL / "removed_ids" / f"ABC2D6_{part}.csv")
        perov = ids(ABL / "removed_ids" / f"PEROV_{part}.csv")
        assert full.is_unique and fam <= set(full) and perov <= set(full), f"{part}: removed IDs not in MP-20"
        assert fam <= perov, f"{part}: ABC2D6 family is not contained in the PEROV removal"
        extra = perov - fam
        pool = sorted(set(full) - perov)  # neither the family nor a perovskite framework
        result["arms"].setdefault("ABC2D6", {})[part] = {"removed": len(fam), "remaining": len(full) - len(fam)}
        result["arms"].setdefault("PEROV", {})[part] = {"removed": len(perov), "extra_beyond_family": len(extra),
                                                       "remaining": len(full) - len(perov)}
        for arm, seed in PRE_REGISTERED["draw_seeds"].items():
            rng = np.random.default_rng(seed + (0 if part == "train" else 1_000_000))
            drawn = sorted(rng.choice(pool, size=len(extra), replace=False))
            removed = sorted(fam | set(drawn))
            body = pd.DataFrame({"material_id": removed}).to_csv(index=False).encode()
            (out_dir / f"{arm}_{part}_removed.csv").write_bytes(body)
            remaining = len(full) - len(removed)
            assert remaining == len(full) - len(perov), f"{arm} {part}: size not matched to PEROV"
            assert not set(drawn) & perov
            result["arms"].setdefault(arm, {})[part] = {"removed": len(removed), "random_extra": len(drawn),
                                                       "remaining": remaining, "removed_ids_sha256": sha256_bytes(body)}
    # Overlap between the random extras of the three draws (the shared family excluded; reported, not controlled)
    fam = ids(ABL / "removed_ids" / "ABC2D6_train.csv")
    tr = {a: set(pd.read_csv(out_dir / f"{a}_train_removed.csv").material_id) - fam for a in PRE_REGISTERED["draw_seeds"]}
    result["pairwise_overlap_random_extra_train"] = {f"{x}&{y}": len(tr[x] & tr[y]) for x in tr for y in tr if x < y}
    result["expected_overlap_if_independent"] = round(1268 * 1268 / (len(train) - 2819), 1)
    return result


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = ROOT / "results" / f"csp_random_control_{stamp}"
    run.mkdir(parents=True)
    (run / "config.json").write_text(json.dumps(PRE_REGISTERED, indent=2, ensure_ascii=False))

    s1 = step1_existing_arms(run)
    (run / "existing_arms.json").write_text(json.dumps(s1, indent=2))
    s2 = step2_splits(run)
    (run / "splits.json").write_text(json.dumps(s2, indent=2))

    inputs = [RAW / "MANIFEST.json", RAW / "mp_20" / "train.csv", RAW / "mp_20" / "val.csv",
              ABL / "ablation_per_target.csv", ABL / "ablation_summary.csv"] + sorted((ABL / "removed_ids").glob("*.csv"))
    write_provenance(run, "random_removal_control", inputs=inputs, seed=None, status="splits built; no training run",
                     note="draw seeds are in config.json")
    print(run.relative_to(ROOT))
    print(json.dumps({k: s1[k] for k in ("summary_recomputed_from_per_target", "consensus", "fit",
                                         "ABC2D6_to_PEROV_consensus_lost", "ABC2D6_to_PEROV_consensus_gained",
                                         "ABC2D6_to_PEROV_fit_lost", "ABC2D6_to_PEROV_fit_gained")}, indent=1))
    print(json.dumps(s2, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
