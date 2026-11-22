#!/usr/bin/env bash
# Watch one G0 training pod from the Mac: copy logs back every 10 min and checkpoints every hour;
# when the run writes exit_code (or the time cap is reached) do a final full copy, then terminate
# the pod and confirm it is gone. The API key is read from the Keychain and piped as a header only.
# Needs: the throwaway key $POD_WORKDIR/id_g0; data under $POD_WORKDIR/<RUN>/.
# Usage: pod_monitor.sh RUN POD_ID SSH_HOST SSH_PORT CREATED_EPOCH CAP_HOURS   (RUN = <ARM>_s<SEED>, e.g. PEROV_s43)
# G0 used ARM in place of RUN with seed 42 fixed; results/csp_g0_train_20261122T055536Z was made that way.
set -u
RUN=$1; POD=$2; HOST=$3; PORT=$4; CREATED=$5; CAP_H=$6
G=${POD_WORKDIR:?set POD_WORKDIR to a scratch folder outside the repository (it holds the throwaway SSH key and the copied outputs)}; D=$G/$RUN; mkdir -p "$D/pulled"
LOG=$D/monitor.log
SSH="ssh -i $G/id_g0 -o UserKnownHostsFile=$D/known_hosts -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=30 -p $PORT root@$HOST"
api() { security find-generic-password -s runpod-api-key -w | sed 's/^/Authorization: Bearer /' | curl -s -m 30 -H @- "$@"; }
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
pull_logs() { $SSH "cd /workspace/out && tar -cf - --exclude='*.ckpt' $RUN" 2>>"$LOG" | tar -xf - -C "$D/pulled" 2>>"$LOG"; }
pull_all() { $SSH "cd /workspace/out && tar -cf - $RUN" 2>>"$LOG" | tar -xf - -C "$D/pulled" 2>>"$LOG"; }
terminate() {
  code=$(api -o /dev/null -w '%{http_code}' -X DELETE "https://api.runpod.io/v2/pods/$POD")
  log "DELETE pod $POD -> HTTP $code"
  sleep 20
  left=$(api "https://api.runpod.io/v2/pods" | python3 -c "import json,sys;print([p['id'] for p in json.load(sys.stdin)['pods']])" 2>&1)
  log "pods left on account: $left"
  date -u +%FT%TZ > "$D/terminated_at.txt"
}
log "monitor start pod=$POD host=$HOST:$PORT cap=${CAP_H}h"
i=0
while true; do
  now=$(date +%s)
  if [ $((now - CREATED)) -ge $((CAP_H * 3600)) ]; then
    log "time cap reached; final copy, then terminate"; pull_all; terminate; exit 0
  fi
  if [ $((i % 6)) -eq 0 ]; then pull_all; else pull_logs; fi
  i=$((i + 1))
  last=$(tail -1 "$D/pulled/$RUN/steps.jsonl" 2>/dev/null)
  log "copied; last step record: $last"
  if [ -f "$D/pulled/$RUN/exit_code" ]; then
    log "run finished: $(cat "$D/pulled/$RUN/exit_code"); final copy"
    pull_all
    # Every checkpoint still on the pod must be on the Mac with the same SHA-256. (The first version compared
    # full listings, which never matched: save_top_k=1 deletes superseded best checkpoints on the pod, while the
    # hourly copies keep them here. That kept both G0 pods running until the 11 h cap.)
    remote=$($SSH "cd /workspace/out/$RUN && find . -name '*.ckpt' -exec sha256sum {} \\;" 2>>"$LOG" | sort)
    missing=$(cd "$D/pulled/$RUN" && echo "$remote" | while read -r h f; do [ -n "$h" ] && [ "$(shasum -a 256 "$f" 2>/dev/null | cut -d' ' -f1)" != "$h" ] && echo "$f"; done)
    if [ -n "$remote" ] && [ -z "$missing" ]; then log "all pod checkpoints copied, SHA-256 match:"; echo "$remote" >> "$LOG"
      terminate; exit 0
    fi
    log "WARNING not yet copied or hash differs: [$missing]; pod kept until the next check or the cap"
  fi
  sleep 600
done
