#!/usr/bin/env bash

grt_doctor() {
  local failed=0
  grt_find_grok
  grt_require python3

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

  check "grok binary" test -x "$GRT_GROK"
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
  check "serena" grt_have serena
  check "browser-act" grt_have browser-act
  check "gh" grt_have gh
  check "semgrep" grt_have semgrep
  check "osv-scanner" grt_have osv-scanner
  check "gitleaks" grt_have gitleaks
  check "chromium helper" test -x "$GRT_HOME/bin/grok-chromium-cdp"
  check "chromium binary" "$GRT_HOME/bin/grok-chromium-cdp" resolve
  if [[ "$GRT_SKIP_DESIGN_BANK" == 1 ]]; then
    grt_info "SKIP design bank"
  else
    check "design bank catalogs" grt_find_design_bank
  fi

  local skill
  for skill in adhd ask-matt browser-act chrome-devtools-axi emil-design-eng found-this-design full-audit-keamanan full-performance-audit gh-axi grill-with-docs impeccable matt-code-review matt-implement scroll-world tdd to-spec to-tickets visual-studio; do
    check "skill $skill" test -f "$GRT_SKILLS/$skill/SKILL.md"
  done

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

  "$GRT_GROK" mcp list

  local mcp_json
  mcp_json="$("$GRT_GROK" mcp list --json 2>/dev/null || true)"
  python3 - "$mcp_json" <<'PY' || failed=1
import json, sys
raw = sys.argv[1]
try:
    data = json.loads(raw) if raw else {}
except json.JSONDecodeError:
    print("ERROR: FAIL mcp list --json", file=sys.stderr)
    raise SystemExit(1)

servers = data if isinstance(data, list) else data.get("servers") or data.get("mcp_servers") or []
if isinstance(servers, dict):
    items = [{"name": name, **(value if isinstance(value, dict) else {})} for name, value in servers.items()]
else:
    items = servers

by_name = {}
for item in items:
    if isinstance(item, dict):
        name = item.get("name") or item.get("id")
        if name:
            by_name[name] = item

required = ["codebase-memory-mcp", "context7", "exa", "serena"]
missing = [name for name in required if name not in by_name]
if missing:
    print("ERROR: FAIL missing MCP: " + ", ".join(missing), file=sys.stderr)
    raise SystemExit(1)
print("OK  mcp servers registered: " + ", ".join(required))
PY

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
    grt_die "doctor found failures"
  fi
  grt_info "doctor passed"
}
