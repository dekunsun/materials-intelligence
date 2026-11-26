"""Checks for src/csp/far_stage2_decide.py and far_stage2_sample.py on made-up inputs only (no model output).

Usage (repository root):  .venv/bin/python -I tests/check_far_stage2.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from csp.far_stage2_decide import combine, outcome, somers_d  # noqa: E402
from csp.far_stage2_sample import draw_matched, eligible  # noqa: E402

bad = 0


def check(cond, msg):
    global bad
    bad += not cond
    print(("OK  " if cond else "FAIL"), msg)


# Somers' D: lower prediction = more stable
st = np.array([True, True, False, False])
check(somers_d(st, np.array([0.0, 0.01, 0.05, 0.08])) == 1, "perfect ranking gives 1")
check(somers_d(st, np.array([0.08, 0.05, 0.01, 0.0])) == -1, "inverted ranking gives -1")
check(somers_d(st, np.array([0.0, 0.0, 0.0, 0.0])) == 0, "all ties give 0")
check(somers_d(st, np.array([0.0, np.nan, 0.05, 0.08])) == 0, "a failed stable entry ranks last")
check(abs(somers_d(st, np.array([0.0, 0.06, 0.05, 0.08])) - 0.5) < 1e-12, "one discordant pair of four gives 0.5")
rng = np.random.default_rng(0)
s = rng.random(4000) < 0.3; p = rng.random(4000)
check(abs(somers_d(s, p)) < 0.05, "random predictions give about 0")

# ordered rules: (stable, frameworks_with_stable, r_lo, r_hi, d_lo, d_hi)
CASES = [
    ((49, 30, 0.9, 1.0, 0.5, 0.6), "too_small"),
    ((80, 19, 0.9, 1.0, 0.5, 0.6), "too_small"),
    ((50, 20, 0.9, 1.0, 0.5, 0.6), "holds"),
    ((80, 30, 0.3, 0.49, 0.5, 0.6), "fails"),
    ((80, 30, 0.3, 0.50, 0.5, 0.6), "partial"),
    ((80, 30, 0.9, 1.0, 0.1, 0.19), "fails"),     # D upper below 0.2 although r would hold
    ((80, 30, 0.80, 1.0, 0.21, 0.6), "holds"),
    ((80, 30, 0.79, 1.0, 0.21, 0.6), "partial"),
    ((80, 30, 0.9, 1.0, 0.20, 0.6), "partial"),   # D lower exactly 0.2 is not above it
]
for args, want in CASES:
    check(outcome(*args) == want, f"outcome{args} = {outcome(*args)} (expected {want})")
check(combine("holds", "fails") == "partial" and combine("fails", "holds") == "partial", "disagreeing strata -> partial")
check(combine("holds", "partial") == "holds" and combine("holds", "too_small") == "holds", "otherwise the main stands")

# sampling: eligibility and matched element counts
pool = pd.DataFrame({"mat_id": list("abcdefg"), "plus_u": [0, 1, 0, 0, 0, 0, 0], "in_wbm": [0, 0, 1, 0, 0, 0, 0],
                     "framework": ["x", "x", "x", None, "x", "x", "x"], "chem_familiar": [1, 1, 1, 1, 1, 0, 1],
                     "framework_known": [1, 1, 1, 1, 0, 0, 1], "e_hull": [0.0, 0, 0, 0, 0.03, 0.5, -0.01]})
pool[["plus_u", "in_wbm", "chem_familiar", "framework_known"]] = pool[["plus_u", "in_wbm", "chem_familiar",
                                                                       "framework_known"]].astype(bool)
e = eligible(pool)
check(list(e.mat_id) == ["a", "e", "g"], "eligible drops +U, WBM overlap, missing framework, e_hull > 0.1")
check(list(e.stratum) == ["stable", "bin1", "stable"] and e.cell.iloc[1] == "structural_extrapolation", "strata and cells")
edges = pool.iloc[[0] * 5].assign(mat_id=list("vwxyz"), e_hull=[0.001, 0.025, 0.0251, 0.075, 0.1])
check(list(eligible(edges).stratum) == ["bin0", "bin0", "bin1", "bin2", "bin3"], "bin edges are right-closed")
g = pd.DataFrame({"n_elements": [2] * 100 + [3] * 100})
m = draw_matched(g, pd.Series({2: 0.25, 3: 0.75}), 40, np.random.default_rng(1))
check((m.n_elements == 2).sum() == 10 and (m.n_elements == 3).sum() == 30, "matched draw follows the target mix")

print("ALL_OK" if not bad else f"{bad} FAILED")
sys.exit(1 if bad else 0)
