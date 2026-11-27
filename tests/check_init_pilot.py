"""Checks for the initial-structure pilot scripts on made-up inputs only (no model output).

Usage (repository root):  .venv/bin/python -I tests/check_init_pilot.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from csp.init_pilot_build import assignments, reduced_counts  # noqa: E402
from csp.init_pilot_collect import template_path  # noqa: E402
import pandas as pd  # noqa: E402
from csp.far_stage2_decide import somers_d  # noqa: E402
from csp.init_pilot_decide import outcome, with_template  # noqa: E402

bad = 0


def check(cond, msg):
    global bad
    bad += not cond
    print(("OK  " if cond else "FAIL"), msg)


# template paths follow the archive layout
check(template_path("AB2C10_0_spg69").parts[-3:] == ("3", "AB2C10", "AB2C10_0_spg69.cif"), "template path")
check(template_path("A_0_spg225").parts[-3] == "1", "one-element template")

# assignments preserve counts and enumerate ties
check(reduced_counts({"a": 2.0, "b": 4.0}) == {"a": 1, "b": 2}, "reduced counts")
m = assignments({"Xxa": 1, "Xxb": 2, "Xxc": 10}, {"Sr": 1, "Rh": 2, "Cd": 10})
check(m == [{"Xxa": "Sr", "Xxb": "Rh", "Xxc": "Cd"}], "no tie: one assignment")
m = assignments({"Xxa": 1, "Xxb": 1, "Xxc": 1, "Xxd": 7}, {"Cs": 1, "Hf": 1, "Cd": 1, "F": 7})
check(len(m) == 6 and all(x["Xxd"] == "F" for x in m), "three tied elements: 6 assignments, F fixed")
check(len({tuple(sorted(x.items())) for x in m}) == 6, "assignments are distinct")
m = assignments({"Xxa": 1, "Xxb": 1, "Xxc": 2, "Xxd": 2}, {"A": 1, "B": 1, "C": 2, "D": 2})
check(len(m) == 4, "two tied pairs: 2 x 2 assignments")
check(assignments({"Xxa": 1, "Xxb": 3}, {"A": 1, "B": 2}) == "counts differ from template", "count mismatch")

# rules, in order: fails, holds, partial
check(outcome(0.05, 0.19, 0.9, 0.1, 0.3) == "fails", "D(initial) upper < 0.2 fails")
check(outcome(0.3, 0.6, 0.9, -0.2, -0.01) == "fails", "d upper < 0 fails, even with good D")
check(outcome(0.3, 0.6, 0.8, 0.01, 0.3) == "holds", "all three lower bounds clear: holds")
check(outcome(0.3, 0.6, 0.79, 0.01, 0.3) == "partial", "p lower just below 0.8: partial")
check(outcome(0.2, 0.6, 0.9, 0.01, 0.3) == "partial", "D(initial) lower = 0.2 is not > 0.2: partial")
check(outcome(0.3, 0.6, 0.9, 0.0, 0.3) == "partial", "d lower = 0 is not > 0: partial")

# main analysis: entries with a template only; rank-last over all entries lowers D
df = pd.DataFrame({"has_template": [True, True, True, True, False, False],
                   "stable": [True, False, True, False, True, False],
                   "x": [0.0, 1.0, 0.1, 0.9, float("nan"), float("nan")]})
m = with_template(df)
check(len(m) == 4 and m.has_template.all(), "with_template keeps only entries with a template")
check(somers_d(m.stable.to_numpy(), m.x.to_numpy()) == 1.0, "perfect ranking on the template entries: D = 1")
check(somers_d(df.stable.to_numpy(), df.x.to_numpy()) < 1.0, "rank-last over all entries lowers D (sensitivity)")

# worker split: every entry once, order kept, load balanced
sys.path.insert(0, str(ROOT / "src/csp"))
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("relax", ROOT / "src/csp/init_pilot_relax.py")
relax = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(relax)
    recs = {f"e{n}": {"assignments": [{"structure": {"sites": [0] * s}}] * a}
            for n, (s, a) in enumerate([(80, 2), (10, 1), (10, 1), (12, 1), (50, 1), (8, 3)])}
    parts = relax.balance(list(recs), recs, 3)
    check(sorted(sum(parts, [])) == sorted(recs) and all(p == sorted(p, key=list(recs).index) for p in parts),
          "balance: each entry once, shuffled order kept")
    check(parts[0] == ["e0"], "balance: the heaviest entry gets a worker of its own here")
    check(relax.cost({"assignments": []}) == 0, "entry without a template costs nothing")
except ModuleNotFoundError as exc:  # far_stage2_relax needs the model environment
    print("SKIP balance checks:", exc)

print("ALL_OK" if bad == 0 else f"{bad} FAILED")
sys.exit(bad > 0)
