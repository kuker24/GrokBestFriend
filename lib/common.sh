#!/usr/bin/env bash

GRT_LIB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
GRT_ROOT="$(cd -- "$GRT_LIB_DIR/.." && pwd)"
GRT_HOME="${GRT_HOME:-$HOME/.grok}"
GRT_RUNTIME="$GRT_HOME/runtime"
GRT_MANIFEST="$GRT_RUNTIME/manifest.json"
GRT_SKILLS="$GRT_HOME/skills"
GRT_RULES="$GRT_HOME/rules"
GRT_HOOKS="$GRT_HOME/hooks"
GRT_VENDOR="$GRT_ROOT/vendor"
GRT_CODEBASE_MEMORY_BIN="${GRT_CODEBASE_MEMORY_BIN:-$GRT_HOME/runtime/components/codebase-memory/bin/codebase-memory-mcp}"
GRT_DRY_RUN="${GRT_DRY_RUN:-0}"
GRT_SKIP_TOOLS="${GRT_SKIP_TOOLS:-0}"
GRT_SKIP_DESIGN_BANK="${GRT_SKIP_DESIGN_BANK:-0}"
GRT_GROK="${GRT_GROK:-}"
GRT_PATH_MARKER="# GrokBestFriend PATH"

grt_info() { printf '%s\n' "$*"; }
grt_warn() { printf 'WARNING: %s\n' "$*" >&2; }
grt_error() { printf 'ERROR: %s\n' "$*" >&2; }
grt_die() { grt_error "$*"; exit 1; }
grt_have() { command -v "$1" >/dev/null 2>&1; }

grt_find_grok() {
  if [[ -n "$GRT_GROK" && -x "$GRT_GROK" ]]; then
    return 0
  fi
  if grt_have grok; then
    GRT_GROK="$(command -v grok)"
    return 0
  fi
  if [[ -x "$HOME/.grok/bin/grok" ]]; then
    GRT_GROK="$HOME/.grok/bin/grok"
    return 0
  fi
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    GRT_GROK="${GRT_GROK:-grok}"
    grt_info "WOULD_NEED grok binary"
    return 0
  fi
  grt_die "grok binary not found"
}

grt_require() {
  local command
  for command in "$@"; do
    grt_have "$command" || grt_die "Required command not found: $command"
  done
}

grt_sha256() {
  sha256sum -- "$1" | awk '{print $1}'
}

grt_source_field() {
  local id="$1" field="$2"
  python3 - "$GRT_VENDOR/sources.json" "$id" "$field" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
node = data.get("sources", {}).get(sys.argv[2], {})
value = node.get(sys.argv[3], "")
print(value)
PY
}

grt_grok_seen_version() {
  python3 - "$GRT_VENDOR/sources.json" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(data.get("grok", {}).get("seenVersion", ""))
PY
}

grt_read_allowlist() {
  local file="$GRT_VENDOR/skill-allowlist.txt"
  [[ -f "$file" ]] || grt_die "missing skill allowlist: $file"
  grep -E -v '^[[:space:]]*(#|$)' "$file"
}

grt_load_skill_allowlist() {
  mapfile -t GRT_SKILLS_VENDOR < <(grt_read_allowlist)
  [[ ${#GRT_SKILLS_VENDOR[@]} -gt 0 ]] || grt_die "skill allowlist is empty"
}

grt_version_contains() {
  local output="$1" wanted="$2"
  [[ -n "$wanted" && "$output" == *"$wanted"* ]]
}

grt_atomic_write() {
  local target="$1" source="$2" dir tmp mode
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_WRITE $target"
    return 0
  fi
  dir="$(dirname -- "$target")"
  mkdir -p -- "$dir"
  tmp="$(mktemp "$dir/.grt.XXXXXX")"
  cp -- "$source" "$tmp"
  mode=600
  [[ -e "$target" ]] && mode="$(stat -c '%a' "$target")"
  chmod "$mode" "$tmp"
  mv -f -- "$tmp" "$target"
}

grt_copy_tree() {
  local src="$1" dest="$2"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_COPY $src -> $dest"
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dest")"
  rm -rf -- "$dest"
  cp -a -- "$src" "$dest"
}

grt_ensure_dir() {
  local dir="$1"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_MKDIR $dir"
    return 0
  fi
  mkdir -p -- "$dir"
}

grt_download() {
  local url="$1" dest="$2" expected="${3:-}"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_DOWNLOAD $url -> $dest"
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dest")"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$url" --output "$dest"
  if [[ -n "$expected" ]]; then
    local actual
    actual="$(grt_sha256 "$dest")"
    [[ "$actual" == "$expected" ]] || grt_die "checksum mismatch for $dest"
  fi
}
