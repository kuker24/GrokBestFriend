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
  ./install.sh --restore [stamp]
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
    --restore) mode="restore" ;;
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
    grt_restore_backup "$restore_stamp"
    ;;
  install)
    grt_run_install
    if [[ "$GRT_DRY_RUN" == 1 ]]; then
      grt_info "dry-run complete"
    else
      if ! grt_doctor; then
        grt_restore_backup
        grt_die "doctor found failures; restored backup ${GRT_BACKUP_STAMP:-latest}"
      fi
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
