#!/usr/bin/env bash
# Refresh vendor/ from the live ~/.grok on this machine. Never copies auth or sessions.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOME_GROK="${GROK_HOME:-$HOME/.grok}"
VENDOR_ROOT="${SNAPSHOT_VENDOR:-$ROOT/vendor}"
ALLOW_EXTRA=()

usage() {
  cat <<'EOF'
Copy the official allowlisted skills, rules, and hook from the live Grok home.

Usage:
  ./scripts/snapshot-live.sh
  ./scripts/snapshot-live.sh --allow-extra NAME
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-extra)
      [[ -n "${2:-}" ]] || { echo "missing name after --allow-extra" >&2; exit 1; }
      ALLOW_EXTRA+=("$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

[[ -d "$HOME_GROK/skills" ]] || { echo "missing $HOME_GROK/skills" >&2; exit 1; }
ALLOWLIST="$ROOT/vendor/skill-allowlist.txt"
[[ -f "$ALLOWLIST" ]] || { echo "missing $ALLOWLIST" >&2; exit 1; }

mapfile -t OFFICIAL < <(grep -E -v '^[[:space:]]*(#|$)' "$ALLOWLIST")
[[ ${#OFFICIAL[@]} -gt 0 ]] || { echo "skill allowlist is empty" >&2; exit 1; }

allowed() {
  local name="$1" item
  for item in "${OFFICIAL[@]}" "${ALLOW_EXTRA[@]}"; do
    [[ "$item" == "$name" ]] && return 0
  done
  return 1
}

extras=()
for live in "$HOME_GROK/skills"/*; do
  [[ -d "$live" ]] || continue
  name="$(basename -- "$live")"
  if ! allowed "$name"; then
    extras+=("$name")
  fi
done
if [[ ${#extras[@]} -gt 0 ]]; then
  echo "ERROR: live home has skills outside the official allowlist:" >&2
  printf '  %s\n' "${extras[@]}" >&2
  echo "Pass --allow-extra NAME to include a specific extra skill." >&2
  exit 1
fi

mkdir -p "$VENDOR_ROOT/skills" "$VENDOR_ROOT/hooks" "$VENDOR_ROOT/rules"

for name in "${OFFICIAL[@]}"; do
  src="$HOME_GROK/skills/$name"
  [[ -d "$src" ]] || { echo "missing live skill $src" >&2; exit 1; }
  mkdir -p "$VENDOR_ROOT/skills/$name"
  rsync -a --delete "$src/" "$VENDOR_ROOT/skills/$name/"
done

[[ -f "$HOME_GROK/hooks/impeccable.json" ]] && cp -a "$HOME_GROK/hooks/impeccable.json" "$VENDOR_ROOT/hooks/impeccable.json"
[[ -f "$HOME_GROK/rules/00-routing.md" ]] && cp -a "$HOME_GROK/rules/00-routing.md" "$VENDOR_ROOT/rules/00-routing.md"
[[ -f "$HOME_GROK/rules/01-verification.md" ]] && cp -a "$HOME_GROK/rules/01-verification.md" "$VENDOR_ROOT/rules/01-verification.md"

python3 "$ROOT/lib/overlay.py" --dest "$VENDOR_ROOT/skills/found-this-design" --name found-this-design --prepend ""
python3 - "$VENDOR_ROOT/skills/found-this-design" <<'PY'
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
home_path = re.compile(r"`?/home/[^/`\s]+/Downloads/LAB GITHUB/Design`?")
for path in root.rglob("*"):
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if "Downloads/LAB GITHUB/Design" in text:
        path.write_text(
            home_path.sub("`$GROK_DESIGN_BANK` or `~/Design`", text),
            encoding="utf-8",
        )
PY

if grep -R -n -E '/home/[^/]+/' "$VENDOR_ROOT" >/dev/null; then
  echo "ERROR: vendor still contains a machine home path" >&2
  grep -R -n -E '/home/[^/]+/' "$VENDOR_ROOT" >&2 || true
  exit 1
fi

if grep -R -n --exclude-dir=.git \
    -E 'XAI_API_KEY=|gho_[A-Za-z0-9]{10,}|xai-[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9._-]{20,}' \
    "$VENDOR_ROOT" >/dev/null; then
  echo "ERROR: secret-like token pattern found in vendor after snapshot" >&2
  exit 1
fi

if [[ "$VENDOR_ROOT" == "$ROOT/vendor" && -d "$ROOT/.git" ]]; then
  echo "vendor status:"
  git -C "$ROOT" status --short -- vendor || true
  git -C "$ROOT" diff --stat -- vendor || true
fi

echo "snapshot written to $VENDOR_ROOT"
