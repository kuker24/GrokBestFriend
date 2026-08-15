#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
./install.sh --dry-run
python3 - <<'PY'
from pathlib import Path
root = Path(".")
required = [
    "install.sh",
    "vendor/sources.json",
    "vendor/inventory.json",
    "vendor/config/user.toml",
    "vendor/hooks/impeccable.json",
    "vendor/rules/00-routing.md",
    "vendor/rules/01-verification.md",
    "vendor/skills/impeccable/SKILL.md",
    "vendor/skills/found-this-design/SKILL.md",
    "vendor/skills/matt-implement/SKILL.md",
    "lib/grok-chromium-cdp.sh",
]
missing = [p for p in required if not (root / p).exists()]
if missing:
    raise SystemExit("missing: " + ", ".join(missing))
print("OK  required vendor files present")
PY
