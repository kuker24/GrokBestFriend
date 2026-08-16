#!/usr/bin/env bash

grt_mcp_list_json() {
  "$GRT_GROK" mcp list --json
}

grt_mcp_assert() {
  local require_disabled=()
  local arg
  for arg in "$@"; do
    require_disabled+=(--require-disabled "$arg")
  done
  local list_json
  list_json="$(grt_mcp_list_json)" || grt_die "grok mcp list --json failed"
  printf '%s\n' "$list_json" | python3 "$GRT_ROOT/lib/mcp_state.py" \
    --policy "$GRT_VENDOR/mcp-policy.json" \
    --memory-bin "$GRT_CODEBASE_MEMORY_BIN" \
    --serena-bin "$(command -v serena 2>/dev/null || true)" \
    "${require_disabled[@]}"
}

grt_mcp_add_stdio() {
  local name="$1"
  shift
  grt_info "MCP add $name (stdio)"
  "$GRT_GROK" mcp add --scope user "$name" -- "$@"
}

grt_mcp_add_http() {
  local name="$1" url="$2"
  grt_info "MCP add $name (http)"
  "$GRT_GROK" mcp add --transport http --scope user "$name" "$url"
}

grt_mcp_disable_strict() {
  local name="$1"
  grt_info "MCP disable $name"
  "$GRT_GROK" mcp disable "$name"
  grt_mcp_assert "$name"
}

grt_install_mcp() {
  local serena_bin
  grt_find_grok

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    serena_bin="$(command -v serena 2>/dev/null || printf '%s' 'serena')"
    grt_info "WOULD_MCP codebase-memory-mcp -- $GRT_CODEBASE_MEMORY_BIN"
    grt_info "WOULD_MCP context7 http https://mcp.context7.com/mcp"
    grt_info "WOULD_MCP exa http https://mcp.exa.ai/mcp"
    grt_info "WOULD_MCP serena -- $serena_bin start-mcp-server --context agent --project-from-cwd --open-web-dashboard false"
    grt_info "WOULD_MCP disable serena"
    grt_info "WOULD_MCP disable exa"
    grt_info "WOULD_MCP assert policy"
    return 0
  fi

  [[ -x "$GRT_CODEBASE_MEMORY_BIN" ]] || grt_die "Codebase Memory binary missing: $GRT_CODEBASE_MEMORY_BIN"
  grt_have serena || grt_die "serena is not on PATH"
  serena_bin="$(command -v serena)"

  grt_mcp_add_stdio codebase-memory-mcp "$GRT_CODEBASE_MEMORY_BIN"
  grt_mcp_add_http context7 "https://mcp.context7.com/mcp"
  grt_mcp_add_http exa "https://mcp.exa.ai/mcp"
  grt_mcp_add_stdio serena "$serena_bin" start-mcp-server --context agent --project-from-cwd --open-web-dashboard false
  grt_rewrite_mcp_paths "$serena_bin"
  grt_info "MCP disable serena"
  "$GRT_GROK" mcp disable serena
  grt_info "MCP disable exa"
  "$GRT_GROK" mcp disable exa
  grt_mcp_assert serena exa
}

grt_rewrite_mcp_paths() {
  local serena_bin="$1"
  python3 - "$GRT_HOME/config.toml" "$GRT_CODEBASE_MEMORY_BIN" "$serena_bin" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
memory_bin = sys.argv[2]
serena_bin = sys.argv[3]
text = path.read_text(encoding="utf-8")
updated = text
# Keep command lines pointing at the portable binaries even if mcp add was a no-op.
import re
updated = re.sub(
    r'(?m)^(\[mcp_servers\.codebase-memory-mcp\][\s\S]*?^command = )".*"',
    lambda m: f'{m.group(1)}"{memory_bin}"',
    updated,
    count=1,
)
updated = re.sub(
    r'(?m)^(\[mcp_servers\.serena\][\s\S]*?^command = )".*"',
    lambda m: f'{m.group(1)}"{serena_bin}"',
    updated,
    count=1,
)
if updated != text:
    path.write_text(updated, encoding="utf-8")
PY
}
