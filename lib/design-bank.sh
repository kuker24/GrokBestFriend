#!/usr/bin/env bash

GRT_SKIP_DESIGN_BANK="${GRT_SKIP_DESIGN_BANK:-0}"

grt_design_bank_ok() {
  local root="$1"
  [[ -n "$root" && -f "$root/Refero/bank/catalog.json" && -f "$root/motionsites/library/catalog.json" ]]
}

grt_find_design_bank() {
  local candidate
  for candidate in "${GROK_DESIGN_BANK:-}" "$HOME/Design" "$HOME/Downloads/LAB GITHUB/Design"; do
    if grt_design_bank_ok "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

grt_design_bank_action() {
  local dest="$1"
  if grt_design_bank_ok "$dest"; then
    printf '%s\n' reuse
    return 0
  fi
  if [[ ! -e "$dest" ]]; then
    printf '%s\n' create
    return 0
  fi
  if [[ -d "$dest" && -z "$(find "$dest" -mindepth 1 -maxdepth 1 | head -n 1)" ]]; then
    printf '%s\n' create
    return 0
  fi
  printf '%s\n' fail
}

grt_persist_design_bank_env() {
  local root="$1"
  export GROK_DESIGN_BANK="$root"

  local rc=""
  if [[ -n "${BASH_VERSION:-}" && -f "$HOME/.bashrc" ]]; then
    rc="$HOME/.bashrc"
  elif [[ -n "${ZSH_VERSION:-}" && -f "$HOME/.zshrc" ]]; then
    rc="$HOME/.zshrc"
  elif [[ -f "$HOME/.bashrc" ]]; then
    rc="$HOME/.bashrc"
  fi
  [[ -n "$rc" ]] || return 0
  GRT_RC_PATH="$rc"

  if grep -Fq 'export GROK_DESIGN_BANK=' "$rc"; then
    return 0
  fi
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_EXPORT GROK_DESIGN_BANK=$root -> $rc"
    return 0
  fi
  {
    printf '\n# GrokBestFriend design bank\n'
    printf 'export GROK_DESIGN_BANK="%s"\n' "$root"
  } >>"$rc"
  GRT_CREATED_DESIGN_BANK_EXPORT=1
  grt_info "Appended GROK_DESIGN_BANK to $rc"
}

grt_design_bank_archive_candidates() {
  printf '%s\n' \
    "${GRT_DESIGN_BANK_ARCHIVE:-}" \
    "$GRT_ROOT/Design-bank.tgz" \
    "$GRT_VENDOR/.cache/Design-bank.tgz" \
    "/tmp/gbf-design/Design-bank.tgz"
}

grt_install_design_bank() {
  if [[ "$GRT_SKIP_DESIGN_BANK" == 1 ]]; then
    grt_info "skipping design bank"
    return 0
  fi

  local existing dest archive url expected tmp
  if existing="$(grt_find_design_bank)"; then
    grt_info "design bank already present at $existing"
    grt_persist_design_bank_env "$existing"
    return 0
  fi

  dest="${GROK_DESIGN_BANK:-$HOME/Design}"
  case "$(grt_design_bank_action "$dest")" in
    reuse)
      grt_info "design bank already present at $dest"
      grt_persist_design_bank_env "$dest"
      return 0
      ;;
    fail)
      grt_die "design bank dest exists but is not a valid catalog tree: $dest (refusing to mix files)"
      ;;
  esac

  archive=""
  while IFS= read -r candidate; do
    [[ -n "$candidate" && -f "$candidate" ]] || continue
    archive="$candidate"
    break
  done < <(grt_design_bank_archive_candidates)

  url="$(grt_source_field design-bank artifactUrl)"
  expected="$(grt_source_field design-bank artifactSha256)"

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    if [[ -n "$archive" ]]; then
      grt_info "WOULD_RESTORE_DESIGN_BANK $archive -> $dest"
    else
      grt_info "WOULD_DOWNLOAD_DESIGN_BANK $url -> $dest"
    fi
    return 0
  fi

  if [[ -z "$archive" ]]; then
    [[ -n "$url" ]] || grt_die "design-bank artifactUrl missing from vendor/sources.json"
    tmp="$GRT_VENDOR/.cache"
    mkdir -p -- "$tmp"
    archive="$tmp/Design-bank.tgz"
    grt_info "Downloading design bank (this is a few hundred MB)"
    grt_download "$url" "$archive" "$expected"
  elif [[ -n "$expected" ]]; then
    local actual
    actual="$(grt_sha256 "$archive")"
    [[ "$actual" == "$expected" ]] || grt_die "design bank checksum mismatch for $archive"
  fi

  if [[ -d "$dest" && -z "$(find "$dest" -mindepth 1 -maxdepth 1 | head -n 1)" ]]; then
    rmdir -- "$dest"
  fi
  tmp="$(mktemp -d "${dest}.tmp.XXXXXX")"
  if ! GROK_DESIGN_BANK="$tmp" "$GRT_ROOT/scripts/restore-design-bank.sh" "$archive"; then
    rm -rf -- "$tmp"
    grt_die "design bank extract failed"
  fi
  if ! grt_design_bank_ok "$tmp"; then
    rm -rf -- "$tmp"
    grt_die "design bank extract did not produce catalogs"
  fi
  mv -- "$tmp" "$dest"
  GRT_CREATED_DESIGN_BANK=1
  grt_design_bank_ok "$dest" || dest="$(grt_find_design_bank)" || grt_die "design bank restore failed"
  grt_persist_design_bank_env "$dest"
}
