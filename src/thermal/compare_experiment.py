"""Post-hoc: put DFT, the five best models and measurement side by side for seven
commercially relevant high-kappa materials (data/thermal/experimental_kappa.csv,
every row with its source).

Signed relative differences (a - b) / b. Experimental ranges use the midpoint;
SiC (3C) is a lower bound (">500"), so its DFT-vs-experiment error is at least
the value shown. n = 7 hand-picked materials, no intervals: descriptive only.
The five models were selected by SRME on this same benchmark.

Usage:
    .venv/bin/python src/thermal/compare_experiment.py results/<thermal_run_id>
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from thermal.provenance import write as write_provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    run = Path(sys.argv[1])
    src = ROOT / "data" / "thermal" / "experimental_kappa.csv"
    exp = pd.read_csv(src).set_index("material_id")
    pm = pd.read_csv(run / "per_material.csv")
    best5 = pd.read_csv(run / "model_metrics.csv").sort_values("srme").model[:5].tolist()
    sub = pm[pm.material_id.isin(exp.index) & pm.model.isin(best5)]
    g = sub.groupby("material_id").agg(k_dft=("k_dft", "first"), best5_min=("k_pred", "min"),
                                       best5_max=("k_pred", "max"), best5_mean=("k_pred", "mean"))
    out = exp.join(g)
    out["exp_mid"] = (out.exp_low + out.exp_high) / 2
    out["model_vs_dft_worst"] = pd.concat([(out.best5_min / out.k_dft - 1).abs(),
                                           (out.best5_max / out.k_dft - 1).abs()], axis=1).max(axis=1)
    out["dft_vs_exp"] = out.k_dft / out.exp_mid - 1
    out["best5_mean_vs_exp"] = out.best5_mean / out.exp_mid - 1
    out["status"] = "post-hoc"
    out.to_csv(run / "experiment_comparison.csv")
    write_provenance(run, "compare_experiment", inputs=[src, run / "per_material.csv", run / "model_metrics.csv"],
                     status="post-hoc", note="n=7, descriptive")
    print(out[["material", "k_dft", "best5_min", "best5_max", "exp_mid", "model_vs_dft_worst", "dft_vs_exp", "best5_mean_vs_exp"]].round(3).to_string())
    print("median |model-DFT| worst of 5:", round(out.model_vs_dft_worst.median(), 3),
          "| median |DFT-exp|:", round(out.dft_vs_exp.abs().median(), 3),
          "| median |best5 mean - exp|:", round(out.best5_mean_vs_exp.abs().median(), 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
