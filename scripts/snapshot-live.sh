#!/usr/bin/env bash
# Refresh vendor/ from the live ~/.grok on this machine. Never copies auth or sessions.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOME_GROK="${GROK_HOME:-$HOME/.grok}"

[[ -d "$HOME_GROK/skills" ]] || { echo "missing $HOME_GROK/skills" >&2; exit 1; }

mkdir -p "$ROOT/vendor/skills" "$ROOT/vendor/hooks" "$ROOT/vendor/rules"
rsync -a --delete "$HOME_GROK/skills/" "$ROOT/vendor/skills/"
[[ -f "$HOME_GROK/hooks/impeccable.json" ]] && cp -a "$HOME_GROK/hooks/impeccable.json" "$ROOT/vendor/hooks/impeccable.json"
[[ -f "$HOME_GROK/rules/00-routing.md" ]] && cp -a "$HOME_GROK/rules/00-routing.md" "$ROOT/vendor/rules/00-routing.md"
[[ -f "$HOME_GROK/rules/01-verification.md" ]] && cp -a "$HOME_GROK/rules/01-verification.md" "$ROOT/vendor/rules/01-verification.md"

python3 "$ROOT/lib/overlay.py" --dest "$ROOT/vendor/skills/found-this-design" --name found-this-design --prepend ""
python3 - "$ROOT/vendor/skills/found-this-design" <<'PY'
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

if grep -R -n -E '/home/[^/]+/' "$ROOT/vendor" >/dev/null; then
  echo "ERROR: vendor still contains a machine home path" >&2
  grep -R -n -E '/home/[^/]+/' "$ROOT/vendor" >&2 || true
  exit 1
fi

echo "snapshot written to $ROOT/vendor"
