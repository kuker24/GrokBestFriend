#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/transaction.sh"

purge_tools=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) GRT_DRY_RUN=1 ;;
    --purge-tools) purge_tools=1 ;;
    -h|--help)
      cat <<'EOF'
Remove GrokBestFriend-owned skills, rules, hooks, helper, and manifest.

Usage:
  ./uninstall.sh
  ./uninstall.sh --dry-run
  ./uninstall.sh --purge-tools

Does not remove the Grok CLI, auth.json, sessions, or config.toml tokens.
--purge-tools also removes uv-installed serena/browser-act/semgrep if present.
EOF
      exit 0
      ;;
    *) grt_die "Unknown argument: $arg" ;;
  esac
done

grt_backup_owned
grt_uninstall_owned

if [[ "$purge_tools" == 1 ]]; then
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_PURGE uv tools serena-agent browser-act-cli semgrep"
  else
    if command -v uv >/dev/null 2>&1; then
      uv tool uninstall serena-agent >/dev/null 2>&1 || true
      uv tool uninstall browser-act-cli >/dev/null 2>&1 || true
      uv tool uninstall semgrep >/dev/null 2>&1 || true
    fi
    grt_info "purged optional uv tools (gitleaks/osv-scanner left in ~/.local/bin)"
  fi
fi
