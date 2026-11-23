"""Apply the pre-registered decision rules of the CSP random-removal control to the scored runs.

Written and committed on 2026-11-23, while R1-R3 were still training and before any R1-R3 candidate was
generated or scored, so that the analysis cannot be fitted to their results.

The rules are those of src/csp/random_removal_control.py (PRE_REGISTERED["decision_rules"]) with the order
fixed by amendment A1. The first rule that matches decides:
  1. G0_runner       our ABC2D6 and PEROV seed-42 consensus within 1 of the paper's 8 and 3 (checked in G0)
  2. not_reproduced  mean(PEROV) >= 6
  3. template_specific  every R run beats every PEROV run on consensus AND mean(R) - mean(PEROV) >= 3
  4. data_amount     mean(R) - mean(PEROV) <= 1 (this also covers R scoring below PEROV)
  5. inconclusive    anything else; no further runs without a new written decision
Means are compared as exact fractions, so a difference of exactly 3 or exactly 1 is not lost to rounding.

Primary metric: consensus on the relaxed, energy-ranked candidates (score_relaxed.csv). Two things are
reported but never decide anything, and are labelled that way in the output:
  - the same rules applied to the unrelaxed candidates (score_raw.csv): a sensitivity check, added because
    PEROV seed 44 scored consensus 2 unrelaxed and 4 relaxed (not pre-registered);
  - the exact one-sided permutation p-value of the 3-vs-3 consensus counts (the pre-registration's note:
    its smallest possible value is 1/20 = 0.05).

Usage (repository root):
    .venv/bin/python -I src/csp/r_decision.py <R eval dir> <out dir>
The R eval dir holds R1_s42/, R2_s43/, R3_s44/ from src/csp/g0/run_eval.sh. PEROV runs are read from the
committed G0 and PEROV-seed result folders below. Writes <out dir>/decision.json and
<out dir>/per_target_all_runs.csv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G0 = ROOT / "results" / "csp_g0_score_20261122T174350Z"
PEROV_EVAL = ROOT / "results" / "csp_perov_seeds_eval_20261123T1025Z"
PEROV_RUNS = {"PEROV_s42": G0 / "PEROV", "PEROV_s43": PEROV_EVAL / "PEROV_s43", "PEROV_s44": PEROV_EVAL / "PEROV_s44"}
R_RUNS = ["R1_s42", "R2_s43", "R3_s44"]
TARGETS = ["mp-6231", "mp-19093", "mp-19274", "mp-6389", "mp-16307", "mp-557387", "mp-6603", "mp-1215245",
           "mp-10321", "mp-12449", "mp-556434"]
N_CANDIDATES = 20


def decide(g0_pass: bool, perov: list[int], r: list[int]) -> dict:
    """The pre-registered rules, in A1 order. Inputs are per-run consensus counts (0-11)."""
    mp, mr = Fraction(sum(perov), len(perov)), Fraction(sum(r), len(r))
    diff = mr - mp
    checks = {
        "G0_runner": g0_pass,
        "not_reproduced": mp >= 6,
        "every_R_beats_every_PEROV": min(r) > max(perov),
        "mean_diff_ge_3": diff >= 3,
        "mean_diff_le_1": diff <= 1,
    }
    if not g0_pass:
        outcome = "stop_G0_failed"
    elif checks["not_reproduced"]:
        outcome = "not_reproduced"
    elif checks["every_R_beats_every_PEROV"] and checks["mean_diff_ge_3"]:
        outcome = "template_specific"
    elif checks["mean_diff_le_1"]:
        outcome = "data_amount"
    else:
        outcome = "inconclusive"
    return {"outcome": outcome, "mean_PEROV": str(mp), "mean_R": str(mr), "mean_R_minus_PEROV": str(diff),
            "mean_R_minus_PEROV_float": round(float(diff), 3), "checks": checks}


def permutation_p(perov: list[int], r: list[int]) -> str:
    """Exact one-sided p for 'R higher than PEROV': share of the 20 relabelings with sum(R) >= observed."""
    pooled, obs = perov + r, sum(r)
    splits = list(combinations(range(len(pooled)), len(r)))
    hits = sum(sum(pooled[i] for i in s) >= obs for s in splits)
    return str(Fraction(hits, len(splits)))


def read_scores(path: Path) -> dict:
    rows = {row["material_id"]: row for row in csv.DictReader(open(path))}
    problems = [t for t in TARGETS if t not in rows] + [
        f"{t}: {rows[t]['n_files']} files, {rows[t]['n_read']} read" for t in TARGETS
        if t in rows and (int(rows[t]["n_files"]) != N_CANDIDATES or int(rows[t]["n_read"]) != N_CANDIDATES)]
    if problems or set(rows) != set(TARGETS):
        raise SystemExit(f"{path}: not a complete 11-target, 20-candidate score: {problems or sorted(rows)}")
    return rows


def main(r_eval: str, out: str) -> int:
    r_eval, out = Path(r_eval), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    g0 = json.load(open(G0 / "config.json"))
    g0_pass = g0["verdict"] == "PASS"
    runs = {**PEROV_RUNS, **{k: r_eval / k for k in R_RUNS}}
    scores = {kind: {k: read_scores(d / f"score_{kind}.csv") for k, d in runs.items()} for kind in ("relaxed", "raw")}
    count = lambda kind, k, field: sum(scores[kind][k][t][field] == "True" for t in TARGETS)

    result = {"what": "Pre-registered decision of the CSP random-removal control (src/csp/r_decision.py)",
              "primary": "consensus on relaxed candidates", "inputs": {}, "runs": {}}
    for kind in ("relaxed", "raw"):
        for k, d in runs.items():
            p = d / f"score_{kind}.csv"
            rel = str(p.resolve().relative_to(ROOT)) if p.resolve().is_relative_to(ROOT) else str(p.resolve())
            result["inputs"][f"{k}/{p.name}"] = {"path": rel,
                                                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    for k in runs:
        result["runs"][k] = {f"{kind}_{f}": count(kind, k, f) for kind in ("relaxed", "raw") for f in ("consensus", "fit")}

    cons = lambda kind, ks: [count(kind, k, "consensus") for k in ks]
    perov_keys = list(PEROV_RUNS)
    result["decision"] = decide(g0_pass, cons("relaxed", perov_keys), cons("relaxed", R_RUNS))
    result["sensitivity_raw_not_deciding"] = decide(g0_pass, cons("raw", perov_keys), cons("raw", R_RUNS))
    fit = lambda ks: [count("relaxed", k, "fit") for k in ks]
    result["secondary_fit_relaxed_not_deciding"] = {"PEROV": fit(perov_keys), "R": fit(R_RUNS),
                                                    "mean_R_minus_PEROV": round(float(Fraction(sum(fit(R_RUNS)), 3) - Fraction(sum(fit(perov_keys)), 3)), 3)}
    result["permutation_p_one_sided_not_deciding"] = {
        "relaxed_consensus": permutation_p(cons("relaxed", perov_keys), cons("relaxed", R_RUNS)),
        "note": "3 vs 3 runs: the smallest possible value is 1/20 = 0.05 (pre-registration note)"}

    with open(out / "per_target_all_runs.csv", "w", newline="") as f:
        cols = ["material_id"] + [f"{k}_{f}" for k in runs for f in ("consensus", "fit", "rank")] + \
               ["PEROV_consensus_runs", "R_consensus_runs"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for t in TARGETS:
            row = {"material_id": t}
            for k in runs:
                s = scores["relaxed"][k][t]
                row.update({f"{k}_consensus": s["consensus"], f"{k}_fit": s["fit"], f"{k}_rank": s["first_match_rank"]})
            row["PEROV_consensus_runs"] = sum(scores["relaxed"][k][t]["consensus"] == "True" for k in perov_keys)
            row["R_consensus_runs"] = sum(scores["relaxed"][k][t]["consensus"] == "True" for k in R_RUNS)
            w.writerow(row)
    (out / "decision.json").write_text(json.dumps(result, indent=1))
    d = result["decision"]
    print(f"PEROV consensus {cons('relaxed', perov_keys)} | R consensus {cons('relaxed', R_RUNS)} | "
          f"mean diff {d['mean_R_minus_PEROV']} -> {d['outcome']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
