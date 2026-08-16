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

mkdir -p "$GRT_SKILLS/old-skill" "$GRT_RULES" "$GRT_HOOKS" "$GRT_HOME/bin"
echo old > "$GRT_SKILLS/old-skill/SKILL.md"
echo old-rule > "$GRT_RULES/00-routing.md"
echo old-hook > "$GRT_HOOKS/impeccable.json"
echo old-bin > "$GRT_HOME/bin/grok-chromium-cdp"

grt_backup_owned
[[ -n "$GRT_BACKUP_STAMP" ]]
[[ -f "$(grt_backup_root)/$GRT_BACKUP_STAMP/skills/old-skill/SKILL.md" ]]
echo "OK  backup captured owned surfaces"

grt_stage_owned
grt_validate_stage
echo "OK  staged tree validates"

grt_atomic_swap
[[ -f "$GRT_SKILLS/impeccable/SKILL.md" ]]
[[ ! -d "$GRT_SKILLS/old-skill" ]]
[[ -f "$GRT_RULES/00-routing.md" ]]
grep -q 'at most one verification specialist' "$GRT_RULES/00-routing.md"
echo "OK  swap published staged skills"

echo corrupted > "$GRT_RULES/00-routing.md"
grt_restore_backup
grep -q 'old-rule' "$GRT_RULES/00-routing.md"
[[ -f "$GRT_SKILLS/old-skill/SKILL.md" ]]
echo "OK  restore rolls back to the backup"

printf 'test-install-transaction passed\n'
