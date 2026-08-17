#!/usr/bin/env bash

grt_write_manifest() {
  local tmp
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_WRITE $GRT_MANIFEST"
    return 0
  fi
  mkdir -p -- "$GRT_RUNTIME"
  tmp="$(mktemp "$GRT_RUNTIME/.manifest.XXXXXX")"
  python3 - "$tmp" "$GRT_HOME" "$GRT_ROOT" "$GRT_CODEBASE_MEMORY_BIN" "$GRT_ROOT/VERSION" \
    "${GRT_DI_MANIFEST_FILE:-}" "${GRT_DI_ACTION:-skip}" <<'PY'
import json, sys, datetime
from pathlib import Path
target, grok_home, root, memory_bin, version_file, di_file, di_action = sys.argv[1:8]
allowlist = Path(root, "vendor/skill-allowlist.txt").read_text(encoding="utf-8")
skills = [line.strip() for line in allowlist.splitlines() if line.strip() and not line.startswith("#")]
version = Path(version_file).read_text(encoding="utf-8").strip()
design = {
    "engine": "installed",
    "bank": "skipped" if di_action in {"", "skip"} else "installed",
    "path": "~/DesignIntelligence",
    "snapshot": None,
    "generationId": None,
    "contentStatus": "missing" if di_action in {"", "skip"} else "degraded-with-expected-limitations",
}
if di_file:
    path = Path(di_file)
    if path.is_file():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        fragment = loaded.get("manifest") if isinstance(loaded.get("manifest"), dict) else loaded
        if isinstance(fragment, dict):
            for key in (
                "engine",
                "bank",
                "path",
                "snapshot",
                "generationId",
                "items",
                "systems",
                "structures",
                "recipes",
                "specialists",
                "contentStatus",
                "archives",
            ):
                if key in fragment:
                    design[key] = fragment[key]
if isinstance(design.get("path"), str) and design["path"].startswith("/"):
    design["path"] = "~/DesignIntelligence"
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
    "designIntelligence": design,
}
Path(target).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  chmod 600 "$tmp"
  mv -f -- "$tmp" "$GRT_MANIFEST"
}

grt_run_install() {
  grt_preflight
  grt_lock_begin
  grt_tx_check_stale
  grt_di_preflight
  grt_tx_set_state PREPARING
  grt_backup_owned
  grt_tx_set_state BACKED_UP
  grt_tx_set_state MUTATING
  grt_install_grok_cli
  grt_ensure_path
  grt_tx_update_created
  grt_find_grok
  grt_require_grok_version
  grt_install_tools
  grt_install_mcp
  grt_stage_owned
  grt_validate_stage
  grt_di_stage
  if [[ "${GRT_DI_ACTION:-skip}" == "create" && "${GRT_DRY_RUN}" != 1 ]]; then
    grt_tx_set_state BANK_STAGED
  fi
  grt_atomic_swap
  if [[ "${GRT_DI_ACTION:-skip}" == "create" && "${GRT_DRY_RUN}" != 1 ]]; then
    grt_tx_set_state GROK_SWAPPED
  fi
  grt_merge_user_config
  grt_install_design_bank
  grt_install_design_intelligence_bank
  if [[ "${GRT_DI_CREATED:-0}" == 1 && "${GRT_DRY_RUN}" != 1 ]]; then
    grt_tx_set_state BANK_PROMOTED
  fi
  grt_tx_update_created
  grt_ensure_learning_log
  grt_write_manifest
}
