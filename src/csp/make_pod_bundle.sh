#!/usr/bin/env bash
# Pack what a rented GPU pod needs to train one arm of the CSP random-removal control:
# the EquiCSP source at the pinned commit (without its bundled datasets), this project's training
# wrapper and setup script, and the arm's prepared data from src/csp/equicsp_prepare_arms.py.
# Usage (from the repository root):  bash src/csp/make_pod_bundle.sh PEROV /path/to/outdir
# Then on the pod: tar -xzf bundle.tgz && cd bundle && bash src/csp/pod_setup.sh
set -euo pipefail
ARM=${1:?arm name, e.g. PEROV}; OUT=${2:?output directory}
B="$OUT/bundle"; rm -rf "$B"; mkdir -p "$B/src/csp" "$B/data/$ARM" "$B/equicsp_src"
cp src/csp/pod_setup.sh src/csp/pod_train.sh src/csp/equicsp_train.py src/csp/requirements-equicsp.txt "$B/src/csp/"
cp data/raw/equicsp_data/"$ARM"/* "$B/data/$ARM/"
cp data/raw/equicsp_data/MANIFEST.json "$B/data/equicsp_data_MANIFEST.json"
cp data/raw/csp_ablation/MANIFEST.json "$B/data/csp_ablation_MANIFEST.json"
# Exclude only the top-level data/ folder of EquiCSP; conf/data/ holds the dataset configs and is needed.
(cd data/raw/equicsp_src && git archive HEAD -- . ':(exclude,top)data' | tar -x -C "$B/equicsp_src")
test -f "$B/equicsp_src/conf/data/mp_20.yaml" || { echo "conf/data missing from bundle" >&2; exit 1; }
(cd "$OUT" && COPYFILE_DISABLE=1 tar --no-xattrs -czf bundle.tgz bundle 2>/dev/null || COPYFILE_DISABLE=1 tar -czf bundle.tgz bundle)
shasum -a 256 "$OUT/bundle.tgz"
