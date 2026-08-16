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
python3 - <<'PY'
import re
from pathlib import Path
root = Path(".")
failed = False

for name in ("ask-matt", "grill-with-docs", "to-spec", "to-tickets"):
    text = (root / "vendor/skills" / name / "SKILL.md").read_text(encoding="utf-8")
    if re.search(r"^disable-model-invocation:\s*true\s*$", text, re.MULTILINE):
        print("ERROR: FAIL vendor %s still disable-model-invocation" % name)
        failed = True
    else:
        print("OK  vendor %s is model-invocable" % name)

grill = (root / "vendor/skills/grill-with-docs/SKILL.md").read_text(encoding="utf-8")
if re.search(r"`?/grilling`?|`?/domain-modeling`?", grill):
    print("ERROR: FAIL vendor grill-with-docs still names missing primitives")
    failed = True
else:
    print("OK  vendor grill-with-docs has no stub primitives")

ask = (root / "vendor/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
if len(re.findall(r"^## GrokBuild map\s*$", ask, re.MULTILINE)) > 1:
    print("ERROR: FAIL vendor ask-matt has duplicate GrokBuild maps")
    failed = True
else:
    print("OK  vendor ask-matt has at most one GrokBuild map")

routing = (root / "vendor/rules/00-routing.md").read_text(encoding="utf-8")
if "If Codebase Memory has no project for cwd" not in routing:
    print("ERROR: FAIL vendor 00-routing.md missing unindexed-cwd skip")
    failed = True
else:
    print("OK  vendor 00-routing.md skips unindexed Codebase Memory")
if "Do **not** auto-start bundled `/implement`" not in routing:
    print("ERROR: FAIL vendor 00-routing.md missing no-auto-implement")
    failed = True
else:
    print("OK  vendor 00-routing.md does not auto-start /implement")

if failed:
    raise SystemExit(1)
PY
python3 tests/test-overlay.py
