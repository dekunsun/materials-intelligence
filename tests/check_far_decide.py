"""Checks for src/csp/far_split.py and src/csp/far_decide.py on made-up inputs only.

Written before any per-cell model metric existed; touches no real prediction. Covers the framework key, the
normalised score, the reweighted interpolation reference, and every boundary of the ordered decision rules.

Usage (repository root):  .venv/bin/python -I tests/check_far_decide.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from csp.far_decide import cell_nrp, nrp, outcome, ref_nrp  # noqa: E402
from csp.far_split import framework  # noqa: E402

bad = 0


def check(cond, msg):
    global bad
    bad += not cond
    print(("OK  " if cond else "FAIL"), msg)


# framework key: element grouping ignored, letters and multiplicities kept
check(framework("A2BC_cF16_225_c_a_b:Ag-Ba-La") == "cF16_225_abc", "framework of A2BC_cF16_225_c_a_b")
check(framework("AB2_mP12_13_af_2g:Ag-Te") == "mP12_13_afgg", "framework with a multiplicity (2g)")
check(framework("A3B_hP8_194_h_c:Ac-U") == framework("AB3_hP8_194_c_h:U-Ac"), "same framework, elements swapped")
check(framework(None) is None, "missing label")

# normalised score
check(nrp(0.15, 0.15) == 0 and nrp(1.0, 0.15) == 1, "NRp: random 0, perfect 1")
true = np.array([-0.1, -0.2, 0.3, 0.4, 0.5, 0.6])           # 2 stable of 6
check(abs(cell_nrp(true, true) - 1) < 1e-12, "perfect ranking scores 1")
check(abs(cell_nrp(true, -true) - nrp(0.0, 2 / 6)) < 1e-12, "inverted ranking scores the floor")

# reweighted reference: stratum 2 is ranked perfectly, stratum 3 inversely; weights decide the blend
t2 = np.array([-0.1, 0.2, 0.3, 0.4]); t3 = np.array([-0.1, 0.2, 0.3, 0.4])
ti = np.concatenate([t2, t3]); pi = np.concatenate([t2, -t3]); ni = np.array([2] * 4 + [3] * 4)
check(abs(ref_nrp(ti, pi, ni, {2: 1.0}) - 1) < 1e-12, "reference with all weight on the perfect stratum")
check(abs(ref_nrp(ti, pi, ni, {3: 1.0}) - nrp(0.0, 0.25)) < 1e-12, "reference with all weight on the inverted stratum")
check(abs(ref_nrp(ti, pi, ni, {2: 0.5, 3: 0.5}) - nrp(0.5, 0.25)) < 1e-12, "reference with equal weights")
check(abs(ref_nrp(ti, pi, ni, {2: 0.5, 5: 0.5}) - 1) < 1e-12, "a stratum absent from interpolation is dropped")

# ordered rules: (stable, frameworks_with_stable, r_lo, r_hi, d_lo, d_hi) -> outcome
CASES = [
    ((49, 30, 0.9, 1.0, 0.2, 0.3), "too_small"),   # stable below 50
    ((80, 19, 0.9, 1.0, 0.2, 0.3), "too_small"),   # frameworks below 20
    ((50, 20, 0.9, 1.0, 0.2, 0.3), "holds"),       # exactly at both minimums
    ((80, 30, 0.3, 0.49, 0.2, 0.3), "fails"),      # r upper just below 0.5
    ((80, 30, 0.3, 0.50, 0.2, 0.3), "partial"),    # r upper exactly 0.5 is not a fail
    ((80, 30, 0.9, 1.0, 0.05, 0.099), "fails"),    # d upper below 0.10, even though r would hold
    ((80, 30, 0.80, 1.0, 0.11, 0.3), "holds"),     # r lower exactly 0.8
    ((80, 30, 0.79, 1.0, 0.11, 0.3), "partial"),   # r lower just below 0.8
    ((80, 30, 0.9, 1.0, 0.10, 0.3), "partial"),    # d lower exactly 0.10 is not above the margin
    ((80, 30, 0.6, 0.9, 0.0, 0.3), "partial"),
]
for args, want in CASES:
    got = outcome(*args)
    check(got == want, f"outcome{args} = {got} (expected {want})")

print("ALL_OK" if not bad else f"{bad} FAILED")
sys.exit(1 if bad else 0)
