#!/usr/bin/env bash
# Hard cap: DELETE the pod at CREATED + SECONDS, whatever the monitor did. Usage: watchdog.sh POD CREATED_EPOCH SECONDS
POD=$1; END=$(( $2 + $3 ))
while [ "$(date +%s)" -lt "$END" ]; do sleep 60; done
security find-generic-password -s runpod-api-key -w | sed 's/^/Authorization: Bearer /' | curl -s -m 30 -o /dev/null -w "watchdog DELETE $POD -> %{http_code}\n" -H @- -X DELETE "https://api.runpod.io/v2/pods/$POD"
