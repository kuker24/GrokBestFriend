#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/lib/common.sh"
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
  ls -1 "$root" | grep -E '^[0-9]{8}T[0-9]{6}Z$' || true
  if [[ -f "$root/LATEST" ]]; then
    grt_info "LATEST=$(cat "$root/LATEST")"
  fi
  exit 0
fi

grt_restore_backup "${1:-}"
