"""Fetch the public inputs for the CSP random-removal control.

Two sources, both pinned to a commit:

- usccolumbia/benchmark_deep_csp (MIT), the code and data release of
  Wei et al., arXiv:2609.26502 v2. We take the ablation protocol, the audit file
  (split hashes), the per-target and summary results of the released arms, and
  the removed-structure ID lists for the ABC2D6 and perovskite-framework arms.
- jiaor17/DiffCSP (MIT), which hosts the MP-20 train/val/test CSVs the paper
  used. Their SHA-256 must equal the source hashes recorded in the paper's
  audit.json, otherwise the script stops: a different MP-20 copy would make
  our splits incomparable with theirs.

Files land in data/raw/csp_ablation/ (not committed) with MANIFEST.json.

Usage:
    .venv/bin/python -I src/csp/fetch_csp_ablation.py
"""

from __future__ import annotations

import hashlib
import json
import ssl
import sys
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "csp_ablation"
CTX = ssl.create_default_context(cafile=certifi.where())

BENCH = "usccolumbia/benchmark_deep_csp"
BENCH_COMMIT = "631c7654942ed9fdf57cc42f37764e0d0994dd31"  # 2026-10-16, matches the v2 release
BENCH_FILES = [
    "ablation/PROTOCOL.md",
    "ablation/audit.json",
    "ablation/ablation_summary.csv",
    "ablation/ablation_per_target.csv",
    "ablation/removed_ids/ABC2D6_train.csv",
    "ablation/removed_ids/ABC2D6_val.csv",
    "ablation/removed_ids/PEROV_train.csv",
    "ablation/removed_ids/PEROV_val.csv",
]
DIFFCSP = "jiaor17/DiffCSP"
DIFFCSP_COMMIT = "7121d159826efa2ba9500bf299250d96da37f146"  # 2024-04-27
MP20_FILES = ["train.csv", "val.csv", "test.csv"]


def get(url: str, dest: Path) -> dict:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "python-urllib research-script"})
        with urllib.request.urlopen(req, context=CTX, timeout=600) as r:
            dest.write_bytes(r.read())
    data = dest.read_bytes()
    return {"file": str(dest.relative_to(OUT)), "url": url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = [get(f"https://raw.githubusercontent.com/{BENCH}/{BENCH_COMMIT}/{f}", OUT / "benchmark" / f) for f in BENCH_FILES]
    mp20 = [get(f"https://raw.githubusercontent.com/{DIFFCSP}/{DIFFCSP_COMMIT}/data/mp_20/{f}", OUT / "mp_20" / f) for f in MP20_FILES]

    # The paper's audit records the SHA-256 of the MP-20 CSVs it filtered (keys are the authors' local paths).
    audit = json.loads((OUT / "benchmark" / "ablation" / "audit.json").read_text())
    expected = {Path(k).name: v for k, v in audit["source_hashes"].items() if Path(k).parent.name == "mp_20"}
    for m in mp20:
        name = Path(m["file"]).name
        m["matches_paper_audit"] = m["sha256"] == expected.get(name)
        if not m["matches_paper_audit"]:
            raise SystemExit(f"{name}: sha256 {m['sha256']} differs from the paper's audit {expected.get(name)}")

    manifest = {"benchmark_repo": BENCH, "benchmark_commit": BENCH_COMMIT, "benchmark_licence": "MIT",
                "mp20_repo": DIFFCSP, "mp20_commit": DIFFCSP_COMMIT, "mp20_licence": "MIT (repository); MP-20 derives from Materials Project",
                "files": files, "mp20": mp20}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"{len(files)} benchmark files, {len(mp20)} MP-20 files; MP-20 hashes match the paper's audit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
