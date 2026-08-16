#!/usr/bin/env bash

grt_write_manifest() {
  local tmp
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_WRITE $GRT_MANIFEST"
    return 0
  fi
  mkdir -p -- "$GRT_RUNTIME"
  tmp="$(mktemp "$GRT_RUNTIME/.manifest.XXXXXX")"
  python3 - "$tmp" "$GRT_HOME" "$GRT_ROOT" "$GRT_CODEBASE_MEMORY_BIN" "$GRT_ROOT/VERSION" <<'PY'
import json, sys, datetime
from pathlib import Path
target, grok_home, root, memory_bin, version_file = sys.argv[1:6]
allowlist = Path(root, "vendor/skill-allowlist.txt").read_text(encoding="utf-8")
skills = [line.strip() for line in allowlist.splitlines() if line.strip() and not line.startswith("#")]
version = Path(version_file).read_text(encoding="utf-8").strip()
payload = {
    "version": 3,
    "product": "GrokBestFriend",
    "productVersion": version,
    "installed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": root,
    "codebase_memory_bin": memory_bin,
    "rules": [
        f"{grok_home}/rules/00-routing.md",
        f"{grok_home}/rules/01-verification.md",
    ],
    "hooks": [f"{grok_home}/hooks/impeccable.json"],
    "skills": [f"{grok_home}/skills/{name}" for name in skills],
    "mcp": {
        "codebase-memory-mcp": {"enabled": True, "transport": "stdio"},
        "context7": {"enabled": True, "transport": "http"},
        "exa": {"enabled": False, "transport": "http", "status": "SETUP_REQUIRED"},
        "serena": {"enabled": False, "transport": "stdio", "context": "agent"},
    },
    "plugins": [],
    "compat_claude": False,
}
Path(target).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  chmod 600 "$tmp"
  mv -f -- "$tmp" "$GRT_MANIFEST"
}

grt_run_install() {
  grt_preflight
  grt_install_grok_cli
  grt_ensure_path
  grt_find_grok
  grt_require_grok_version
  grt_install_tools
  grt_install_mcp
  grt_backup_owned
  grt_stage_owned
  grt_validate_stage
  grt_atomic_swap
  grt_merge_user_config
  grt_install_design_bank
  grt_ensure_learning_log
  grt_write_manifest
}
