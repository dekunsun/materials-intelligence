#!/usr/bin/env bash
# Build the EquiCSP training environment on a rented Linux GPU pod (CUDA 11.1 builds of torch 1.9.0).
# Run on the pod from the unpacked bundle directory, e.g. /workspace/bundle:
#     bash src/csp/pod_setup.sh
# Python 3.8 comes from uv. GPUs must be Ampere or older (sm_86 at most): torch 1.9.0+cu111 has no
# kernels for Ada (RTX 4090, L4) or Hopper.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv -p 3.8 /workspace/venv
export VIRTUAL_ENV=/workspace/venv
uv pip install "torch==1.9.0+cu111" -f https://download.pytorch.org/whl/torch_stable.html
uv pip install "torch-scatter==2.0.9" "torch-sparse==0.6.12" -f https://data.pyg.org/whl/torch-1.9.0+cu111.html
# PyYAML 5.4.1 does not build with Cython 3, so install the pinned Cython first and build without isolation.
uv pip install "cython==0.29.37" "setuptools==59.5.0" wheel
uv pip install --no-build-isolation "pyyaml==5.4.1"
grep -v -E '^(#|torch==|torch-scatter==|torch-sparse==|pyyaml==|cython==|setuptools==)' src/csp/requirements-equicsp.txt > /tmp/req.txt
uv pip install -r /tmp/req.txt
/workspace/venv/bin/python -c "import torch, torch_scatter, torch_sparse, torch_geometric, pytorch_lightning as pl; \
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'gpu', torch.cuda.get_device_name(0), 'pl', pl.__version__)"
