#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/transaction.sh"

purge_tools=0
purge_learning=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) GRT_DRY_RUN=1 ;;
    --purge-tools) purge_tools=1 ;;
    --purge-learning) purge_learning=1 ;;
    -h|--help)
      cat <<'EOF'
Remove GrokBestFriend-owned skills, rules, hooks, helper, and manifest.

Usage:
  ./uninstall.sh
  ./uninstall.sh --dry-run
  ./uninstall.sh --purge-tools
  ./uninstall.sh --purge-learning

Does not remove the Grok CLI, auth.json, sessions, foreign skills, or config.toml tokens.
Does not remove ~/.grok/runtime/learning unless --purge-learning.
Does not remove ~/DesignIntelligence; that bank is user data.
--purge-tools also removes uv-installed serena/browser-act/semgrep if present.
EOF
      exit 0
      ;;
    *) grt_die "Unknown argument: $arg" ;;
  esac
done

grt_lock_begin
trap 'grt_lock_end' EXIT
grt_tx_check_stale
grt_backup_owned
grt_uninstall_owned
if [[ -d "${GROK_DESIGN_INTELLIGENCE_BANK:-$HOME/DesignIntelligence}" ]]; then
  grt_info "Design Intelligence bank retained at ${GROK_DESIGN_INTELLIGENCE_BANK:-$HOME/DesignIntelligence} (user data)"
else
  grt_info "Design Intelligence bank not present; nothing to retain"
fi
if [[ "$purge_learning" == 1 ]]; then
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_PURGE learning log and hmac key"
  else
    rm -f -- "$GRT_HOME/runtime/learning/events.jsonl" "$GRT_HOME/runtime/learning/hmac.key"
    grt_info "purged learning log"
  fi
fi

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
