#!/usr/bin/env bash

GRT_BACKUP_STAMP="${GRT_BACKUP_STAMP:-}"

grt_backup_root() {
  printf '%s\n' "$GRT_HOME/runtime/backups"
}

grt_stage_root() {
  printf '%s\n' "$GRT_HOME/runtime/stage"
}

grt_preflight() {
  grt_require python3
  [[ -d "$GRT_VENDOR/skills" ]] || grt_die "Vendor skills missing: $GRT_VENDOR/skills"
  [[ -f "$GRT_VENDOR/skill-allowlist.txt" ]] || grt_die "missing $GRT_VENDOR/skill-allowlist.txt"
  [[ -f "$GRT_VENDOR/mcp-policy.json" ]] || grt_die "missing $GRT_VENDOR/mcp-policy.json"
  [[ -f "$GRT_VENDOR/sources.json" ]] || grt_die "missing $GRT_VENDOR/sources.json"
  python3 - "$GRT_VENDOR/sources.json" "$GRT_VENDOR/mcp-policy.json" <<'PY' || grt_die "vendor JSON failed to parse"
import json, sys
from pathlib import Path
for path in sys.argv[1:]:
    json.loads(Path(path).read_text(encoding="utf-8"))
PY
  grt_load_skill_allowlist
  local name
  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    [[ -d "$GRT_VENDOR/skills/$name" ]] || grt_die "Missing vendor skill: $name"
  done
}

grt_backup_owned() {
  local stamp dest
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_BACKUP $GRT_HOME/skills $GRT_HOME/rules $GRT_HOME/hooks"
    return 0
  fi
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dest="$(grt_backup_root)/$stamp"
  mkdir -p -- "$dest/bin"
  [[ -d "$GRT_SKILLS" ]] && cp -a -- "$GRT_SKILLS" "$dest/skills"
  [[ -d "$GRT_RULES" ]] && cp -a -- "$GRT_RULES" "$dest/rules"
  [[ -d "$GRT_HOOKS" ]] && cp -a -- "$GRT_HOOKS" "$dest/hooks"
  [[ -f "$GRT_HOME/bin/grok-chromium-cdp" ]] && cp -a -- "$GRT_HOME/bin/grok-chromium-cdp" "$dest/bin/grok-chromium-cdp"
  [[ -f "$GRT_MANIFEST" ]] && cp -a -- "$GRT_MANIFEST" "$dest/manifest.json"
  printf '%s\n' "$stamp" >"$(grt_backup_root)/LATEST"
  GRT_BACKUP_STAMP="$stamp"
  grt_info "BACKUP $dest"
}

grt_latest_backup_stamp() {
  local latest
  latest="$(grt_backup_root)/LATEST"
  if [[ -n "${1:-}" ]]; then
    printf '%s\n' "$1"
    return 0
  fi
  [[ -f "$latest" ]] || return 1
  cat -- "$latest"
}

grt_restore_backup() {
  local stamp src
  stamp="$(grt_latest_backup_stamp "${1:-}")" || grt_die "no backup to restore"
  src="$(grt_backup_root)/$stamp"
  [[ -d "$src" ]] || grt_die "backup not found: $src"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_RESTORE $src"
    return 0
  fi
  mkdir -p -- "$GRT_HOME/bin" "$GRT_RUNTIME"
  if [[ -d "$src/skills" ]]; then
    rm -rf -- "$GRT_SKILLS"
    cp -a -- "$src/skills" "$GRT_SKILLS"
  fi
  if [[ -d "$src/rules" ]]; then
    rm -rf -- "$GRT_RULES"
    cp -a -- "$src/rules" "$GRT_RULES"
  fi
  if [[ -d "$src/hooks" ]]; then
    rm -rf -- "$GRT_HOOKS"
    cp -a -- "$src/hooks" "$GRT_HOOKS"
  fi
  if [[ -f "$src/bin/grok-chromium-cdp" ]]; then
    cp -a -- "$src/bin/grok-chromium-cdp" "$GRT_HOME/bin/grok-chromium-cdp"
    chmod 755 -- "$GRT_HOME/bin/grok-chromium-cdp"
  fi
  if [[ -f "$src/manifest.json" ]]; then
    cp -a -- "$src/manifest.json" "$GRT_MANIFEST"
  fi
  grt_info "RESTORED $stamp"
}

grt_stage_owned() {
  local stage name src dest prepend
  grt_load_skill_allowlist
  stage="$(grt_stage_root)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_STAGE $stage"
    return 0
  fi
  rm -rf -- "$stage"
  mkdir -p -- "$stage/skills" "$stage/rules" "$stage/hooks" "$stage/bin"

  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    src="$GRT_VENDOR/skills/$name"
    dest="$stage/skills/$name"
    [[ -d "$src" ]] || grt_die "Missing vendor skill: $src"
    cp -a -- "$src" "$dest"
    prepend=""
    case "$name" in
      ask-matt) prepend="$GRT_ROOT/templates/skill-overlays/ask-matt.prepend.md" ;;
      grill-with-docs) prepend="$GRT_ROOT/templates/skill-overlays/grill-with-docs.body.md" ;;
      browser-act) prepend="$GRT_ROOT/templates/skill-overlays/browser-act.prepend.md" ;;
      chrome-devtools-axi) prepend="$GRT_ROOT/templates/skill-overlays/chrome-devtools-axi.prepend.md" ;;
    esac
    python3 "$GRT_ROOT/lib/overlay.py" --dest "$dest" --name "$name" --prepend "$prepend"
  done

  if [[ -f "$GRT_VENDOR/rules/00-routing.md" ]]; then
    cp -a -- "$GRT_VENDOR/rules/00-routing.md" "$stage/rules/00-routing.md"
    cp -a -- "$GRT_VENDOR/rules/01-verification.md" "$stage/rules/01-verification.md"
  else
    cp -a -- "$GRT_ROOT/templates/rules/00-routing.md" "$stage/rules/00-routing.md"
    cp -a -- "$GRT_ROOT/templates/rules/01-verification.md" "$stage/rules/01-verification.md"
  fi
  cp -a -- "$GRT_VENDOR/hooks/impeccable.json" "$stage/hooks/impeccable.json"
  cp -a -- "$GRT_ROOT/lib/grok-chromium-cdp.sh" "$stage/bin/grok-chromium-cdp"
  chmod 755 -- "$stage/bin/grok-chromium-cdp"
}

grt_validate_stage() {
  local stage
  stage="$(grt_stage_root)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_VALIDATE_STAGE $stage"
    return 0
  fi
  python3 "$GRT_ROOT/lib/validate_skills.py" --skills "$stage/skills" --routing "$stage/rules/00-routing.md" \
    || grt_die "staged skills failed validation"
}

grt_atomic_swap() {
  local stage old
  stage="$(grt_stage_root)"
  old="$GRT_HOME/runtime/swap-old"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_SWAP $stage -> $GRT_HOME"
    return 0
  fi
  [[ -d "$stage/skills" ]] || grt_die "stage missing skills"
  rm -rf -- "$old"
  mkdir -p -- "$old" "$GRT_HOME/bin"

  [[ -d "$GRT_SKILLS" ]] && mv -- "$GRT_SKILLS" "$old/skills"
  [[ -d "$GRT_RULES" ]] && mv -- "$GRT_RULES" "$old/rules"
  [[ -d "$GRT_HOOKS" ]] && mv -- "$GRT_HOOKS" "$old/hooks"
  [[ -f "$GRT_HOME/bin/grok-chromium-cdp" ]] && mv -- "$GRT_HOME/bin/grok-chromium-cdp" "$old/grok-chromium-cdp"

  mv -- "$stage/skills" "$GRT_SKILLS"
  mv -- "$stage/rules" "$GRT_RULES"
  mv -- "$stage/hooks" "$GRT_HOOKS"
  mv -- "$stage/bin/grok-chromium-cdp" "$GRT_HOME/bin/grok-chromium-cdp"
  chmod 755 -- "$GRT_HOME/bin/grok-chromium-cdp"
  rm -rf -- "$GRT_SKILLS/implement" "$GRT_SKILLS/code-review" "$stage"
  grt_info "SWAP complete"
}

grt_ensure_learning_log() {
  local dir="$GRT_HOME/runtime/learning"
  local file="$dir/events.jsonl"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_TOUCH $file"
    return 0
  fi
  mkdir -p -- "$dir"
  if [[ ! -f "$file" ]]; then
    umask 077
    : >"$file"
    chmod 600 -- "$file"
  fi
}

grt_uninstall_owned() {
  local name
  grt_load_skill_allowlist
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_UNINSTALL owned GrokBestFriend surfaces"
    return 0
  fi
  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    rm -rf -- "$GRT_SKILLS/$name"
  done
  rm -rf -- "$GRT_SKILLS/implement" "$GRT_SKILLS/code-review"
  rm -f -- "$GRT_RULES/00-routing.md" "$GRT_RULES/01-verification.md"
  rm -f -- "$GRT_HOOKS/impeccable.json"
  rm -f -- "$GRT_HOME/bin/grok-chromium-cdp"
  rm -f -- "$GRT_MANIFEST"
  grt_info "uninstalled owned GrokBestFriend files (Grok CLI and credentials left in place)"
}
