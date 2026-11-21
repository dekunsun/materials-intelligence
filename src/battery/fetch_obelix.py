"""Download the OBELiX dataset files at a pinned commit and record their hashes.

OBELiX: Therrien et al. 2025, arXiv:2502.14234, https://github.com/NRC-Mila/OBELiX
License: CC BY 4.0. We do not commit the data; we commit this script.

Files land in data/raw/obelix/<commit>/ with a MANIFEST.json holding the
source URL and SHA-256 of every file, so a later run can prove which bytes
it used.

Usage:
    .venv/bin/python -I src/battery/fetch_obelix.py
"""

from __future__ import annotations

import hashlib
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi

# Pinned commit (main as of 2025-11-27). Change deliberately, never implicitly.
COMMIT = "4eaac889809dd489e3bae468c45d5c0e02b9147a"
FILES = ["data/processed.csv", "data/raw.xlsx", "data/train_idx.csv",
         "data/test_idx.csv", "LICENSE.txt"]
BASE = f"https://raw.githubusercontent.com/NRC-Mila/OBELiX/{COMMIT}/"

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "obelix" / COMMIT


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "https://github.com/NRC-Mila/OBELiX", "commit": COMMIT,
                "license": "CC BY 4.0",
                "fetched_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
    for rel in FILES:
        url = BASE + rel
        dest = OUT / Path(rel).name
        # A generic client name: no personal details go to the server.
        req = urllib.request.Request(url, headers={"User-Agent": "materials-intelligence-fetch/0.1"})
        # python.org builds on macOS ship without system CA certs; use certifi's bundle.
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            dest.write_bytes(resp.read())
        manifest["files"][dest.name] = {"url": url, "sha256": sha256(dest),
                                        "bytes": dest.stat().st_size}
        print(f"{dest.name:16s} {manifest['files'][dest.name]['bytes']:>8d} B")
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {OUT / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
