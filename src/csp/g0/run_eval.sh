#!/usr/bin/env bash
# Sample, relax and score any trained runs on this Mac, with the same steps and settings as G0 (run_g0.sh).
#   1. sample.py (EquiCSP env, CPU): 20 candidates per ABC2D6 target; sampling seed = the run's training seed (A1)
#   2. relax.py  (ORB env, CPU):     ORB-v3 relaxation, energy-per-atom ranking, export rank01..rank20
#   3. score.py  (project env):      fit / consensus, on relaxed (primary) and raw candidates
# The checkpoint is the run's single validation-selected epoch=*.ckpt in data/raw/csp_g0/<RUN>/ (never last.ckpt).
# Usage (repository root):  REFS=<11 T180 reference CIFs> bash src/csp/g0/run_eval.sh <out_dir> <RUN> [<RUN> ...]
#   RUN = <ARM>_s<SEED>, e.g. PEROV_s43
set -euo pipefail
OUT=${1:?output dir}; shift; RUNS=("$@"); [ ${#RUNS[@]} -gt 0 ] || { echo "no runs given" >&2; exit 1; }
ROOT=$(pwd); mkdir -p "$OUT"
REFS=${REFS:?set REFS to a folder holding the 11 T180 reference CIFs (data/testsets/v3.1/T180/cifs at benchmark commit 631c765)}
for R in "${RUNS[@]}"; do
  n=$(ls data/raw/csp_g0/$R/ | grep -c '^epoch=.*\.ckpt$' || true)
  [ "$n" -eq 1 ] || { echo "$R: expected one epoch=*.ckpt, found $n" >&2; exit 1; }
done
for R in "${RUNS[@]}"; do
  C=$(ls data/raw/csp_g0/$R/ | grep '^epoch=.*\.ckpt$'); SEED=${R##*_s}; mkdir -p "$OUT/$R"
  (cd data/raw/csp_g0 && PROJECT_ROOT=$ROOT/data/raw/equicsp_src ../equicsp_venv/bin/python "$ROOT/src/csp/g0/sample.py" \
     "$R" "$C" "$ROOT/$OUT/$R/raw" "$SEED" cpu 2>&1 | tr '\r' '\n' | grep -v 'it/s' > "$ROOT/$OUT/$R/sample.log") &
done
wait
for R in "${RUNS[@]}"; do
  T=($(ls "$OUT/$R/raw" | grep '^mp-'))
  for w in 0 1 2 3; do
    S=(); for i in "${!T[@]}"; do [ $((i % 4)) -eq $w ] && S+=("${T[$i]}"); done
    data/raw/orb_venv/bin/python -I src/csp/g0/relax.py "$OUT/$R/raw" "$OUT/$R/relaxed" "${S[@]}" > "$OUT/$R/relax_w$w.log" 2>&1 &
  done
done
wait
for R in "${RUNS[@]}"; do
  .venv/bin/python -I src/csp/g0/score.py "$OUT/$R/relaxed" "$REFS" "$OUT/$R/score_relaxed.csv" > "$OUT/$R/score_relaxed.log" 2>&1
  .venv/bin/python -I src/csp/g0/score.py "$OUT/$R/raw" "$REFS" "$OUT/$R/score_raw.csv" > "$OUT/$R/score_raw.log" 2>&1
  echo "$R relaxed: $(tail -1 "$OUT/$R/score_relaxed.log") | raw: $(tail -1 "$OUT/$R/score_raw.log")"
done
