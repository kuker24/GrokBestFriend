#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export HOME="$tmp/home-user"
export GRT_HOME="$tmp/home"
export GRT_DRY_RUN=0
export GRT_SKIP_TOOLS=1
export GRT_SKIP_DESIGN_BANK=1
mkdir -p "$HOME" "$GRT_HOME"

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/design-intelligence-bank.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/transaction.sh"

fail() { echo "FAIL $*" >&2; exit 1; }

[[ "${GRT_DI_BANK_REQUEST:-0}" == 0 ]] || fail "default request should be off"
grt_di_resolve_request
[[ -z "${GRT_DI_ARCHIVE_DIR:-}" ]] || fail "default must not pick an archive dir"
echo "OK  installer without flag is backward compatible"

GRT_DI_BANK_REQUEST=1
GRT_DI_ARCHIVE_DIR=""
unset GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR
if (grt_di_resolve_request) 2>"$tmp/need.err"; then
  fail "request without path/env should fail"
fi
grep -q DESIGN_INTELLIGENCE_ARCHIVE_DIR_REQUIRED "$tmp/need.err" || fail "missing required code"
echo "OK  flag without path/env fails"

write_marker() {
  local dir="$1" kind="$2" tx="$3"
  mkdir -p "$dir"
  cat >"$dir/.grokbestfriend-di-transaction.json" <<EOF
{"kind":"$kind","target":"~/DesignIntelligence","transaction_id":"$tx"}
EOF
}

# Interrupted staging is dropped without touching a missing target.
mkdir -p "$GRT_HOME/runtime/tx"
staging="$HOME/DesignIntelligence.stage.deadbeef"
mkdir -m 700 "$staging"
echo x >"$staging/keep"
write_marker "$staging" "design-intelligence-stage" "deadbeef"
GRT_DI_STAGING="$staging"
cat >"$(grt_tx_path)" <<EOF
{
  "state": "BANK_STAGED",
  "stamp": "deadbeef",
  "created_this_run": {"design_intelligence_bank": true},
  "design_intelligence": {
    "action": "create",
    "created_this_run": true,
    "staging": "$staging",
    "target": "~/DesignIntelligence",
    "target_path": "$HOME/DesignIntelligence",
    "transaction_id": "deadbeef"
  }
}
EOF
grt_tx_check_stale
[[ ! -e "$staging" ]] || fail "BANK_STAGED leftover staging was not removed"
[[ ! -e "$HOME/DesignIntelligence" ]] || fail "stale staged tx created the target"
echo "OK  interrupted import can be recovered"

# Fresh process must reload journal instead of inheriting empty shell vars.
staging="$HOME/DesignIntelligence.stage.freshproc"
mkdir -m 700 "$staging"
echo leftover >"$staging/keep"
write_marker "$staging" "design-intelligence-stage" "freshproc"
mkdir -p "$GRT_HOME/runtime/tx"
cat >"$(grt_tx_path)" <<EOF
{
  "state": "BANK_STAGED",
  "stamp": "freshproc",
  "created_this_run": {"design_intelligence_bank": true},
  "design_intelligence": {
    "action": "create",
    "created_this_run": true,
    "staging": "$staging",
    "target": "~/DesignIntelligence",
    "target_path": "$HOME/DesignIntelligence",
    "transaction_id": "freshproc"
  }
}
EOF
env -u GRT_DI_STAGING -u GRT_DI_CREATED -u GRT_DI_TARGET -u GRT_DI_TX_ID \
  HOME="$HOME" GRT_HOME="$GRT_HOME" GRT_ROOT="$ROOT" \
  bash --noprofile --norc -c '
    set -euo pipefail
    source "$GRT_ROOT/lib/common.sh"
    source "$GRT_ROOT/lib/design-intelligence-bank.sh"
    source "$GRT_ROOT/lib/transaction.sh"
    [[ -z "${GRT_DI_STAGING:-}" ]] || exit 2
    grt_tx_check_stale
  ' || fail "fresh-process BANK_STAGED recovery failed"
[[ ! -e "$staging" ]] || fail "fresh process left orphan staging"
echo "OK  fresh-process recovery removes journaled staging"

# Failure after promotion moves a created bank to recovery and leaves a reused bank alone.
created="$HOME/DesignIntelligence"
mkdir -p "$created"
echo created >"$created/marker"
write_marker "$created" "design-intelligence-bank" "promoted1"
GRT_DI_CREATED=1
GRT_DI_TX_ID="promoted1"
grt_di_recover_promoted
[[ ! -e "$created" ]] || fail "promoted bank was not moved"
[[ -n "${GRT_DI_RECOVERY:-}" && -f "$GRT_DI_RECOVERY/marker" ]] || fail "recovery location missing"
echo "OK  failure after promotion activates recovery"

# Fresh process BANK_PROMOTED recovery
rm -rf -- "$HOME"/DesignIntelligence.recovery.*
created="$HOME/DesignIntelligence"
mkdir -p "$created"
echo created >"$created/marker"
write_marker "$created" "design-intelligence-bank" "freshprom"
cat >"$(grt_tx_path)" <<EOF
{
  "state": "BANK_PROMOTED",
  "stamp": "freshprom",
  "created_this_run": {"design_intelligence_bank": true},
  "design_intelligence": {
    "action": "create",
    "created_this_run": true,
    "staging": null,
    "target": "~/DesignIntelligence",
    "target_path": "$created",
    "transaction_id": "freshprom"
  }
}
EOF
env -u GRT_DI_STAGING -u GRT_DI_CREATED -u GRT_DI_TARGET -u GRT_DI_TX_ID \
  HOME="$HOME" GRT_HOME="$GRT_HOME" GRT_ROOT="$ROOT" GRT_TX_RECOVER=1 \
  bash --noprofile --norc -c '
    set -euo pipefail
    source "$GRT_ROOT/lib/common.sh"
    source "$GRT_ROOT/lib/design-intelligence-bank.sh"
    source "$GRT_ROOT/lib/transaction.sh"
    [[ -z "${GRT_DI_CREATED:-}" || "${GRT_DI_CREATED}" == 0 ]] || exit 2
    grt_tx_check_stale
  ' || fail "fresh-process BANK_PROMOTED recovery failed"
[[ ! -e "$created" ]] || fail "fresh process left promoted bank in place"
shopt -s nullglob
recovered=( "$HOME"/DesignIntelligence.recovery.* )
shopt -u nullglob
[[ ${#recovered[@]} -eq 1 && -f "${recovered[0]}/marker" ]] || fail "fresh process did not move bank to recovery"
echo "OK  fresh-process recovery moves journaled created bank"

reuse="$HOME/DesignIntelligence"
mkdir -p "$reuse"
echo keep >"$reuse/safe"
GRT_DI_CREATED=0
GRT_DI_RECOVERY=""
grt_di_recover_promoted
[[ -f "$reuse/safe" ]] || fail "reused bank was moved"
echo "OK  reused existing bank is not moved"

# Stale reuse manifest is replaced atomically.
mkdir -p "$GRT_RUNTIME"
printf '%s\n' '{"snapshot":"STALE_CANARY","generationId":"stale"}' >"$GRT_RUNTIME/di-manifest.json"
GRT_DI_MANIFEST_FILE="$GRT_RUNTIME/di-manifest.json"
rm -f -- "$GRT_DI_MANIFEST_FILE"
printf '%s\n' '{"manifest":{"snapshot":"od-test-minifixture-v1.3.1","generationId":"abc","items":3,"path":"~/DesignIntelligence","bank":"installed"},"bank_integrity":"PASS","bank_content_readiness":"DEGRADED","install_result":"SUCCESS_WITH_EXPECTED_LIMITATIONS"}' >"$tmp/reuse-payload.json"
grt_di_commit_manifest "$tmp/reuse-payload.json" >/dev/null
grep -q 'od-test-minifixture-v1.3.1' "$GRT_DI_MANIFEST_FILE" || fail "reuse manifest missing snapshot"
! grep -q STALE_CANARY "$GRT_DI_MANIFEST_FILE" || fail "stale manifest canary survived"
echo "OK  reuse manifest is rewritten without stale canary"

# Uninstall retains user bank.
mkdir -p "$GRT_HOME"
printf '%s\n' 'user' >"$reuse/safe"
# shellcheck source=/dev/null
# Uninstall script is a process; invoke it in dry-run.
if ! HOME="$HOME" GRT_HOME="$GRT_HOME" "$ROOT/uninstall.sh" --dry-run >"$tmp/un.out"; then
  fail "uninstall dry-run failed"
fi
grep -qi 'retained\|user data' "$tmp/un.out" || fail "uninstall did not report retained bank"
[[ -f "$reuse/safe" ]] || fail "uninstall removed the bank"
echo "OK  uninstall retains bank"

# restore --list mentions bank journal fields when present.
mkdir -p "$(grt_backup_root)/20260817T000000Z-1-deadbeef"
cat >"$(grt_backup_root)/20260817T000000Z-1-deadbeef/journal.json" <<'EOF'
{
  "state": "COMMITTED",
  "created_this_run": {"design_intelligence_bank": true},
  "design_intelligence": {"action": "create", "snapshot": "od-packs-2026-07-20"}
}
EOF
"$ROOT/restore.sh" --list >"$tmp/list.out"
grep -q 'di_created=true' "$tmp/list.out" || fail "restore --list missing bank creation"
echo "OK  restore --list explains bank-creating transactions"

# No raw archives in git
if git -C "$ROOT" ls-files -- '*.zip' | grep -q .; then
  fail "raw archives are tracked"
fi
echo "OK  raw archives are not committed"

printf 'test-design-intelligence-bank-install passed\n'
