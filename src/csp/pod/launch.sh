#!/usr/bin/env bash
# Upload one run's bundle to its pod, build the environment, start the pod-side 12 h backstop, and start the
# 106,000-step training run detached. Same steps as G0 (which ran them from a scratch copy with seed 42 fixed).
# Usage: launch.sh RUN HOST PORT CREATED_EPOCH   (RUN = <ARM>_s<SEED>, e.g. PEROV_s43)
# Needs $POD_WORKDIR/id_g0 (throwaway key) and $POD_WORKDIR/<RUN>/bundle.tgz (from make_pod_bundle.sh).
set -euo pipefail
RUN=$1; HOST=$2; PORT=$3; E=$4
ARM=${RUN%_s*}; SEED=${RUN##*_s}
G=${POD_WORKDIR:?set POD_WORKDIR to a scratch folder outside the repository}; D=$G/$RUN
HERE=$(cd "$(dirname "$0")" && pwd)
OPTS="-i $G/id_g0 -o UserKnownHostsFile=$D/known_hosts -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20"
SSH="ssh $OPTS -p $PORT root@$HOST"
scp -q $OPTS -P "$PORT" "$D/bundle.tgz" "$HERE/backstop.sh" "root@$HOST:/workspace/"
$SSH "cd /workspace && sha256sum bundle.tgz && tar -xzf bundle.tgz && cd bundle && bash src/csp/pod_setup.sh > /workspace/setup.log 2>&1; echo setup_exit=\$?; tail -6 /workspace/setup.log; nproc; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"
$SSH "setsid nohup bash /workspace/backstop.sh $E > /dev/null 2>&1 < /dev/null & set -e; R=/workspace/out/$RUN; mkdir -p \$R; cp /workspace/setup.log \$R/; /root/.local/bin/uv pip freeze -p /workspace/venv > \$R/pip_freeze.txt 2>/dev/null; nvidia-smi > \$R/nvidia_smi.txt; cd /workspace/bundle; setsid nohup bash src/csp/pod_train.sh $ARM $SEED 106000 > \$R/train_log.txt 2>&1 < /dev/null & sleep 90; tail -3 \$R/train_log.txt; tail -2 \$R/steps.jsonl; pgrep -f backstop.sh > /dev/null && echo backstop=running"
