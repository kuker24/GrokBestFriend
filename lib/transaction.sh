#!/usr/bin/env bash

GRT_BACKUP_STAMP="${GRT_BACKUP_STAMP:-}"
GRT_LOCK_FD="${GRT_LOCK_FD:-}"
GRT_TX_IN_HANDLER="${GRT_TX_IN_HANDLER:-0}"
GRT_TX_RECOVER="${GRT_TX_RECOVER:-0}"
GRT_CREATED_PATH_MARKER="${GRT_CREATED_PATH_MARKER:-0}"
GRT_CREATED_DESIGN_BANK_EXPORT="${GRT_CREATED_DESIGN_BANK_EXPORT:-0}"
GRT_CREATED_DESIGN_BANK="${GRT_CREATED_DESIGN_BANK:-0}"

if ! type grt_di_cleanup_staging >/dev/null 2>&1; then
  grt_di_cleanup_staging() { return 0; }
fi
if ! type grt_di_recover_promoted >/dev/null 2>&1; then
  grt_di_recover_promoted() { return 0; }
fi

grt_backup_root() {
  printf '%s\n' "$GRT_HOME/runtime/backups"
}

grt_stage_root() {
  printf '%s\n' "$GRT_HOME/runtime/stage"
}

grt_lock_file() {
  printf '%s\n' "$GRT_HOME/runtime/locks/install.lock"
}

grt_tx_path() {
  printf '%s\n' "$GRT_HOME/runtime/tx/current.json"
}

grt_swap_old_path() {
  printf '%s\n' "$GRT_HOME/runtime/swap-old"
}

grt_product_version() {
  tr -d '[:space:]' <"$GRT_ROOT/VERSION"
}

grt_preflight() {
  grt_require python3
  [[ -d "$GRT_VENDOR/skills" ]] || grt_die "Vendor skills missing: $GRT_VENDOR/skills"
  [[ -f "$GRT_VENDOR/skill-allowlist.txt" ]] || grt_die "missing $GRT_VENDOR/skill-allowlist.txt"
  [[ -f "$GRT_VENDOR/mcp-policy.json" ]] || grt_die "missing $GRT_VENDOR/mcp-policy.json"
  [[ -f "$GRT_VENDOR/sources.json" ]] || grt_die "missing $GRT_VENDOR/sources.json"
  [[ -f "$GRT_VENDOR/runtime-policy.json" ]] || grt_die "missing $GRT_VENDOR/runtime-policy.json"
  [[ -d "$GRT_VENDOR/design-intelligence" ]] || grt_die "missing $GRT_VENDOR/design-intelligence"
  [[ -d "$GRT_ROOT/lib/design_intelligence" ]] || grt_die "missing $GRT_ROOT/lib/design_intelligence"
  [[ -f "$GRT_ROOT/scripts/design-intelligence.py" ]] || grt_die "missing design-intelligence CLI"
  python3 - "$GRT_VENDOR/sources.json" "$GRT_VENDOR/mcp-policy.json" "$GRT_VENDOR/runtime-policy.json" <<'PY' || grt_die "vendor JSON failed to parse"
import json, sys
from pathlib import Path
for path in sys.argv[1:]:
    json.loads(Path(path).read_text(encoding="utf-8"))
PY
  python3 - "$GRT_VENDOR/design-intelligence" <<'PY' || grt_die "Design Intelligence policy/schema JSON failed to parse"
import json, sys
from pathlib import Path
for path in sorted(Path(sys.argv[1]).rglob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
PY
  grt_load_skill_allowlist
  local name
  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    [[ -d "$GRT_VENDOR/skills/$name" ]] || grt_die "Missing vendor skill: $name"
  done

  grt_require_node
}

grt_lock_begin() {
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_LOCK $(grt_lock_file)"
    return 0
  fi
  mkdir -p -- "$GRT_HOME/runtime/locks" "$GRT_HOME/runtime/tx"
  local lock
  lock="$(grt_lock_file)"
  exec {GRT_LOCK_FD}>"$lock"
  if ! flock -n "$GRT_LOCK_FD"; then
    eval "exec ${GRT_LOCK_FD}>&-"
    GRT_LOCK_FD=""
    grt_die "another GrokBestFriend install/restore/uninstall holds the lock: $lock"
  fi
}

grt_lock_end() {
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    return 0
  fi
  if [[ -n "${GRT_LOCK_FD:-}" ]]; then
    flock -u "$GRT_LOCK_FD" 2>/dev/null || true
    eval "exec ${GRT_LOCK_FD}>&-"
    GRT_LOCK_FD=""
  fi
}

grt_tx_state() {
  python3 - "$(grt_tx_path)" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    print("")
    raise SystemExit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    print("")
    raise SystemExit(0)
print(data.get("state") or "")
PY
}

grt_tx_stamp() {
  python3 - "$(grt_tx_path)" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    print("")
    raise SystemExit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    print("")
    raise SystemExit(0)
print(data.get("stamp") or "")
PY
}

grt_tx_set_state() {
  local state="$1"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_TX $state"
    return 0
  fi
  mkdir -p -- "$GRT_HOME/runtime/tx"
  python3 - "$(grt_tx_path)" "$state" "${GRT_BACKUP_STAMP:-}" "$(grt_swap_old_path)" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
state, stamp, swap_old = sys.argv[2], sys.argv[3], sys.argv[4]
data = {}
if path.is_file():
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    except (OSError, json.JSONDecodeError):
        data = {}
data["state"] = state
if stamp:
    data["stamp"] = stamp
data["swap_old"] = swap_old
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
}

grt_tx_write_journal() {
  local dest="$1"
  python3 - "$dest" "$GRT_HOME" "$GRT_SKILLS" "$GRT_RULES" "$GRT_HOOKS" "$GRT_MANIFEST" \
    "${GRT_BACKUP_STAMP:-}" "$(grt_tx_state)" "$(grt_swap_old_path)" \
    "$GRT_CREATED_PATH_MARKER" "$GRT_CREATED_DESIGN_BANK_EXPORT" "$GRT_CREATED_DESIGN_BANK" \
    "${GRT_RC_PATH:-}" \
    "${GRT_DI_ACTION:-skip}" "${GRT_DI_CREATED:-0}" "${GRT_DI_STAGING:-}" \
    "${GRT_DI_TARGET_DISPLAY:-~/DesignIntelligence}" "${GRT_DI_RECOVERY:-}" \
    "${GRT_DI_SNAPSHOT:-}" "${HOME}" <<'PY'
import json, sys
from pathlib import Path

dest = Path(sys.argv[1])
home = Path(sys.argv[2])
skills, rules, hooks, manifest = map(Path, sys.argv[3:7])
stamp, state, swap_old = sys.argv[7], sys.argv[8], sys.argv[9]
created_path, created_export, created_bank = sys.argv[10], sys.argv[11], sys.argv[12]
rc_path = sys.argv[13]
di_action, di_created, di_staging = sys.argv[14], sys.argv[15], sys.argv[16]
di_target, di_recovery, di_snapshot, home_user = sys.argv[17], sys.argv[18], sys.argv[19], sys.argv[20]
chromium = home / "bin" / "grok-chromium-cdp"
config = home / "config.toml"
learning = home / "runtime" / "learning" / "events.jsonl"
payload = {
    "state": state,
    "stamp": stamp,
    "swap_old": swap_old,
    "existed": {
        "skills": skills.is_dir(),
        "rules": rules.is_dir(),
        "hooks": hooks.is_dir(),
        "config": config.is_file(),
        "manifest": manifest.is_file(),
        "chromium": chromium.is_file(),
        "learning_events": learning.is_file(),
    },
    "created_this_run": {
        "path_marker": created_path == "1",
        "design_bank_export": created_export == "1",
        "design_bank": created_bank == "1",
        "design_intelligence_bank": di_created == "1",
    },
    "rc_path": rc_path,
    "design_intelligence": {
        "action": di_action,
        "created_this_run": di_created == "1",
        "staging": di_staging,
        "target": di_target,
        "recovery": di_recovery,
        "snapshot": di_snapshot or None,
    },
}
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

grt_tx_update_created() {
  local dest
  dest="$(grt_tx_path)"
  [[ -f "$dest" ]] || return 0
  python3 - "$dest" "$GRT_CREATED_PATH_MARKER" "$GRT_CREATED_DESIGN_BANK_EXPORT" "$GRT_CREATED_DESIGN_BANK" "${GRT_RC_PATH:-}" \
    "${GRT_DI_ACTION:-skip}" "${GRT_DI_CREATED:-0}" "${GRT_DI_STAGING:-}" \
    "${GRT_DI_TARGET_DISPLAY:-~/DesignIntelligence}" "${GRT_DI_RECOVERY:-}" "${GRT_DI_SNAPSHOT:-}" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
created = data.setdefault("created_this_run", {})
created["path_marker"] = sys.argv[2] == "1"
created["design_bank_export"] = sys.argv[3] == "1"
created["design_bank"] = sys.argv[4] == "1"
created["design_intelligence_bank"] = sys.argv[7] == "1"
if sys.argv[5]:
    data["rc_path"] = sys.argv[5]
data["design_intelligence"] = {
    "action": sys.argv[6],
    "created_this_run": sys.argv[7] == "1",
    "staging": sys.argv[8] or None,
    "target": sys.argv[9],
    "recovery": sys.argv[10] or None,
    "snapshot": sys.argv[11] or None,
}
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
  if [[ -n "${GRT_BACKUP_STAMP:-}" ]]; then
    local copy
    copy="$(grt_backup_root)/$GRT_BACKUP_STAMP/journal.json"
    if [[ -f "$copy" ]]; then
      cp -a -- "$dest" "$copy"
    fi
  fi
}

grt_tx_clear() {
  rm -f -- "$(grt_tx_path)"
}

grt_tx_check_stale() {
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    return 0
  fi
  local path state stamp
  path="$(grt_tx_path)"
  [[ -f "$path" ]] || return 0
  state="$(grt_tx_state)"
  stamp="$(grt_tx_stamp)"
  case "$state" in
    ""|PREPARING|BACKED_UP|COMMITTED)
      rm -f -- "$path"
      return 0
      ;;
    BANK_STAGED)
      grt_warn "incomplete transaction (BANK_STAGED); dropping unused Design Intelligence staging"
      grt_di_cleanup_staging || true
      rm -f -- "$path"
      return 0
      ;;
    MUTATING)
      grt_warn "incomplete transaction (MUTATING); restoring managed surfaces from ${stamp:-latest}"
      grt_di_cleanup_staging || true
      grt_recover_swap_old || true
      if [[ -n "$stamp" ]]; then
        grt_restore_backup "$stamp" || true
      fi
      rm -f -- "$path"
      return 0
      ;;
    SWAPPED|GROK_SWAPPED)
      if [[ "$GRT_TX_RECOVER" == 1 ]]; then
        grt_di_cleanup_staging || true
        return 0
      fi
      grt_die "incomplete transaction (state=${state} stamp=${stamp:-unknown}). Run: ./restore.sh ${stamp:-}   or ./install.sh --recover"
      ;;
    BANK_PROMOTED)
      if [[ "$GRT_TX_RECOVER" == 1 ]]; then
        grt_di_recover_promoted || true
        return 0
      fi
      grt_die "incomplete transaction (state=BANK_PROMOTED stamp=${stamp:-unknown}). Run: ./install.sh --recover"
      ;;
    *)
      grt_die "unknown transaction state: $state"
      ;;
  esac
}

grt_recover_swap_old() {
  local old
  old="$(grt_swap_old_path)"
  [[ -d "$old" ]] || return 0
  if [[ ! -d "$GRT_SKILLS" && -d "$old/skills" ]]; then
    mv -- "$old/skills" "$GRT_SKILLS"
  fi
  if [[ ! -d "$GRT_RULES" && -d "$old/rules" ]]; then
    mv -- "$old/rules" "$GRT_RULES"
  fi
  if [[ ! -d "$GRT_HOOKS" && -d "$old/hooks" ]]; then
    mv -- "$old/hooks" "$GRT_HOOKS"
  fi
  if [[ ! -f "$GRT_HOME/bin/grok-chromium-cdp" && -f "$old/grok-chromium-cdp" ]]; then
    mkdir -p -- "$GRT_HOME/bin"
    mv -- "$old/grok-chromium-cdp" "$GRT_HOME/bin/grok-chromium-cdp"
  fi
}

grt_tx_on_signal() {
  local rc=$?
  if [[ "$GRT_TX_IN_HANDLER" == 1 ]]; then
    return "$rc"
  fi
  GRT_TX_IN_HANDLER=1
  local state
  state="$(grt_tx_state || true)"
  if [[ "$state" == "BANK_STAGED" ]]; then
    grt_di_cleanup_staging || true
  fi
  if [[ "$state" == "BANK_PROMOTED" ]]; then
    grt_di_recover_promoted || true
  fi
  if [[ "$state" == "MUTATING" || "$state" == "SWAPPED" || "$state" == "GROK_SWAPPED" || "$state" == "BANK_PROMOTED" ]]; then
    grt_di_cleanup_staging || true
    grt_recover_swap_old || true
    grt_restore_backup "${GRT_BACKUP_STAMP:-}" || true
  fi
  grt_lock_end
  exit "$rc"
}

grt_new_backup_stamp() {
  python3 - <<'PY'
import os, secrets, datetime
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
print(f"{now}-{os.getpid()}-{secrets.token_hex(4)}")
PY
}

grt_can_replace_owned() {
  local kind="$1" target="$2" name="${3:-}"
  case "$kind" in
    skill)
      python3 "$GRT_ROOT/lib/ownership.py" check-skill "$target" "$name" "$GRT_MANIFEST" >/dev/null
      ;;
    rule)
      python3 "$GRT_ROOT/lib/ownership.py" check-rule "$target" "$GRT_MANIFEST" >/dev/null
      ;;
    hook)
      python3 "$GRT_ROOT/lib/ownership.py" check-hook "$target" "$GRT_MANIFEST" >/dev/null
      ;;
    *)
      return 1
      ;;
  esac
}

grt_assert_replaceable() {
  local kind="$1" target="$2" name="${3:-}"
  if [[ ! -e "$target" ]]; then
    return 0
  fi
  if grt_can_replace_owned "$kind" "$target" "$name"; then
    return 0
  fi
  grt_die "unowned collision: $target is not a GrokBestFriend-owned $kind (no marker, not in manifest). Move or rename it, then retry."
}

grt_backup_owned() {
  local stamp dest
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_BACKUP $GRT_HOME/skills $GRT_HOME/rules $GRT_HOME/hooks $GRT_HOME/config.toml"
    return 0
  fi
  stamp="$(grt_new_backup_stamp)"
  dest="$(grt_backup_root)/$stamp"
  mkdir -p -- "$dest/bin"
  [[ -d "$GRT_SKILLS" ]] && cp -a -- "$GRT_SKILLS" "$dest/skills"
  [[ -d "$GRT_RULES" ]] && cp -a -- "$GRT_RULES" "$dest/rules"
  [[ -d "$GRT_HOOKS" ]] && cp -a -- "$GRT_HOOKS" "$dest/hooks"
  [[ -f "$GRT_HOME/bin/grok-chromium-cdp" ]] && cp -a -- "$GRT_HOME/bin/grok-chromium-cdp" "$dest/bin/grok-chromium-cdp"
  [[ -f "$GRT_MANIFEST" ]] && cp -a -- "$GRT_MANIFEST" "$dest/manifest.json"
  [[ -f "$GRT_HOME/config.toml" ]] && cp -a -- "$GRT_HOME/config.toml" "$dest/config.toml"
  GRT_BACKUP_STAMP="$stamp"
  grt_tx_write_journal "$dest/journal.json"
  if [[ -f "$(grt_tx_path)" ]]; then
    python3 - "$(grt_tx_path)" "$stamp" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = {}
if path.is_file():
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    except (OSError, json.JSONDecodeError):
        data = {}
data["stamp"] = sys.argv[2]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
    # refresh journal state/stamp from current tx
    cp -a -- "$(grt_tx_path)" "$dest/tx.json" 2>/dev/null || true
    python3 - "$dest/journal.json" "$stamp" "$(grt_tx_state)" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
data["stamp"] = sys.argv[2]
data["state"] = sys.argv[3]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
  fi
  printf '%s\n' "$stamp" >"$(grt_backup_root)/LATEST"
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

grt_journal_for_stamp() {
  local stamp="$1"
  local path
  path="$(grt_backup_root)/$stamp/journal.json"
  if [[ -f "$path" ]]; then
    printf '%s\n' "$path"
    return 0
  fi
  return 1
}

grt_restore_surface() {
  local existed="$1" backup="$2" live="$3"
  if [[ "$existed" == "true" ]]; then
    if [[ -e "$backup" ]]; then
      rm -rf -- "$live"
      mkdir -p -- "$(dirname -- "$live")"
      cp -a -- "$backup" "$live"
    fi
  else
    rm -rf -- "$live"
  fi
}

grt_strip_rc_block() {
  local rc="$1" marker="$2"
  [[ -n "$rc" && -f "$rc" ]] || return 0
  python3 - "$rc" "$marker" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
marker = sys.argv[2]
text = path.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    if marker in lines[i]:
        i += 1
        if i < len(lines) and lines[i].lstrip().startswith("export "):
            i += 1
        if i < len(lines) and lines[i].strip() == "":
            i += 1
        continue
    out.append(lines[i])
    i += 1
path.write_text("".join(out), encoding="utf-8")
PY
}

grt_restore_backup() {
  local stamp src journal
  stamp="$(grt_latest_backup_stamp "${1:-}")" || grt_die "no backup to restore"
  src="$(grt_backup_root)/$stamp"
  [[ -d "$src" ]] || grt_die "backup not found: $src"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_RESTORE $src"
    return 0
  fi
  mkdir -p -- "$GRT_HOME/bin" "$GRT_RUNTIME"
  grt_recover_swap_old
  journal=""
  if journal="$(grt_journal_for_stamp "$stamp")"; then
    python3 - "$journal" "$src" "$GRT_HOME" "$GRT_SKILLS" "$GRT_RULES" "$GRT_HOOKS" "$GRT_MANIFEST" <<'PY'
import json, shutil, sys
from pathlib import Path

journal = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
src = Path(sys.argv[2])
home = Path(sys.argv[3])
skills, rules, hooks, manifest = map(Path, sys.argv[4:8])
existed = journal.get("existed") or {}

def restore_dir(flag: str, backup: Path, live: Path) -> None:
    if existed.get(flag):
        if backup.is_dir():
            if live.exists():
                shutil.rmtree(live)
            shutil.copytree(backup, live, dirs_exist_ok=False)
    else:
        if live.exists():
            shutil.rmtree(live)

def restore_file(flag: str, backup: Path, live: Path) -> None:
    if existed.get(flag):
        if backup.is_file():
            live.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, live)
    else:
        if live.is_file() or live.is_symlink():
            live.unlink()

restore_dir("skills", src / "skills", skills)
restore_dir("rules", src / "rules", rules)
restore_dir("hooks", src / "hooks", hooks)
restore_file("manifest", src / "manifest.json", manifest)
restore_file("chromium", src / "bin" / "grok-chromium-cdp", home / "bin" / "grok-chromium-cdp")
restore_file("config", src / "config.toml", home / "config.toml")
if not existed.get("learning_events"):
    events = home / "runtime" / "learning" / "events.jsonl"
    if events.is_file() and events.stat().st_size == 0:
        events.unlink()

PY
    local meta rc_path
    meta="$(python3 - "$journal" <<'PY'
import json, sys
from pathlib import Path
j = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
c = j.get("created_this_run") or {}
print(j.get("rc_path") or "")
print("1" if c.get("path_marker") else "0")
print("1" if c.get("design_bank_export") else "0")
print("1" if c.get("design_bank") else "0")
PY
)"
    rc_path="$(printf '%s\n' "$meta" | sed -n '1p')"
    local path_marker export_flag bank_flag
    path_marker="$(printf '%s\n' "$meta" | sed -n '2p')"
    export_flag="$(printf '%s\n' "$meta" | sed -n '3p')"
    bank_flag="$(printf '%s\n' "$meta" | sed -n '4p')"
    if [[ "$path_marker" == 1 ]]; then
      grt_strip_rc_block "$rc_path" "# GrokBestFriend PATH"
    fi
    if [[ "$export_flag" == 1 ]]; then
      grt_strip_rc_block "$rc_path" "# GrokBestFriend design bank"
    fi
    if [[ "$bank_flag" == 1 ]]; then
      local dest="${GROK_DESIGN_BANK:-$HOME/Design}"
      if [[ -d "$dest" && ! -f "$dest/Refero/bank/catalog.json" ]]; then
        rm -rf -- "$dest"
      elif [[ -d "$dest" ]]; then
        # we created it this run via atomic rename; remove the tree we added
        rm -rf -- "$dest"
      fi
    fi
  else
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
    if [[ -f "$src/config.toml" ]]; then
      cp -a -- "$src/config.toml" "$GRT_HOME/config.toml"
    fi
  fi
  rm -rf -- "$(grt_swap_old_path)"
  grt_tx_clear
  grt_info "RESTORED $stamp"
}

grt_stage_owned() {
  local stage name src dest prepend version
  grt_load_skill_allowlist
  stage="$(grt_stage_root)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_STAGE $stage"
    return 0
  fi

  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    grt_assert_replaceable skill "$GRT_SKILLS/$name" "$name"
  done
  for name in implement code-review; do
    if [[ -e "$GRT_SKILLS/$name" ]]; then
      grt_assert_replaceable skill "$GRT_SKILLS/$name" "$name"
    fi
  done
  grt_assert_replaceable rule "$GRT_RULES/00-routing.md"
  grt_assert_replaceable rule "$GRT_RULES/01-verification.md"
  grt_assert_replaceable hook "$GRT_HOOKS/impeccable.json"

  rm -rf -- "$stage"
  mkdir -p -- "$stage/skills" "$stage/rules" "$stage/hooks" "$stage/bin"
  if [[ -d "$GRT_SKILLS" ]]; then
    cp -a -- "$GRT_SKILLS/." "$stage/skills/"
  fi
  if [[ -d "$GRT_RULES" ]]; then
    cp -a -- "$GRT_RULES/." "$stage/rules/"
  fi
  if [[ -d "$GRT_HOOKS" ]]; then
    cp -a -- "$GRT_HOOKS/." "$stage/hooks/"
  fi

  version="$(grt_product_version)"
  for name in "${GRT_SKILLS_VENDOR[@]}"; do
    src="$GRT_VENDOR/skills/$name"
    dest="$stage/skills/$name"
    [[ -d "$src" ]] || grt_die "Missing vendor skill: $src"
    rm -rf -- "$dest"
    cp -a -- "$src" "$dest"
    prepend=""
    case "$name" in
      ask-matt) prepend="$GRT_ROOT/templates/skill-overlays/ask-matt.prepend.md" ;;
      grill-with-docs) prepend="$GRT_ROOT/templates/skill-overlays/grill-with-docs.body.md" ;;
      browser-act) prepend="$GRT_ROOT/templates/skill-overlays/browser-act.prepend.md" ;;
      chrome-devtools-axi) prepend="$GRT_ROOT/templates/skill-overlays/chrome-devtools-axi.prepend.md" ;;
    esac
    python3 "$GRT_ROOT/lib/overlay.py" --dest "$dest" --name "$name" --prepend "$prepend"
    python3 - "$GRT_ROOT/lib/ownership.py" "$dest" "$name" "$version" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
from ownership import write_skill_marker
write_skill_marker(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
PY
  done

  # Design Intelligence is an internal Impeccable reference engine, not a
  # separately routable skill. Package its stdlib-only runtime atomically with
  # the owning skill so install/restore cannot split their versions.
  dest="$stage/skills/impeccable"
  mkdir -p -- "$dest/scripts"
  cp -a -- "$GRT_ROOT/lib/design_intelligence" "$dest/scripts/design_intelligence"
  find "$dest/scripts/design_intelligence" -type d -name __pycache__ -prune -exec rm -rf -- {} +
  find "$dest/scripts/design_intelligence" -type f -name '*.pyc' -delete
  cp -a -- "$GRT_ROOT/scripts/design-intelligence.py" "$dest/scripts/design-intelligence.py"
  chmod 755 -- "$dest/scripts/design-intelligence.py"
  cp -a -- "$GRT_VENDOR/design-intelligence" "$dest/design-intelligence"
  cp -a -- "$GRT_VENDOR/skill-allowlist.txt" "$dest/design-intelligence/skill-allowlist.txt"

  # Only remove implement/code-review from the staged tree when they are GBF-owned.
  for name in implement code-review; do
    if [[ -e "$stage/skills/$name" ]]; then
      if grt_can_replace_owned skill "$GRT_SKILLS/$name" "$name"; then
        rm -rf -- "$stage/skills/$name"
      fi
    fi
  done

  if [[ -f "$GRT_VENDOR/rules/00-routing.md" ]]; then
    cp -a -- "$GRT_VENDOR/rules/00-routing.md" "$stage/rules/00-routing.md"
    cp -a -- "$GRT_VENDOR/rules/01-verification.md" "$stage/rules/01-verification.md"
  else
    cp -a -- "$GRT_ROOT/templates/rules/00-routing.md" "$stage/rules/00-routing.md"
    cp -a -- "$GRT_ROOT/templates/rules/01-verification.md" "$stage/rules/01-verification.md"
  fi
  cp -a -- "$GRT_VENDOR/hooks/impeccable.json" "$stage/hooks/impeccable.json"
  python3 - "$GRT_ROOT/lib/ownership.py" "$stage/rules" "$stage/hooks" "$version" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
from ownership import write_dir_marker
write_dir_marker(Path(sys.argv[2]), ["00-routing.md", "01-verification.md"], sys.argv[4])
write_dir_marker(Path(sys.argv[3]), ["impeccable.json"], sys.argv[4])
PY
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
  [[ -f "$stage/skills/impeccable/scripts/design-intelligence.py" ]] \
    || grt_die "staged Impeccable is missing Design Intelligence CLI"
  [[ -f "$stage/skills/impeccable/scripts/design_intelligence/selection.py" ]] \
    || grt_die "staged Impeccable is missing Design Intelligence runtime"
  [[ -f "$stage/skills/impeccable/scripts/design_intelligence/bootstrap.py" ]] \
    || grt_die "staged Impeccable is missing Design Intelligence bootstrap"
  [[ -f "$stage/skills/impeccable/design-intelligence/policy.json" ]] \
    || grt_die "staged Impeccable is missing Design Intelligence policy"
  python3 - "$stage/skills/impeccable/design-intelligence" <<'PY' \
    || grt_die "staged Design Intelligence policy/schema JSON failed to parse"
import json, sys
from pathlib import Path
for path in sorted(Path(sys.argv[1]).rglob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
PY
  PYTHONDONTWRITEBYTECODE=1 python3 "$stage/skills/impeccable/scripts/design-intelligence.py" --help >/dev/null \
    || grt_die "staged Design Intelligence CLI failed to load"
}

grt_atomic_swap() {
  local stage old
  stage="$(grt_stage_root)"
  old="$(grt_swap_old_path)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_SWAP $stage -> $GRT_HOME"
    return 0
  fi
  [[ -d "$stage/skills" ]] || grt_die "stage missing skills"
  rm -rf -- "$old"
  mkdir -p -- "$old" "$GRT_HOME/bin"
  grt_tx_set_state MUTATING

  [[ -d "$GRT_SKILLS" ]] && mv -- "$GRT_SKILLS" "$old/skills"
  [[ -d "$GRT_RULES" ]] && mv -- "$GRT_RULES" "$old/rules"
  [[ -d "$GRT_HOOKS" ]] && mv -- "$GRT_HOOKS" "$old/hooks"
  [[ -f "$GRT_HOME/bin/grok-chromium-cdp" ]] && mv -- "$GRT_HOME/bin/grok-chromium-cdp" "$old/grok-chromium-cdp"

  mv -- "$stage/skills" "$GRT_SKILLS"
  mv -- "$stage/rules" "$GRT_RULES"
  mv -- "$stage/hooks" "$GRT_HOOKS"
  mv -- "$stage/bin/grok-chromium-cdp" "$GRT_HOME/bin/grok-chromium-cdp"
  chmod 755 -- "$GRT_HOME/bin/grok-chromium-cdp"
  rm -rf -- "$stage" "$old"
  grt_tx_set_state SWAPPED
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
    if [[ -d "$GRT_SKILLS/$name" ]] && grt_can_replace_owned skill "$GRT_SKILLS/$name" "$name"; then
      rm -rf -- "${GRT_SKILLS:?}/$name"
    fi
  done
  for name in implement code-review; do
    if [[ -d "$GRT_SKILLS/$name" ]] && grt_can_replace_owned skill "$GRT_SKILLS/$name" "$name"; then
      rm -rf -- "${GRT_SKILLS:?}/$name"
    fi
  done
  if [[ -f "$GRT_RULES/00-routing.md" ]] && grt_can_replace_owned rule "$GRT_RULES/00-routing.md"; then
    rm -f -- "$GRT_RULES/00-routing.md"
  fi
  if [[ -f "$GRT_RULES/01-verification.md" ]] && grt_can_replace_owned rule "$GRT_RULES/01-verification.md"; then
    rm -f -- "$GRT_RULES/01-verification.md"
  fi
  if [[ -f "$GRT_HOOKS/impeccable.json" ]] && grt_can_replace_owned hook "$GRT_HOOKS/impeccable.json"; then
    rm -f -- "$GRT_HOOKS/impeccable.json"
  fi
  rm -f -- "$GRT_RULES/.grokbestfriend-owned.json" "$GRT_HOOKS/.grokbestfriend-owned.json"
  rm -f -- "$GRT_HOME/bin/grok-chromium-cdp"
  rm -f -- "$GRT_MANIFEST"
  grt_info "uninstalled owned GrokBestFriend files (Grok CLI, credentials, foreign skills, and learning log left in place)"
}
