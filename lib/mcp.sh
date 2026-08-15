#!/usr/bin/env bash

grt_mcp_has() {
  local name="$1"
  "$GRT_GROK" mcp list --json 2>/dev/null | python3 - "$name" <<'PY'
import json, sys
name = sys.argv[1]
raw = sys.stdin.read().strip()
try:
    data = json.loads(raw) if raw else {}
except json.JSONDecodeError:
    raise SystemExit(1)
servers = data if isinstance(data, list) else data.get("servers") or data.get("mcp_servers") or []
if isinstance(servers, dict):
    items = [{"name": k, **(v if isinstance(v, dict) else {})} for k, v in servers.items()]
else:
    items = servers
for item in items:
    if isinstance(item, dict) and (item.get("name") or item.get("id")) == name:
        raise SystemExit(0)
raise SystemExit(1)
PY
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
    return 0
  fi

  [[ -x "$GRT_CODEBASE_MEMORY_BIN" ]] || grt_die "Codebase Memory binary missing: $GRT_CODEBASE_MEMORY_BIN"
  grt_have serena || grt_die "serena is not on PATH"
  serena_bin="$(command -v serena)"

  "$GRT_GROK" mcp add codebase-memory-mcp -- "$GRT_CODEBASE_MEMORY_BIN" || true
  "$GRT_GROK" mcp add --transport http --scope user context7 https://mcp.context7.com/mcp || true
  "$GRT_GROK" mcp add --transport http --scope user exa https://mcp.exa.ai/mcp || true
  "$GRT_GROK" mcp add serena -- "$serena_bin" start-mcp-server --context agent --project-from-cwd --open-web-dashboard false || true
  "$GRT_GROK" mcp disable serena || true
  "$GRT_GROK" mcp disable exa || true
  grt_rewrite_mcp_paths "$serena_bin"
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
