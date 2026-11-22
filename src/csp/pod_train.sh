#!/usr/bin/env bash
# Train one arm/seed on a pod with the pre-registered EquiCSP recipe (see src/csp/random_removal_control.py).
# Run from the unpacked bundle after src/csp/pod_setup.sh:
#     bash src/csp/pod_train.sh PEROV 42 106000      # full run
#     bash src/csp/pod_train.sh PEROV 42 1000        # smoke test
# Writes /workspace/out/<ARM>_s<SEED>/: steps.jsonl (time per step), gpu_util.csv, Hydra run dir,
# started_at / finished_at / exit_code.
set -uo pipefail
ARM=${1:?arm}; SEED=${2:?seed}; STEPS=${3:?max optimiser steps}
export LC_ALL=C.UTF-8
B=$(cd "$(dirname "$0")/../.." && pwd)
O=/workspace/out/${ARM}_s${SEED}; mkdir -p "$O"
export PROJECT_ROOT=$B/equicsp_src HYDRA_JOBS=$O WABDB_DIR=$O STEP_LOG=$O/steps.jsonl
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used --format=csv -l 15 > "$O/gpu_util.csv" 2>&1 &
SMI=$!
date -u +%FT%TZ > "$O/started_at"
cd "$B"
/workspace/venv/bin/python src/csp/equicsp_train.py expname="${ARM}_s${SEED}" \
  data.root_path="$B/data/$ARM" \
  data.datamodule.batch_size.train=64 train.pl_trainer.accumulate_grad_batches=4 \
  train.random_seed="$SEED" data.train_max_epochs=2000 +train.pl_trainer.max_steps="$STEPS"
echo "exit $?" > "$O/exit_code"
date -u +%FT%TZ > "$O/finished_at"
kill $SMI
