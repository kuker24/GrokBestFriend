#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/grok-cli.sh"
source "$ROOT/lib/tools.sh"
source "$ROOT/lib/config.sh"
source "$ROOT/lib/mcp.sh"
source "$ROOT/lib/design-bank.sh"
source "$ROOT/lib/transaction.sh"
source "$ROOT/lib/install.sh"
source "$ROOT/lib/doctor.sh"

usage() {
  cat <<'EOF'
Install this machine's GrokBuild system onto a new laptop.

Usage:
  ./install.sh --dry-run
  ./install.sh
  ./install.sh --doctor
  ./install.sh --doctor --strict
  ./install.sh --restore [stamp]
  ./install.sh --recover
  ./install.sh --skip-tools
  ./install.sh --skip-design-bank

Does:
  - install the official Grok CLI if missing
  - copy vendored skills, rules, and the impeccable hook
  - merge sanitized ~/.grok/config.toml (no tokens)
  - install serena, browser-act, semgrep, osv-scanner, gitleaks
  - install Codebase Memory under ~/.grok/runtime/components/
  - register MCP servers (serena and exa stay disabled)
  - install grok-chromium-cdp
  - restore the Refero + Motionsites design bank to ~/Design
  - leave bundled /implement and /review unshadowed
  - leave [compat.claude] off

Does not:
  - copy auth.json, sessions, or trusted folders
  - copy tokens, gateway URLs, or model mappings
  - install Grok marketplace plugins (none are installed on the source machine)
  - launch Google Chrome
EOF
}

mode="install"
restore_stamp=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) GRT_DRY_RUN=1 ;;
    --doctor) mode="doctor" ;;
    --strict) GRT_DOCTOR_STRICT=1 ;;
    --restore) mode="restore" ;;
    --recover) mode="recover" ;;
    --skip-tools) GRT_SKIP_TOOLS=1 ;;
    --skip-design-bank) GRT_SKIP_DESIGN_BANK=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      if [[ "$mode" == "restore" && -z "$restore_stamp" && "$arg" != --* ]]; then
        restore_stamp="$arg"
      else
        grt_die "Unknown argument: $arg"
      fi
      ;;
  esac
done

case "$mode" in
  doctor)
    grt_doctor || grt_die "doctor found failures"
    ;;
  restore)
    grt_lock_begin
    GRT_TX_RECOVER=1
    grt_tx_check_stale
    trap 'grt_lock_end' EXIT
    grt_restore_backup "$restore_stamp"
    ;;
  recover)
    grt_lock_begin
    GRT_TX_RECOVER=1
    stamp="$(grt_tx_stamp)"
    [[ -n "$stamp" ]] || stamp="$(grt_latest_backup_stamp || true)"
    [[ -n "$stamp" ]] || { grt_lock_end; grt_die "no incomplete transaction to recover"; }
    trap 'grt_lock_end' EXIT
    grt_restore_backup "$stamp"
    grt_info "recovered managed surfaces from $stamp"
    ;;
  install)
    trap 'grt_tx_on_signal' ERR INT TERM
    grt_run_install
    if [[ "$GRT_DRY_RUN" == 1 ]]; then
      grt_info "dry-run complete"
      grt_lock_end
    else
      if ! grt_doctor; then
        GRT_TX_IN_HANDLER=1
        grt_restore_backup
        grt_lock_end
        grt_die "doctor found failures; restored backup ${GRT_BACKUP_STAMP:-latest}"
      fi
      grt_tx_set_state COMMITTED
      grt_tx_clear
      grt_lock_end
      cat <<'EOF'

Next (human only):
  grok login
  gh auth login
  # later, if you finish Exa OAuth: grok mcp enable exa
  # later, for exact symbol work:   grok mcp enable serena
EOF
    fi
    ;;
esac
