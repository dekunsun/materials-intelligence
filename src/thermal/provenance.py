"""Write a provenance record next to every output a thermal script produces.

Code is identified both by the git commit (with a flag for uncommitted changes
under src/ and tests/) and by the SHA-256 of every src/**/*.py file. Runs made
before the repository existed (2026-11-21) carry file hashes only. (Before 2026-11-21 evening only
src/thermal/*.py was hashed; thermal runs made before then carry that narrower record.)
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ["numpy", "pandas", "scipy", "pymatgen", "matplotlib", "PyYAML", "certifi"]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(step: str, inputs: list[Path], seed: int | None = None, status: str = "pre-registered", note: str = "") -> dict:
    vers = {}
    for p in PACKAGES:
        try:
            vers[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            vers[p] = None
    return {"step": step, "status": status, "note": note, "utc": datetime.now(timezone.utc).isoformat(),
            "seed": seed, "python": platform.python_version(), "packages": vers,
            "inputs": {str(Path(i).resolve().relative_to(ROOT)): sha256(i) for i in inputs},
            "code": {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / "src").rglob("*.py"))},
            **git_state()}


def git_state() -> dict:
    """Commit and whether the working tree had uncommitted changes (code hashes above are kept either way)."""
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "src", "tests"],
                                    capture_output=True, text=True, check=True).stdout.strip())
        return {"git_commit": commit, "git_dirty_src": dirty}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"git_commit": None, "git_note": "not a git repository; code identified by file hashes"}


def write(run: Path, step: str, **kw) -> None:
    (Path(run) / f"provenance_{step}.json").write_text(json.dumps(record(step, **kw), indent=2))
