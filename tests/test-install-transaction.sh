#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export GRT_HOME="$tmp/home"
export GRT_DRY_RUN=0
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"

fail() { echo "FAIL $*" >&2; exit 1; }

type grt_lock_begin >/dev/null 2>&1 || fail "missing grt_lock_begin"
type grt_tx_set_state >/dev/null 2>&1 || fail "missing grt_tx_set_state"
type grt_can_replace_owned >/dev/null 2>&1 || fail "missing grt_can_replace_owned"

mkdir -p "$GRT_SKILLS/old-skill" "$GRT_SKILLS/ask-matt" "$GRT_RULES" "$GRT_HOOKS" "$GRT_HOME/bin" "$GRT_RUNTIME"
echo old > "$GRT_SKILLS/old-skill/SKILL.md"
echo custom-ask > "$GRT_SKILLS/ask-matt/SKILL.md"
echo old-rule > "$GRT_RULES/00-routing.md"
echo personal-rule > "$GRT_RULES/99-personal.md"
echo old-hook > "$GRT_HOOKS/impeccable.json"
echo personal-hook > "$GRT_HOOKS/personal.json"
echo old-bin > "$GRT_HOME/bin/grok-chromium-cdp"

# v1.1.0-style manifest so owned names migrate
python3 - "$GRT_MANIFEST" "$GRT_HOME" <<'PY'
import json, sys
from pathlib import Path
manifest, home = sys.argv[1], sys.argv[2]
Path(manifest).write_text(json.dumps({
    "version": 3,
    "product": "GrokBestFriend",
    "productVersion": "1.1.0",
    "skills": [f"{home}/skills/ask-matt"],
    "rules": [f"{home}/rules/00-routing.md"],
    "hooks": [f"{home}/hooks/impeccable.json"],
}, indent=2) + "\n", encoding="utf-8")
PY

grt_lock_begin
grt_tx_check_stale
grt_tx_set_state PREPARING
grt_backup_owned
[[ -n "${GRT_BACKUP_STAMP:-}" ]] || fail "backup stamp empty"
[[ "$GRT_BACKUP_STAMP" =~ ^[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{8}$ ]] || fail "stamp format $GRT_BACKUP_STAMP"
[[ -f "$(grt_backup_root)/$GRT_BACKUP_STAMP/skills/old-skill/SKILL.md" ]] || fail "backup missed foreign skill"
[[ -f "$(grt_backup_root)/$GRT_BACKUP_STAMP/journal.json" ]] || fail "backup missing journal.json"
echo "OK  backup stamp + journal + foreign skill"

stamp_a="$GRT_BACKUP_STAMP"
grt_backup_owned
stamp_b="$GRT_BACKUP_STAMP"
[[ "$stamp_a" != "$stamp_b" ]] || fail "backup stamps collided"
echo "OK  backup stamps do not collide"

grt_tx_set_state BACKED_UP
grt_tx_set_state MUTATING
grt_stage_owned
grt_validate_stage
echo "OK  staged tree validates"

grt_atomic_swap
[[ -f "$GRT_SKILLS/old-skill/SKILL.md" ]] || fail "foreign old-skill was deleted"
[[ -f "$GRT_RULES/99-personal.md" ]] || fail "foreign rule was deleted"
[[ -f "$GRT_HOOKS/personal.json" ]] || fail "foreign hook was deleted"
[[ -f "$GRT_SKILLS/impeccable/SKILL.md" ]] || fail "owned impeccable missing"
[[ -f "$GRT_SKILLS/impeccable/.grokbestfriend-owned.json" ]] || fail "missing skill ownership marker"
[[ -x "$GRT_SKILLS/impeccable/scripts/design-intelligence.py" ]] || fail "packaged design-intelligence CLI missing"
[[ -f "$GRT_SKILLS/impeccable/scripts/design_intelligence/selection.py" ]] || fail "packaged design-intelligence runtime missing"
[[ -f "$GRT_SKILLS/impeccable/design-intelligence/policy.json" ]] || fail "packaged design-intelligence policy missing"
PYTHONDONTWRITEBYTECODE=1 python3 "$GRT_SKILLS/impeccable/scripts/design-intelligence.py" plan \
  --intent refine --scope narrow --mode Operate --authority established >"$tmp/plan.json"
grep -q '"lane": "none"' "$tmp/plan.json" || fail "packaged design-intelligence CLI does not run"
python3 - "$ROOT" "$tmp/di-bank" <<'PY'
import sys
from pathlib import Path
root, bank = map(Path, sys.argv[1:3])
sys.path.insert(0, str(root / "lib"))
sys.path.insert(0, str(root / "tests"))
from design_intelligence_support import seed_bank
seed_bank(bank)
PY
PYTHONDONTWRITEBYTECODE=1 python3 "$GRT_SKILLS/impeccable/scripts/design-intelligence.py" shortlist \
  --bank "$tmp/di-bank" --intent greenfield --mode Operate \
  --query "acme dashboard sidebar kpi" >"$tmp/shortlist.json"
grep -q '"packages_loaded_during_search": 0' "$tmp/shortlist.json" || fail "packaged shortlist opened packages"
grep -q '"id": "system:acme"' "$tmp/shortlist.json" || fail "packaged shortlist cannot load policy/catalog"
[[ -f "$GRT_RULES/.grokbestfriend-owned.json" ]] || fail "missing rules ownership marker"
grep -q 'at most one verification specialist' "$GRT_RULES/00-routing.md" || fail "owned rule not replaced"
[[ -f "$GRT_SKILLS/ask-matt/SKILL.md" ]] || fail "ask-matt missing"
! grep -qx 'custom-ask' "$GRT_SKILLS/ask-matt/SKILL.md" || fail "migrated ask-matt not replaced"
echo "OK  swap preserves foreign trees and replaces owned names"

echo corrupted > "$GRT_RULES/00-routing.md"
grt_restore_backup
grep -q 'old-rule' "$GRT_RULES/00-routing.md" || fail "restore did not return pre-image rule"
[[ -f "$GRT_SKILLS/old-skill/SKILL.md" ]] || fail "restore lost foreign skill"
echo "OK  restore rolls back to the backup"

grt_lock_end

# Clean-machine: created rules must disappear on restore
home2="$tmp/home2"
export GRT_HOME="$home2"
unset GRT_BACKUP_STAMP
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"
mkdir -p "$GRT_HOME"
[[ ! -d "$GRT_RULES" ]]
grt_lock_begin
grt_tx_set_state PREPARING
grt_backup_owned
grt_tx_set_state MUTATING
grt_stage_owned
grt_atomic_swap
[[ -f "$GRT_RULES/00-routing.md" ]] || fail "stage/swap did not create rules"
grt_restore_backup
[[ ! -d "$GRT_RULES" ]] || fail "clean-machine restore left created rules/"
echo "OK  clean-machine restore deletes created rules/"
grt_lock_end

# Unowned implement must refuse (no silent delete)
home3="$tmp/home3"
export GRT_HOME="$home3"
unset GRT_BACKUP_STAMP
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"
mkdir -p "$GRT_SKILLS/implement"
echo mine > "$GRT_SKILLS/implement/SKILL.md"
if (grt_stage_owned) >"$tmp/impl.out" 2>"$tmp/impl.err"; then
  fail "unowned skills/implement was overwritten or deleted"
fi
grep -q 'implement' "$tmp/impl.err" || fail "collision error did not name implement"
[[ -f "$GRT_SKILLS/implement/SKILL.md" ]] || fail "unowned implement was deleted"
echo "OK  unowned skills/implement refuses and is left in place"

# Exclusive lock
home4="$tmp/home4"
export GRT_HOME="$home4"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"
grt_lock_begin
if GRT_HOME="$home4" GRT_DRY_RUN=0 bash -c '
  set -euo pipefail
  source "'"$ROOT"'/lib/common.sh"
  source "'"$ROOT"'/lib/transaction.sh"
  grt_lock_begin
' 2>"$tmp/lock.err"; then
  fail "second lock holder was allowed"
fi
grep -qi 'lock' "$tmp/lock.err" || fail "lock error did not mention lock"
grt_lock_end
echo "OK  exclusive lock refuses a second holder"

# Leftover SWAPPED refuses a new install helper
home5="$tmp/home5"
export GRT_HOME="$home5"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"
mkdir -p "$GRT_HOME/runtime/tx"
printf '%s\n' '{"state":"SWAPPED","stamp":"deadbeef"}' > "$GRT_HOME/runtime/tx/current.json"
if (grt_tx_check_stale) >"$tmp/stale.out" 2>"$tmp/stale.err"; then
  fail "SWAPPED leftover was not refused"
fi
grep -qi 'incomplete' "$tmp/stale.err" || fail "stale tx error unclear"
echo "OK  leftover SWAPPED refuses"

printf 'test-install-transaction passed\n'
