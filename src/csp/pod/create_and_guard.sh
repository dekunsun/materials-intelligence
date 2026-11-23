#!/usr/bin/env bash
# Retry pod creation (create_pod.sh, $0.30/h ceiling) and, the moment a pod exists, start its Mac-side
# watchdog at 11 h 55 min after creation, so no pod is ever left without a hard cap while waiting for capacity.
# Used for R2 and R3 on 2026-11-23, when A5000 Secure Cloud had no free capacity at first.
# Usage (repository root): POD_WORKDIR=<scratch> bash src/csp/pod/create_and_guard.sh RUN TRIES
#   then launch.sh and pod_monitor.sh as usual, with the pod id and epoch from $POD_WORKDIR/RUN/pod_id_epoch.txt
RUN=$1; TRIES=$2; D=${POD_WORKDIR:?set POD_WORKDIR to a scratch folder outside the repository}/$RUN
HERE=$(cd "$(dirname "$0")" && pwd)
bash "$HERE/create_pod.sh" "$RUN" 0.30 "$TRIES" | grep -v '^try ' ; rc=${PIPESTATUS[0]}
[ "$rc" -eq 0 ] || { echo "$RUN: not created (exit $rc)"; exit "$rc"; }
read -r POD E < <(python3 -c "import json,sys,datetime as d;j=json.load(open(sys.argv[1]));print(j['id'],int(d.datetime.fromisoformat(j['createdAt'].replace('Z','+00:00')).timestamp()))" "$D/created.json")
echo "$POD $E" > "$D/pod_id_epoch.txt"
nohup caffeinate -i bash "$HERE/watchdog.sh" "$POD" "$E" 42900 > "$D/watchdog.log" 2>&1 < /dev/null &
sleep 2; pgrep -f "watchdog.sh $POD" > /dev/null && echo "$RUN: pod $POD created $E, watchdog running"
