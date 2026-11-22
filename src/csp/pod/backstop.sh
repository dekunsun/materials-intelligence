#!/usr/bin/env bash
# On the pod: remove this pod at CREATED_EPOCH + 12 h, in case the Mac-side monitor and watchdog never run
# (e.g. the Mac sleeps). Uses the pod's own RunPod-injected credentials from PID 1's environment; nothing is printed.
END=$(( $1 + 43200 ))
while [ "$(date +%s)" -lt "$END" ]; do sleep 60; done
eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(API_KEY|POD_ID)=' | sed "s/^\([A-Z_]*\)=\(.*\)$/export \1='\2'/")"
runpodctl remove pod "$RUNPOD_POD_ID" > /workspace/backstop.log 2>&1
