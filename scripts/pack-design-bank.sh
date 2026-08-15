#!/usr/bin/env bash
# Pack the local design bank so you can copy it to a new laptop on USB/disk.
# Does not commit the archive.
set -euo pipefail
SRC="${1:-${GROK_DESIGN_BANK:-$HOME/Design}}"
DEST="${2:-./Design-bank.tgz}"

[[ -d "$SRC/Refero" && -d "$SRC/motionsites" ]] || {
  echo "Design bank not found at $SRC (need Refero/ and motionsites/)" >&2
  echo "On this machine the live bank is: \$HOME/Downloads/LAB GITHUB/Design" >&2
  exit 1
}

mkdir -p -- "$(dirname -- "$DEST")"
tar -czf "$DEST" -C "$(dirname -- "$SRC")" "$(basename -- "$SRC")"
sha256sum -- "$DEST" | tee "$DEST.sha256"
echo "packed $SRC -> $DEST"
echo "Upload $DEST to the GitHub Release, then put the SHA-256 in vendor/sources.json"
