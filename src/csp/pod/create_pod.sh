#!/usr/bin/env bash
# Create one A5000 Secure Cloud pod for a G0 arm; retry while there is no capacity. Usage: create_pod.sh ARM TRIES   (A5000 on Secure Cloud, as used for G0)
ARM=$1; TRIES=${2:-20}
G=${POD_WORKDIR:?set POD_WORKDIR to a scratch folder outside the repository (it holds the throwaway SSH key and the copied outputs)}
api() { security find-generic-password -s runpod-api-key -w | sed 's/^/Authorization: Bearer /' | curl -s -m 60 -H @- "$@"; }
python3 -c "import json,sys;print(json.dumps({'name':'csp-g0-'+sys.argv[1].lower(),'cloud':'SECURE','gpu':{'id':'NVIDIA RTX A5000','count':1},'image':'runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04','disk':40,'ports':['22/tcp'],'env':{'PUBLIC_KEY':open(sys.argv[2]).read().strip()}}))" "$ARM" "$G/id_g0.pub" > "$G/$ARM/create.json"
for t in $(seq 1 "$TRIES"); do
  api -X POST -H 'Content-Type: application/json' -d @"$G/$ARM/create.json" https://api.runpod.io/v2/pods > "$G/$ARM/created.json"
  if python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if isinstance(d,dict) and d.get('id') else 1)" "$G/$ARM/created.json" 2>/dev/null; then
    python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('CREATED',d['id'],d['cloud'],d['gpu']['id'],'cost',d['cost'],'vcpu',d['gpu'].get('vcpuCount'),d['createdAt'])" "$G/$ARM/created.json"; exit 0
  fi
  echo "try $t: $(head -c 200 "$G/$ARM/created.json")"; sleep 30
done
exit 1
