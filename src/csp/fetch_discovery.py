"""Fetch the WBM summary and every model's published discovery predictions.

Source: Matbench Discovery (MIT licence), pinned at the same commit as the
thermal module. Every download is checked against the md5 the repository
lists. Also fetches the MP energies file (prototype labels) and the 2023-02-07 MP
structure snapshot (179 MB; only its material ids are used, to define which
structure types the benchmark's MP reference already contained).

Files land in data/raw/discovery/<commit>/ with MANIFEST.json, which
also records each model's published leaderboard metrics for the re-score check.

Usage:
    .venv/bin/python -I src/csp/fetch_discovery.py            # all models
    .venv/bin/python -I src/csp/fetch_discovery.py --limit 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from thermal.fetch_kappa import REPO, REPO_COMMIT, SRC, download, ensure_repo  # noqa: E402

OUT = ROOT / "data" / "raw" / "discovery" / REPO_COMMIT


def models() -> list[dict]:
    rows = []
    for f in sorted((SRC / "models").glob("*/*.yml")):
        d = yaml.safe_load(f.read_text())
        disc = (d.get("metrics") or {}).get("discovery")
        if not isinstance(disc, dict) or not isinstance(disc.get("pred_file"), dict):
            continue
        pf = disc["pred_file"]
        if not pf.get("url"):
            continue
        rows.append({"model": d["model_name"], "yaml": str(f.relative_to(SRC)), "url": pf["url"], "md5": pf.get("md5"),
                     "published": {k: disc.get(k) for k in ("full_test_set", "unique_prototypes")},
                     "training_set": d.get("training_set"), "openness": d.get("openness"),
                     "model_params": d.get("model_params"), "date_published": str(d.get("date_published"))})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int); args = ap.parse_args()
    ensure_repo(); OUT.mkdir(parents=True, exist_ok=True)
    ref = yaml.safe_load((SRC / "matbench_discovery" / "data-files.yml").read_text())["wbm_summary"]
    files = yaml.safe_load((SRC / "matbench_discovery" / "data-files.yml").read_text())
    mp_e, mp_cse = files["mp_energies"], files["mp_computed_structure_entries"]
    manifest = {"repo": REPO, "commit": REPO_COMMIT, "licence": "MIT (repository); WBM and MP data: see data-files.yml",
                "wbm_summary": download(ref["url"], OUT / "wbm_summary.csv.gz", ref["md5"]),
                # MP prototype labels (2025 file) restricted to the ids of the 2023-02-07 snapshot the benchmark used
                "mp_energies": download(mp_e["url"], OUT / "mp_energies.csv.gz", mp_e["md5"]),
                "mp_computed_structure_entries": download(mp_cse["url"], OUT / "mp_computed_structure_entries_2023-02-07.json.gz", mp_cse["md5"]),
                "models": []}
    todo = models()[: args.limit] if args.limit else models()
    for i, m in enumerate(todo):
        slug = "".join(c if c.isalnum() or c in "-_." else "_" for c in m["model"])
        try:
            m.update(download(m["url"], OUT / f"{slug}.csv.gz", m["md5"]))
        except Exception as e:  # recorded, not hidden
            m["error"] = repr(e)
        manifest["models"].append(m)
        print(f"[{i + 1}/{len(todo)}] {m['model']}: {m.get('error', 'ok')}", flush=True)
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
