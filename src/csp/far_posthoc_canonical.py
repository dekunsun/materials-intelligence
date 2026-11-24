"""POST-HOC correction of Stage 1's framework key (written after the pre-registered decision; never replaces it).

Problem found after the run: far_split.framework() drops the element grouping from an AFLOW-style label but keeps the
Wyckoff letters as that label canonicalised them. The canonical origin choice depends on the element grouping, so the
same framework with a different grouping can end up with different letters and look "unfamiliar".

Fix: after dropping the grouping, canonicalise the letter multiset over all equivalent origin choices of the space
group (Matbench Discovery's wyckoff-position-relabelings.yaml.gz, the table its labeller uses) and take the
lexicographically smallest sorted multiset, on both the MP reference and WBM. Then re-label the cells.

Usage (repository root):
    .venv/bin/python -I src/csp/far_posthoc_canonical.py results/<stage1_run>
Writes <run>/posthoc_canonical_framework/split.csv.gz; then run far_decide.py and far_sensitivity.py on that folder.
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from csp.far_split import CELLS, framework  # noqa: E402
from csp.run_screening import RAW, mp2023_ids  # noqa: E402

RELABEL = yaml.safe_load(gzip.open(ROOT / "data/raw/mbd_src/matbench-discovery/matbench_discovery/structure/"
                                   "wyckoff-position-relabelings.yaml.gz"))


def canonical(key) -> str | None:
    """'cF16_225_abc' -> the same framework key with the letters canonicalised over equivalent origin choices."""
    if not isinstance(key, str):
        return None
    pearson, spg, letters = key.split("_", 2)
    options = ["".join(sorted(letters.translate(str.maketrans(t)))) for t in RELABEL.get(int(spg), [])] or [letters]
    return f"{pearson}_{spg}_" + min(options)


def main(run: str) -> int:
    run = Path(run)
    out = run / "posthoc_canonical_framework"
    out.mkdir(exist_ok=True)
    mp = pd.read_csv(RAW / "mp_energies.csv.gz")
    mp = mp[mp.material_id.isin(mp2023_ids())]
    ref = set(mp.protostructure_spglib.dropna().map(framework).map(canonical))
    s = pd.read_csv(run / "split.csv.gz").set_index("material_id")
    was = s.framework_known.copy()
    for col in ("framework", "framework_relaxed"):
        s[col] = s[col].map(canonical)
        s[col + "_known"] = s[col].isin(ref)
    assert (s.framework_known | ~was).all(), "a framework known before canonicalising became unfamiliar"
    s["cell"] = [CELLS[(c, f)] for c, f in zip(s.chem_familiar, s.framework_known)]
    s.to_csv(out / "split.csv.gz")
    moved = int((was != s.framework_known).sum())
    print(f"structures moved from unfamiliar to known framework: {moved}")
    print(s.groupby("cell").agg(n=("stable", "size"), stable=("stable", "sum")).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
