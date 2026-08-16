#!/usr/bin/env bash

grt_tool_version_ok() {
  local label="$1" command="$2" wanted="$3"
  shift 3
  if ! grt_have "$command"; then
    return 1
  fi
  local output
  output="$("$command" "$@" 2>/dev/null || true)"
  grt_version_contains "$output" "$wanted"
}

grt_doctor() {
  local failed=0
  local warned=0
  grt_find_grok
  grt_require python3
  grt_load_skill_allowlist

  check() {
    local label="$1"
    shift
    if "$@"; then
      grt_info "OK  $label"
    else
      grt_error "FAIL $label"
      failed=1
    fi
  }

  warn() {
    local label="$1"
    shift
    if "$@"; then
      grt_info "OK  $label"
    else
      grt_warn "WARN $label"
      warned=1
    fi
  }

  check "grok binary" test -x "$GRT_GROK"
  local wanted_grok
  wanted_grok="$(grt_grok_seen_version)"
  if [[ -n "$wanted_grok" ]]; then
    local grok_ver
    grok_ver="$("$GRT_GROK" --version 2>/dev/null || true)"
    if grt_version_contains "$grok_ver" "$wanted_grok"; then
      grt_info "OK  grok version $wanted_grok"
    else
      grt_error "FAIL grok version wanted $wanted_grok got $grok_ver"
      failed=1
    fi
  fi

  check "routing rule" test -f "$GRT_RULES/00-routing.md"
  check "verification rule" test -f "$GRT_RULES/01-verification.md"
  check "impeccable hook" test -f "$GRT_HOOKS/impeccable.json"
  check "manifest" test -f "$GRT_MANIFEST"
  check "impeccable skill" test -f "$GRT_SKILLS/impeccable/SKILL.md"
  check "no user implement override" test ! -e "$GRT_SKILLS/implement"
  check "no user code-review override" test ! -e "$GRT_SKILLS/code-review"
  check "claude implement ignored" grep -q '~/.claude/skills/implement' "$GRT_HOME/config.toml"
  check "matt-implement exists" test -f "$GRT_SKILLS/matt-implement/SKILL.md"
  check "matt-code-review exists" test -f "$GRT_SKILLS/matt-code-review/SKILL.md"
  check "codebase memory binary" test -x "$GRT_CODEBASE_MEMORY_BIN"
  if [[ -x "$GRT_CODEBASE_MEMORY_BIN" ]]; then
    local cbm_ver cbm_pin
    cbm_pin="$(grt_source_field codebase-memory version)"
    cbm_ver="$("$GRT_CODEBASE_MEMORY_BIN" --version 2>/dev/null || true)"
    if grt_version_contains "$cbm_ver" "$cbm_pin"; then
      grt_info "OK  codebase-memory $cbm_pin"
    else
      grt_error "FAIL codebase-memory version wanted $cbm_pin got $cbm_ver"
      failed=1
    fi
  fi
  check "serena" grt_have serena
  if grt_have serena; then
    check "serena version" grt_tool_version_ok "serena" serena "$(grt_source_field serena version)" --version
  fi
  check "browser-act" grt_have browser-act
  if grt_have browser-act; then
    check "browser-act version" grt_tool_version_ok "browser-act" browser-act "$(grt_source_field browser-act version)" --version
  fi
  warn "gh" grt_have gh
  check "semgrep" grt_have semgrep
  if grt_have semgrep; then
    check "semgrep version" grt_tool_version_ok "semgrep" semgrep "$(grt_source_field semgrep version)" --version
  fi
  check "osv-scanner" grt_have osv-scanner
  if grt_have osv-scanner; then
    check "osv-scanner version" grt_tool_version_ok "osv-scanner" osv-scanner "$(grt_source_field osv-scanner version)" --version
  fi
  check "gitleaks" grt_have gitleaks
  if grt_have gitleaks; then
    check "gitleaks version" grt_tool_version_ok "gitleaks" gitleaks "$(grt_source_field gitleaks version)" version
  fi
  check "chromium helper" test -x "$GRT_HOME/bin/grok-chromium-cdp"
  check "chromium binary" "$GRT_HOME/bin/grok-chromium-cdp" resolve
  if [[ "$GRT_SKIP_DESIGN_BANK" == 1 ]]; then
    grt_info "SKIP design bank"
  else
    check "design bank catalogs" grt_find_design_bank
  fi

  local skill
  for skill in "${GRT_SKILLS_VENDOR[@]}"; do
    check "skill $skill" test -f "$GRT_SKILLS/$skill/SKILL.md"
  done

  python3 "$GRT_ROOT/lib/validate_skills.py" --skills "$GRT_SKILLS" --routing "$GRT_RULES/00-routing.md" || failed=1

  if grep -R -n -E '/home/[^/]+/' "$GRT_SKILLS" >/dev/null 2>&1; then
    grt_error "FAIL live skills still contain a machine home path"
    failed=1
  else
    grt_info "OK  no machine home paths in skills"
  fi

  if grt_have browser-act && browser-act browser list 2>/dev/null | grep -q 'type=chrome-direct'; then
    grt_error "FAIL browser-act chrome-direct still registered"
    failed=1
  else
    grt_info "OK  no browser-act chrome-direct"
  fi

  if grep -A6 '^\[compat.claude\]' "$GRT_HOME/config.toml" | grep -q 'skills = true'; then
    grt_error "FAIL compat.claude skills is on"
    failed=1
  else
    grt_info "OK  compat.claude remains off"
  fi

  if grep -q 'xAI Official' "$GRT_HOME/config.toml"; then
    grt_info "OK  official marketplace source"
  else
    grt_error "FAIL official marketplace source missing"
    failed=1
  fi

  if [[ -x "$GRT_CODEBASE_MEMORY_BIN" ]]; then
    python3 "$GRT_ROOT/lib/index_status.py" --bin "$GRT_CODEBASE_MEMORY_BIN" --cwd "$PWD" || true
  fi

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "SKIP live grok inspect in dry-run"
    return "$failed"
  fi

  local inspect
  inspect="$("$GRT_GROK" inspect 2>/dev/null || true)"
  printf '%s\n' "$inspect" | grep -q 'matt-implement' && grt_info "OK  inspect sees matt-implement" || { grt_error "FAIL inspect missing matt-implement"; failed=1; }
  printf '%s\n' "$inspect" | grep -q 'found-this-design' && grt_info "OK  inspect sees found-this-design" || { grt_error "FAIL inspect missing found-this-design"; failed=1; }
  printf '%s\n' "$inspect" | grep -q 'codebase-memory-mcp' && grt_info "OK  inspect sees codebase-memory-mcp" || { grt_error "FAIL inspect missing codebase-memory-mcp"; failed=1; }
  "$GRT_GROK" inspect --json 2>/dev/null | python3 -c '
import json,sys
skills=json.load(sys.stdin).get("skills") or []
impl=[s for s in skills if s.get("name")=="implement"]
src=(impl[0].get("source") or {}).get("type") if impl else None
if src=="bundled":
    print("OK  bundled /implement is visible")
else:
    print("ERROR: FAIL bundled /implement not visible; source=%s" % src, file=sys.stderr)
    raise SystemExit(1)
' || failed=1

  local list_tmp doctor_tmp
  list_tmp="$(mktemp)"
  doctor_tmp="$(mktemp)"
  if ! "$GRT_GROK" mcp list --json >"$list_tmp"; then
    grt_error "FAIL mcp list --json"
    failed=1
  elif ! "$GRT_GROK" mcp doctor --json >"$doctor_tmp"; then
    grt_error "FAIL mcp doctor --json"
    failed=1
  else
    if python3 "$GRT_ROOT/lib/mcp_state.py" \
      --policy "$GRT_VENDOR/mcp-policy.json" \
      --list-json "$list_tmp" \
      --doctor-json "$doctor_tmp" \
      --memory-bin "$GRT_CODEBASE_MEMORY_BIN" \
      --serena-bin "$(command -v serena 2>/dev/null || true)"; then
      grt_info "OK  mcp policy + health"
    else
      failed=1
    fi
  fi
  rm -f -- "$list_tmp" "$doctor_tmp"

  if command -v "$GRT_GROK" >/dev/null 2>&1; then
    local plugins
    plugins="$("$GRT_GROK" plugin list 2>/dev/null || true)"
    if printf '%s\n' "$plugins" | grep -qi 'No plugins installed'; then
      grt_info "OK  no Grok plugins (matches this snapshot)"
    else
      grt_info "NOTE plugin list: $plugins"
    fi
  fi

  if [[ "$failed" -ne 0 ]]; then
    return 1
  fi
  grt_info "doctor passed"
  return 0
}
