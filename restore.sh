#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/design-intelligence-bank.sh"
source "$ROOT/lib/transaction.sh"

usage() {
  cat <<'EOF'
Restore the last GrokBestFriend backup, or a named stamp.

Usage:
  ./restore.sh
  ./restore.sh 20260816T120000Z
  ./restore.sh --list
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--list" ]]; then
  root="$(grt_backup_root)"
  if [[ ! -d "$root" ]]; then
    grt_info "no backups"
    exit 0
  fi
  shopt -s nullglob
  for entry in "$root"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z*; do
    [[ -d "$entry" ]] || continue
    if [[ -f "$entry/journal.json" ]]; then
      python3 - "$entry/journal.json" "$(basename -- "$entry")" <<'PY'
import json, sys
from pathlib import Path
journal = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
stamp = sys.argv[2]
di = journal.get("design_intelligence") or {}
created = (journal.get("created_this_run") or {}).get("design_intelligence_bank")
print(
    f"{stamp} state={journal.get('state') or ''} "
    f"di_action={di.get('action') or 'skip'} "
    f"di_created={str(bool(created)).lower()} "
    f"di_snapshot={di.get('snapshot') or '-'}"
)
PY
    else
      basename -- "$entry"
    fi
  done
  shopt -u nullglob
  if [[ -f "$root/LATEST" ]]; then
    grt_info "LATEST=$(cat "$root/LATEST")"
  fi
  exit 0
fi

grt_lock_begin
trap 'grt_lock_end' EXIT
GRT_TX_RECOVER=1
grt_tx_check_stale
grt_restore_backup "${1:-}"
