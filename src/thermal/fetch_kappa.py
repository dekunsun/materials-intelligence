"""Fetch the kappa-103 DFT reference and published model predictions.

Source: Matbench Discovery (MIT licence), pinned at REPO_COMMIT. Each model's
YAML lists its kappa-103 prediction file with a Figshare URL and an md5; every
download is checked against that md5. The DFT reference (phononDB PBE,
no non-analytical correction) comes from data-files.yml at the same commit.

Files land in data/raw/kappa/<REPO_COMMIT>/, with MANIFEST.json (md5 + sha256,
published kappa_SRME per model). data/raw/ is git-ignored.

Usage:
    .venv/bin/python -I src/thermal/fetch_kappa.py            # all models
    .venv/bin/python -I src/thermal/fetch_kappa.py --limit 3  # reference + first 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import subprocess
import urllib.request
from pathlib import Path

import certifi
import yaml

ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/janosh/matbench-discovery.git"
REPO_COMMIT = "6d587c184cdb4a4865dc0b15b04a5e6d77ed464f"
SRC = ROOT / "data" / "raw" / "mbd_src" / "matbench-discovery"
OUT = ROOT / "data" / "raw" / "kappa" / REPO_COMMIT
CTX = ssl.create_default_context(cafile=certifi.where())


def ensure_repo() -> None:
    if not SRC.exists():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--filter=blob:none", REPO, str(SRC)], check=True)
    head = subprocess.run(["git", "-C", str(SRC), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != REPO_COMMIT:
        subprocess.run(["git", "-C", str(SRC), "fetch", "--depth", "1", "origin", REPO_COMMIT], check=True)
        subprocess.run(["git", "-C", str(SRC), "checkout", REPO_COMMIT], check=True)


def download(url: str, dest: Path, md5: str | None) -> dict:
    if not dest.exists():
        req = urllib.request.Request(url.replace("https://figshare.com/files/", "https://ndownloader.figshare.com/files/"),
                                     headers={"User-Agent": "python-urllib research-script"})
        with urllib.request.urlopen(req, context=CTX, timeout=300) as r:
            data = r.read()
        dest.write_bytes(data)
    data = dest.read_bytes()
    got = hashlib.md5(data).hexdigest()
    if md5 and got != md5:
        raise ValueError(f"md5 mismatch for {dest.name}: {got} != {md5}")
    return {"file": dest.name, "url": url, "md5": got, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def models() -> list[dict]:
    rows = []
    for f in sorted((SRC / "models").glob("*/*.yml")):
        d = yaml.safe_load(f.read_text())
        k = ((d.get("metrics") or {}).get("phonons") or {})
        k = k.get("kappa_103") if isinstance(k, dict) else None
        if not isinstance(k, dict) or "κ_SRME" not in k or not isinstance(k.get("pred_file"), dict):
            continue
        pf = k["pred_file"]
        rows.append({"model": d["model_name"], "yaml": str(f.relative_to(SRC)), "url": pf["url"], "md5": pf.get("md5"),
                     "published": {m: k.get(m) for m in ["κ_SRME", "κ_SRE", "κ_SRD", "κ_failure_rate"]},
                     "training_set": d.get("training_set"), "openness": d.get("openness")})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int); args = ap.parse_args()
    ensure_repo(); OUT.mkdir(parents=True, exist_ok=True)
    ref = yaml.safe_load((SRC / "matbench_discovery" / "data-files.yml").read_text())["phonondb_pbe_103_kappa_no_nac"]
    manifest = {"repo": REPO, "commit": REPO_COMMIT, "licence": "MIT (repository); reference data: phononDB PBE via Togo, see data-files.yml",
                "reference": download(ref["url"], OUT / "reference_phononDB_PBE_noNAC.json.gz", ref["md5"]), "models": []}
    todo = models()[: args.limit] if args.limit else models()
    for i, m in enumerate(todo):
        slug = "".join(c if c.isalnum() or c in "-_." else "_" for c in m["model"])
        try:
            m.update(download(m["url"], OUT / f"{slug}.json.gz", m["md5"]))
        except Exception as e:  # keep going; failures are recorded, not hidden
            m["error"] = repr(e)
        manifest["models"].append(m)
        print(f"[{i + 1}/{len(todo)}] {m['model']}: {m.get('error', 'ok')}", flush=True)
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
