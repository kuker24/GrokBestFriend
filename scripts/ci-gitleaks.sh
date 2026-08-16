#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 - "$ROOT" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

root = Path(sys.argv[1])
sources = json.loads((root / "vendor/sources.json").read_text(encoding="utf-8"))
node = sources["sources"]["gitleaks"]
url = node["artifactUrl"]
expected = node["artifactSha256"]
dest = root / "vendor/.cache/gitleaks-ci.tgz"
dest.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(url, dest)
digest = hashlib.sha256(dest.read_bytes()).hexdigest()
if digest != expected:
    raise SystemExit(f"gitleaks checksum mismatch: {digest}")
with tempfile.TemporaryDirectory() as tmp:
    with tarfile.open(dest) as archive:
        archive.extractall(tmp)
    binary = Path(tmp) / "gitleaks"
    os.chmod(binary, 0o755)
    subprocess.check_call([str(binary), "detect", "--source", str(root), "--no-git", "--redact"])
PY
