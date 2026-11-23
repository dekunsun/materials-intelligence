"""Independent check of the R1-R3 training data of the CSP random-removal control against the pre-registration.

Run on 2026-11-23 before R1-R3 training (all checks passed). Checks, for train and val:
  - the R CSVs match data/raw/equicsp_data/MANIFEST.json and the committed removed-ID lists
    (results/csp_random_control_20261121T223433Z/splits/);
  - each R arm removes the ABC2D6 family plus exactly as many extra structures as PEROV, none of them in the
    PEROV lists, leaving the same number of rows as PEROV; the test split is the same in every arm;
  - the draws are reproduced byte for byte from the pre-registered draw seeds (same code as
    src/csp/random_removal_control.py step2_splits).
The preprocessed caches (*_ori.pt) were checked separately in the EquiCSP environment: row order equals the
CSV for every R arm and split. Needs data/raw (gitignored; see src/csp/fetch_csp_ablation.py).

Usage (repository root):  .venv/bin/python -I tests/check_csp_r_data.py
"""
import hashlib, json, sys
import pandas as pd
from pathlib import Path
M = Path("data/raw/csp_ablation"); D = Path("data/raw/equicsp_data")
S = Path("results/csp_random_control_20261121T223433Z/splits")
man = json.load(open(D / "MANIFEST.json"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ids = lambda p: list(pd.read_csv(p)["material_id"])
# the full MP-20 split: the ABC2D6 arm CSV plus its removed list
rm = {(a, p): set(ids(M / f"benchmark/ablation/removed_ids/{a}_{p}.csv")) for a in ["ABC2D6", "PEROV"] for p in ["train", "val"]}
ok = True
def chk(cond, msg):
    global ok; ok &= bool(cond); print(("OK  " if cond else "FAIL"), msg)
for p in ["train", "val"]:
    full = set(ids(D / f"ABC2D6/{p}.csv")) | rm[("ABC2D6", p)]
    chk(len(full) == {"train": 27136, "val": 9047}[p], f"{p}: full MP-20 size {len(full)}")
    chk(rm[("ABC2D6", p)] <= rm[("PEROV", p)], f"{p}: PEROV list contains the ABC2D6 family")
    perov_extra = rm[("PEROV", p)] - rm[("ABC2D6", p)]
    extras = {}
    for a in ["R1", "R2", "R3"]:
        f = D / f"{a}/{p}.csv"
        chk(sha(f) == man["arms"][a][p]["csv_sha256"], f"{a} {p}.csv hash matches MANIFEST")
        keep = ids(f); removed = full - set(keep)
        chk(len(keep) == len(set(keep)), f"{a} {p}: no duplicate rows")
        chk(set(keep) <= full, f"{a} {p}: rows all from MP-20")
        committed = set(ids(S / f"{a}_{p}_removed.csv"))
        chk(removed == committed, f"{a} {p}: removed set equals committed split list ({len(committed)})")
        chk(rm[("ABC2D6", p)] <= removed, f"{a} {p}: ABC2D6 family removed")
        x = removed - rm[("ABC2D6", p)]; extras[a] = x
        chk(len(x) == len(perov_extra), f"{a} {p}: random extra {len(x)} = PEROV extra {len(perov_extra)}")
        chk(not (x & perov_extra), f"{a} {p}: random extra disjoint from PEROV lists")
        chk(len(keep) == len(full) - len(rm[("PEROV", p)]), f"{a} {p}: size equals PEROV {len(keep)}")
    for a, b in [("R1", "R2"), ("R1", "R3"), ("R2", "R3")]:
        print(f"     {p}: {a}&{b} overlap of random extras = {len(extras[a] & extras[b])}")
    # test split untouched
t = [sha(D / f"{a}/test.csv") for a in ["ABC2D6", "PEROV", "R1", "R2", "R3"]]
chk(len(set(t)) == 1, "test.csv identical in all arms")

import numpy as np
for p in ["train", "val"]:
    full = pd.read_csv(M / f"mp_20/{p}.csv", usecols=["material_id"])["material_id"]
    fam, perov = rm[("ABC2D6", p)], rm[("PEROV", p)]
    pool = sorted(set(full) - perov)
    for a, s in {"R1": 2026112101, "R2": 2026112102, "R3": 2026112103}.items():
        rng = np.random.default_rng(s + (0 if p == "train" else 1_000_000))
        drawn = sorted(rng.choice(pool, size=len(perov - fam), replace=False))
        body = pd.DataFrame({"material_id": sorted(fam | set(drawn))}).to_csv(index=False).encode()
        chk(body == (S / f"{a}_{p}_removed.csv").read_bytes(), f"{a} {p}: draw reproduced from seed {s}")
print("ALL_OK" if ok else "SOME_FAIL")
sys.exit(0 if ok else 1)
