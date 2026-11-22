"""Train EquiCSP on one arm of the CSP random-removal control, with a per-step timer.

This is a thin wrapper around EquiCSP's own `equicsp/run.py` (commit d7921c3). It changes no
model, data or optimiser code. It only adds one callback that appends a JSON line to $STEP_LOG
every time the optimiser step counter advances, and around each validation pass, so the run's
time per optimiser step can be measured (used by the 1,000-step smoke test to project cost).

The recipe (pre-registered in src/csp/random_removal_control.py) is passed as Hydra overrides:

    PROJECT_ROOT=<EquiCSP checkout> HYDRA_JOBS=<out dir> WABDB_DIR=<out dir> STEP_LOG=<file.jsonl> \
    python equicsp_train.py expname=PEROV_s42 data.root_path=<arm data dir> \
        data.datamodule.batch_size.train=64 train.pl_trainer.accumulate_grad_batches=4 \
        train.random_seed=42 data.train_max_epochs=2000 +train.pl_trainer.max_steps=106000

`data.root_path` must hold the arm's {train,val,test}.csv and {train,val,test}_ori.pt written by
src/csp/equicsp_prepare_arms.py. 64 x 4 accumulation gives the effective batch of 256. The epoch
cap is raised so that the step budget, not the epoch count, ends training (a filtered arm has
fewer than 106 optimiser steps per epoch).
"""

import json
import os
import sys
import time

sys.path.insert(0, os.environ["PROJECT_ROOT"])

import hydra  # noqa: E402
import omegaconf  # noqa: E402
import torch  # noqa: E402
from pytorch_lightning import Callback  # noqa: E402

import equicsp.run as equicsp_run  # noqa: E402


class StepTimer(Callback):
    def __init__(self, path: str):
        self.f = open(path, "a")
        self.t0 = time.time()
        self.last_step = None

    def _write(self, **rec):
        rec["t"] = round(time.time() - self.t0, 3)
        self.f.write(json.dumps(rec) + "\n")
        self.f.flush()

    def on_train_start(self, trainer, pl_module):
        self._write(ev="train_start", step=trainer.global_step,
                    gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")

    def on_train_batch_end(self, trainer, pl_module, *args, **kwargs):
        if trainer.global_step != self.last_step:
            self.last_step = trainer.global_step
            self._write(ev="step", step=trainer.global_step)

    def on_validation_start(self, trainer, pl_module):
        self._write(ev="val_start", step=trainer.global_step)

    def on_validation_end(self, trainer, pl_module):
        self._write(ev="val_end", step=trainer.global_step)

    def on_train_end(self, trainer, pl_module):
        mem = torch.cuda.max_memory_allocated() / 2**30 if torch.cuda.is_available() else None
        self._write(ev="train_end", step=trainer.global_step, peak_gpu_mem_gib=mem)


_build = equicsp_run.build_callbacks
equicsp_run.build_callbacks = lambda cfg: _build(cfg) + [StepTimer(os.environ["STEP_LOG"])]


# EquiCSP's own `main` resolves its config path relative to the equicsp package when it is called
# from another script, so register the same entry point here with the absolute config directory.
@hydra.main(config_path=os.path.join(os.environ["PROJECT_ROOT"], "conf"), config_name="default")
def main(cfg: omegaconf.DictConfig):
    equicsp_run.run(cfg)


if __name__ == "__main__":
    main()
