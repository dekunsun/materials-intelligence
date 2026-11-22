#!/usr/bin/env bash
# Create one A5000 Secure Cloud pod for one training run; retry while there is no capacity. A5000 on Secure Cloud, as used for G0.
# Usage: create_pod.sh RUN MAX_PRICE_PER_HOUR [TRIES]   (RUN = <ARM>_s<SEED>, e.g. PEROV_s43)
# If the created pod's hourly price is above MAX_PRICE_PER_HOUR it is deleted at once and the script fails.
RUN=$1; MAX=${2:?maximum price per hour in USD}; TRIES=${3:-20}
G=${POD_WORKDIR:?set POD_WORKDIR to a scratch folder outside the repository (it holds the throwaway SSH key and the copied outputs)}
api() { security find-generic-password -s runpod-api-key -w | sed 's/^/Authorization: Bearer /' | curl -s -m 60 -H @- "$@"; }
python3 -c "import json,sys;print(json.dumps({'name':'csp-'+sys.argv[1].lower().replace('_','-'),'cloud':'SECURE','gpu':{'id':'NVIDIA RTX A5000','count':1},'image':'runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04','disk':40,'ports':['22/tcp'],'env':{'PUBLIC_KEY':open(sys.argv[2]).read().strip()}}))" "$RUN" "$G/id_g0.pub" > "$G/$RUN/create.json"
for t in $(seq 1 "$TRIES"); do
  api -X POST -H 'Content-Type: application/json' -d @"$G/$RUN/create.json" https://api.runpod.io/v2/pods > "$G/$RUN/created.json"
  if python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if isinstance(d,dict) and d.get('id') else 1)" "$G/$RUN/created.json" 2>/dev/null; then
    python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('CREATED',d['id'],d['cloud'],d['gpu']['id'],'cost',d['cost'],'vcpu',d['gpu'].get('vcpuCount'),d['createdAt'])" "$G/$RUN/created.json"
    if python3 -c "import json,sys;sys.exit(0 if float(json.load(open(sys.argv[1]))['cost'])<=float(sys.argv[2]) else 1)" "$G/$RUN/created.json" "$MAX"; then exit 0; fi
    id=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['id'])" "$G/$RUN/created.json")
    echo "PRICE ABOVE $MAX/h: deleting $id -> HTTP $(api -o /dev/null -w '%{http_code}' -X DELETE "https://api.runpod.io/v2/pods/$id")"; exit 2
  fi
  echo "try $t: $(head -c 200 "$G/$RUN/created.json")"; sleep 30
done
exit 1
