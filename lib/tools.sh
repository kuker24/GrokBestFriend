#!/usr/bin/env bash

grt_install_uv() {
  if grt_have uv; then
    return 0
  fi
  local url
  url="$(grt_source_field uv installUrl)"
  [[ -n "$url" ]] || url="https://astral.sh/uv/install.sh"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_INSTALL_UV $url"
    return 0
  fi
  grt_info "Installing uv"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$url" | sh
  export PATH="$HOME/.local/bin:$PATH"
  grt_have uv || grt_die "uv install finished but uv is not on PATH"
}

grt_uv_tool() {
  local spec="$1" python="${2:-}"
  local pkg ver
  pkg="${spec%%==*}"
  ver="${spec#*==}"
  if [[ "$spec" == "$pkg" ]]; then
    ver=""
  fi
  if [[ -n "$ver" ]] && uv tool list 2>/dev/null | grep -E "^${pkg} v${ver}([[:space:]]|$)" >/dev/null; then
    grt_info "uv tool $pkg $ver already installed"
    return 0
  fi
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_UV_TOOL $spec ${python:+--python $python}"
    return 0
  fi
  grt_install_uv
  if [[ -n "$python" ]]; then
    uv tool install --force --python "$python" "$spec"
  else
    uv tool install --force "$spec"
  fi
}

grt_install_scanners() {
  local dest="$HOME/.local/bin"
  local gitleaks_url gitleaks_sha osv_url osv_sha tmp

  if grt_have semgrep; then
    grt_info "semgrep already present"
  else
    grt_uv_tool "semgrep==$(grt_source_field semgrep version)"
  fi

  gitleaks_url="$(grt_source_field gitleaks artifactUrl)"
  gitleaks_sha="$(grt_source_field gitleaks artifactSha256)"
  osv_url="$(grt_source_field osv-scanner artifactUrl)"
  osv_sha="$(grt_source_field osv-scanner artifactSha256)"

  if grt_have gitleaks; then
    grt_info "gitleaks already present"
  else
    if [[ "$GRT_DRY_RUN" == 1 ]]; then
      grt_info "WOULD_INSTALL gitleaks $gitleaks_url"
    else
      tmp="$(mktemp -d)"
      grt_download "$gitleaks_url" "$tmp/gitleaks.tgz" "$gitleaks_sha"
      tar -xzf "$tmp/gitleaks.tgz" -C "$tmp"
      mkdir -p -- "$dest"
      install -m 755 "$tmp/gitleaks" "$dest/gitleaks"
      rm -rf -- "$tmp"
    fi
  fi

  if grt_have osv-scanner; then
    grt_info "osv-scanner already present"
  else
    if [[ "$GRT_DRY_RUN" == 1 ]]; then
      grt_info "WOULD_INSTALL osv-scanner $osv_url"
    else
      mkdir -p -- "$dest"
      grt_download "$osv_url" "$dest/osv-scanner" "$osv_sha"
      chmod 755 -- "$dest/osv-scanner"
    fi
  fi
}

grt_install_codebase_memory() {
  local version artifact expected target stage claude_bin
  version="$(grt_source_field codebase-memory version)"
  artifact="$(grt_source_field codebase-memory artifactUrl)"
  expected="$(grt_source_field codebase-memory artifactSha256)"
  target="$GRT_CODEBASE_MEMORY_BIN"
  claude_bin="${HOME}/.claude/runtime/components/codebase-memory/bin/codebase-memory-mcp"

  if [[ -x "$target" ]]; then
    if "$target" --version 2>/dev/null | grep -Fq "$version"; then
      grt_info "codebase-memory $version already installed"
      return 0
    fi
  fi

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_INSTALL codebase-memory $version -> $target"
    return 0
  fi

  if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    grt_die "codebase-memory pinned artifact is Linux x86_64 only"
  fi

  mkdir -p -- "$(dirname -- "$target")"
  if [[ -x "$claude_bin" ]] && "$claude_bin" --version 2>/dev/null | grep -Fq "$version"; then
    grt_info "Copying existing codebase-memory $version into $target"
    cp -a -- "$claude_bin" "$target"
    chmod 755 -- "$target"
    return 0
  fi

  stage="$(mktemp -d)"
  grt_download "$artifact" "$stage/cbm.tgz" "$expected"
  tar -xzf "$stage/cbm.tgz" -C "$stage"
  [[ -x "$stage/codebase-memory-mcp" ]] || grt_die "codebase-memory binary missing from archive"
  "$stage/codebase-memory-mcp" --version 2>/dev/null | grep -Fq "$version" || grt_die "codebase-memory version mismatch"
  install -m 755 "$stage/codebase-memory-mcp" "$target"
  rm -rf -- "$stage"
}

grt_install_tools() {
  if [[ "$GRT_SKIP_TOOLS" == 1 ]]; then
    grt_info "skipping tool installs"
    return 0
  fi
  grt_install_uv
  grt_uv_tool "serena-agent==$(grt_source_field serena version)" "$(grt_source_field serena python)"
  grt_uv_tool "browser-act-cli==$(grt_source_field browser-act version)" "$(grt_source_field browser-act python)"
  grt_install_scanners
  grt_install_codebase_memory

  if ! grt_have gh; then
    grt_warn "gh is not installed. On Ubuntu: sudo apt install gh   then run: gh auth login"
  fi
  if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 && [[ ! -x /usr/bin/chromium && ! -x /snap/bin/chromium ]]; then
    grt_warn "Chromium is not installed. Install the Chromium package (not Google Chrome)."
  fi
}
