#!/usr/bin/env bash
# G0 runner check of the CSP random-removal control: sample, relax, score both seed-42 runs on this Mac.
#   1. sample.py   (EquiCSP env, CPU): 20 candidates per ABC2D6 target from the validation-selected checkpoint
#   2. relax.py    (ORB env, CPU):     ORB-v3 relaxation, energy-per-atom ranking, export rank01..rank20
#   3. score.py    (project env):      fit / consensus with the paper's matcher, on relaxed (primary) and raw candidates
# Usage (repository root):  bash src/csp/g0/run_g0.sh <out_dir>
set -euo pipefail
OUT=${1:?output dir}; ROOT=$(pwd); mkdir -p "$OUT"
REFS=${REFS:?set REFS to a folder holding the 11 T180 reference CIFs (data/testsets/v3.1/T180/cifs at benchmark commit 631c765)}
# validation-selected checkpoints (results/csp_g0_train_20261122T055536Z); macOS bash 3.2 has no associative arrays
ckpt() { case $1 in ABC2D6) echo "epoch=394-step=39499.ckpt";; PEROV) echo "epoch=364-step=34674.ckpt";; esac; }
for A in ABC2D6 PEROV; do
  mkdir -p "$OUT/$A"
  (cd data/raw/csp_g0 && PROJECT_ROOT=$ROOT/data/raw/equicsp_src ../equicsp_venv/bin/python "$ROOT/src/csp/g0/sample.py" \
     ${A}_s42 "$(ckpt $A)" "$ROOT/$OUT/$A/raw" 42 cpu 2>&1 | tr '\r' '\n' | grep -v 'it/s' > "$ROOT/$OUT/$A/sample.log") &
done
wait
for A in ABC2D6 PEROV; do
  # four relaxation workers per arm, split by target
  T=($(ls "$OUT/$A/raw" | grep '^mp-'))
  for w in 0 1 2 3; do
    S=(); for i in "${!T[@]}"; do [ $((i % 4)) -eq $w ] && S+=("${T[$i]}"); done
    data/raw/orb_venv/bin/python -I src/csp/g0/relax.py "$OUT/$A/raw" "$OUT/$A/relaxed" "${S[@]}" > "$OUT/$A/relax_w$w.log" 2>&1 &
  done
done
wait
for A in ABC2D6 PEROV; do
  .venv/bin/python -I src/csp/g0/score.py "$OUT/$A/relaxed" "$REFS" "$OUT/$A/score_relaxed.csv" > "$OUT/$A/score_relaxed.log" 2>&1
  .venv/bin/python -I src/csp/g0/score.py "$OUT/$A/raw" "$REFS" "$OUT/$A/score_raw.csv" > "$OUT/$A/score_raw.log" 2>&1
  echo "$A relaxed: $(tail -1 "$OUT/$A/score_relaxed.log") | raw: $(tail -1 "$OUT/$A/score_raw.log")"
done
