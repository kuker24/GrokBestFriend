#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 - "$ROOT" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
failed = False

def ok(msg: str) -> None:
    print("OK  " + msg)

def error(msg: str) -> None:
    global failed
    failed = True
    print("FAIL " + msg)

sources = json.loads((root / "vendor/sources.json").read_text(encoding="utf-8"))
ok("sources.json parses")
sha_re = re.compile(r"^[0-9a-f]{64}$")
for name, node in (sources.get("sources") or {}).items():
    digest = node.get("artifactSha256")
    if digest and not sha_re.match(digest):
        error(f"{name} artifactSha256 is not 64 hex")
    elif digest:
        ok(f"{name} sha256 format")

allow = [
    line.strip()
    for line in (root / "vendor/skill-allowlist.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
]
inventory = json.loads((root / "vendor/inventory.json").read_text(encoding="utf-8")).get("skills") or []
if allow != inventory:
    error("allowlist != inventory.skills")
else:
    ok("allowlist matches inventory.skills")

for name in allow:
    if not (root / "vendor/skills" / name / "SKILL.md").is_file():
        error("missing vendor skill " + name)
ok("every allowlisted skill is vendored")

for name in ("00-routing.md", "01-verification.md"):
    template = (root / "templates/rules" / name).read_bytes()
    vendor = (root / "vendor/rules" / name).read_bytes()
    if template != vendor:
        error(f"templates/rules/{name} != vendor/rules/{name}")
    else:
        ok(f"{name} template matches vendor")

mcp = (root / "lib/mcp.sh").read_text(encoding="utf-8")
if re.search(r"mcp add.*\|\|\s*true", mcp) or re.search(r"mcp disable.*\|\|\s*true", mcp):
    error("mcp.sh still swallows add/disable errors")
else:
    ok("mcp.sh has no || true on add/disable")

tx = (root / "lib/transaction.sh").read_text(encoding="utf-8")
if "old-skill" in tx or "always delete" in tx.lower():
    error("transaction.sh still encodes destructive extra-skill deletion")
else:
    ok("transaction.sh does not hard-code extra-skill deletion")
if "--allow-extra" in (root / "scripts/snapshot-live.sh").read_text(encoding="utf-8") and \
        "not supported" not in (root / "scripts/snapshot-live.sh").read_text(encoding="utf-8"):
    error("snapshot still implements --allow-extra copy")
else:
    ok("snapshot does not copy extras")
if not (root / "vendor/runtime-policy.json").is_file():
    error("missing vendor/runtime-policy.json")
else:
    ok("runtime-policy.json present")

protect = (root / "scripts/enable-main-protection.sh").read_text(encoding="utf-8")
if "reconciling id" in protect:
    error("protection script still auto-picks the first duplicate main-ci")
elif "Resolve the duplicates" not in protect or "exit 1" not in protect:
    error("protection script does not fail closed on duplicate main-ci")
else:
    ok("protection script fails closed on duplicate main-ci")

version = (root / "VERSION").read_text(encoding="utf-8").strip()
snapshot = str(sources.get("snapshot", ""))
if version not in snapshot:
    error(f"VERSION {version} not reflected in sources.snapshot {snapshot}")
else:
    ok("VERSION matches sources.snapshot")

raise SystemExit(1 if failed else 0)
PY

printf 'test-source-integrity passed\n'
