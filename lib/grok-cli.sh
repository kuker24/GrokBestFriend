#!/usr/bin/env bash

grt_install_grok_cli() {
  if grt_have grok || [[ -x "$HOME/.grok/bin/grok" ]]; then
    grt_info "grok CLI already present"
    return 0
  fi
  local url
  url="$(python3 - "$GRT_VENDOR/sources.json" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(data.get("grok", {}).get("installUrl", "https://x.ai/cli/install.sh"))
PY
)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_INSTALL_GROK $url"
    return 0
  fi
  grt_info "Installing Grok CLI from official installer"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$url" | bash
  [[ -x "$HOME/.grok/bin/grok" ]] || grt_have grok || grt_die "grok install finished but binary is missing"
}

grt_require_grok_version() {
  local wanted output
  wanted="$(grt_grok_seen_version)"
  [[ -n "$wanted" ]] || return 0
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_CHECK_GROK_VERSION $wanted"
    return 0
  fi
  grt_find_grok
  output="$("$GRT_GROK" --version 2>/dev/null || true)"
  grt_version_contains "$output" "$wanted" || grt_die "grok version mismatch: wanted $wanted, got $output"
}

grt_ensure_path() {
  local extra="$HOME/.grok/bin:$HOME/.local/bin"
  case ":$PATH:" in
    *":$HOME/.grok/bin:"*) ;;
    *) export PATH="$HOME/.grok/bin:$PATH" ;;
  esac
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
  esac

  local rc=""
  if [[ -n "${BASH_VERSION:-}" && -f "$HOME/.bashrc" ]]; then
    rc="$HOME/.bashrc"
  elif [[ -n "${ZSH_VERSION:-}" && -f "$HOME/.zshrc" ]]; then
    rc="$HOME/.zshrc"
  elif [[ -f "$HOME/.bashrc" ]]; then
    rc="$HOME/.bashrc"
  fi

  if [[ -z "$rc" ]]; then
    grt_info "Add to PATH: export PATH=\"$extra:\$PATH\""
    return 0
  fi
  GRT_RC_PATH="$rc"
  if grep -Fq "$GRT_PATH_MARKER" "$rc"; then
    return 0
  fi
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_APPEND_PATH $rc"
    return 0
  fi
  {
    printf '\n%s\n' "$GRT_PATH_MARKER"
    printf 'export PATH="$HOME/.grok/bin:$HOME/.local/bin:$PATH"\n'
  } >>"$rc"
  GRT_CREATED_PATH_MARKER=1
  grt_info "Appended PATH helper to $rc"
}

grt_hint_design_bank() {
  local candidate="$HOME/Downloads/LAB GITHUB/Design"
  if [[ -d "$candidate/Refero" && -d "$candidate/motionsites" ]]; then
    grt_info "Design bank present at $candidate — export GROK_DESIGN_BANK=\"$candidate\""
  fi
}
