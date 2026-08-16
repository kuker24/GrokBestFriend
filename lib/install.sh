#!/usr/bin/env bash

GRT_SKILLS_VENDOR=(
  adhd
  ask-matt
  browser-act
  chrome-devtools-axi
  emil-design-eng
  found-this-design
  full-audit-keamanan
  full-performance-audit
  gh-axi
  grill-with-docs
  impeccable
  matt-code-review
  matt-implement
  scroll-world
  tdd
  to-spec
  to-tickets
  visual-studio
)

grt_install_rules() {
  local dest
  mkdir -p -- "$GRT_RULES"
  for dest in 00-routing.md 01-verification.md; do
    if [[ -f "$GRT_VENDOR/rules/$dest" ]]; then
      grt_atomic_write "$GRT_RULES/$dest" "$GRT_VENDOR/rules/$dest"
    else
      grt_atomic_write "$GRT_RULES/$dest" "$GRT_ROOT/templates/rules/$dest"
    fi
  done
}

grt_install_hooks() {
  local src="$GRT_VENDOR/hooks/impeccable.json"
  [[ -f "$src" ]] || grt_die "missing hook $src"
  grt_atomic_write "$GRT_HOOKS/impeccable.json" "$src"
}

grt_install_skills() {
  local name src dest prepend
  [[ -d "$GRT_VENDOR/skills" ]] || grt_die "Vendor skills missing: $GRT_VENDOR/skills"
  mkdir -p -- "$GRT_SKILLS"

  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    src="$GRT_VENDOR/skills/$name"
    dest="$GRT_SKILLS/$name"
    [[ -d "$src" ]] || grt_die "Missing vendor skill: $src"
    grt_info "SKILL $name"
    grt_copy_tree "$src" "$dest"
    if [[ "$GRT_DRY_RUN" == 1 ]]; then
      continue
    fi
    prepend=""
    case "$name" in
      ask-matt) prepend="$GRT_ROOT/templates/skill-overlays/ask-matt.prepend.md" ;;
      grill-with-docs) prepend="$GRT_ROOT/templates/skill-overlays/grill-with-docs.body.md" ;;
      browser-act) prepend="$GRT_ROOT/templates/skill-overlays/browser-act.prepend.md" ;;
      chrome-devtools-axi) prepend="$GRT_ROOT/templates/skill-overlays/chrome-devtools-axi.prepend.md" ;;
    esac
    python3 "$GRT_ROOT/lib/overlay.py" --dest "$dest" --name "$name" --prepend "$prepend"
  done

  if [[ "$GRT_DRY_RUN" != 1 ]]; then
    rm -rf -- "$GRT_SKILLS/implement" "$GRT_SKILLS/code-review"
  fi
}

grt_write_manifest() {
  local tmp
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_WRITE $GRT_MANIFEST"
    return 0
  fi
  mkdir -p -- "$GRT_RUNTIME"
  tmp="$(mktemp "$GRT_RUNTIME/.manifest.XXXXXX")"
  python3 - "$tmp" "$GRT_HOME" "$GRT_ROOT" "$GRT_CODEBASE_MEMORY_BIN" <<'PY'
import json, sys, datetime
from pathlib import Path
target, grok_home, root, memory_bin = sys.argv[1:5]
skills = [
    "adhd", "ask-matt", "browser-act", "chrome-devtools-axi",
    "emil-design-eng", "found-this-design", "full-audit-keamanan",
    "full-performance-audit", "gh-axi", "grill-with-docs", "impeccable",
    "matt-code-review", "matt-implement", "scroll-world", "tdd",
    "to-spec", "to-tickets", "visual-studio",
]
payload = {
    "version": 2,
    "product": "GrokBestFriend",
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

grt_install_chromium_helper() {
  local dest="$GRT_HOME/bin/grok-chromium-cdp"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_WRITE $dest"
    return 0
  fi
  mkdir -p -- "$GRT_HOME/bin"
  grt_atomic_write "$dest" "$GRT_ROOT/lib/grok-chromium-cdp.sh"
  chmod 755 -- "$dest"
}

grt_run_install() {
  grt_require python3 curl tar
  grt_install_grok_cli
  grt_ensure_path
  grt_find_grok
  grt_install_rules
  grt_install_hooks
  grt_install_skills
  grt_install_chromium_helper
  grt_merge_user_config
  grt_install_tools
  grt_install_mcp
  grt_install_design_bank
  grt_write_manifest
}
