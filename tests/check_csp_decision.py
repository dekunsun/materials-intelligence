"""Boundary checks for src/csp/r_decision.py (the pre-registered rules of the CSP random-removal control).

Written before any R1-R3 result existed. The PEROV counts here are the real ones (3, 4, 4); the R counts
are made up to sit on each side of every threshold. Also runs the whole script end to end on a fake R folder
made of the three PEROV score files, which must come out as data_amount (difference 0).

Usage (repository root):  .venv/bin/python -I tests/check_csp_decision.py
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "csp"))
import r_decision as rd  # noqa: E402

P = [3, 4, 4]  # PEROV relaxed consensus, seeds 42, 43, 44
CASES = [  # (g0_pass, perov, r, expected)
    (True, P, [5, 5, 10], "template_specific"),   # every R > 4, sum 20: difference exactly 3
    (True, P, [5, 5, 9], "inconclusive"),         # sum 19: difference 8/3 < 3
    (True, P, [4, 8, 8], "inconclusive"),         # sum 20 but one R equals PEROV's best: not "every R beats"
    (True, P, [11, 11, 11], "template_specific"),
    (True, P, [5, 5, 5], "inconclusive"),         # sum 15: difference 4/3
    (True, P, [5, 5, 4], "data_amount"),          # sum 14: difference exactly 1
    (True, P, [3, 4, 4], "data_amount"),          # difference 0
    (True, P, [0, 1, 2], "data_amount"),          # R below PEROV is data_amount (A1)
    (True, [6, 6, 6], [11, 11, 11], "not_reproduced"),
    (True, [6, 6, 5], [11, 11, 11], "template_specific"),  # mean 17/3 < 6, so not_reproduced does not apply
    (False, P, [11, 11, 11], "stop_G0_failed"),
]


def main() -> int:
    bad = 0
    for g0, perov, r, want in CASES:
        got = rd.decide(g0, perov, r)["outcome"]
        ok = got == want
        bad += not ok
        print(("OK  " if ok else "FAIL"), f"G0={g0} PEROV={perov} R={r}: {got} (expected {want})")
    for r, want in [([5, 5, 5], "1/20"), ([4, 4, 4], "1/2"), ([3, 4, 4], "4/5")]:  # 16 of 20 relabelings reach 11
        got = rd.permutation_p(P, r)
        bad += got != want
        print(("OK  " if got == want else "FAIL"), f"permutation p, R={r}: {got} (expected {want})")

    with tempfile.TemporaryDirectory() as tmp:
        fake, out = Path(tmp) / "fake_r", Path(tmp) / "out"
        for r_run, p_run in zip(rd.R_RUNS, rd.PEROV_RUNS):
            (fake / r_run).mkdir(parents=True)
            for kind in ("relaxed", "raw"):
                shutil.copy(rd.PEROV_RUNS[p_run] / f"score_{kind}.csv", fake / r_run / f"score_{kind}.csv")
        rd.main(str(fake), str(out))
        d = json.load(open(out / "decision.json"))
        ok = d["decision"]["outcome"] == "data_amount" and d["decision"]["mean_R_minus_PEROV"] == "0"
        bad += not ok
        print(("OK  " if ok else "FAIL"), "end to end on PEROV copied as R: data_amount, difference 0")
    print("ALL_OK" if not bad else f"{bad} FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
