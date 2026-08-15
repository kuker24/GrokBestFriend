#!/usr/bin/env bash
# Restore a packed design bank to $GROK_DESIGN_BANK or ~/Design.
set -euo pipefail
ARCHIVE="${1:-}"
DEST="${GROK_DESIGN_BANK:-$HOME/Design}"

[[ -n "$ARCHIVE" && -f "$ARCHIVE" ]] || {
  echo "Usage: $0 /path/to/Design-bank.tgz" >&2
  exit 1
}

mkdir -p -- "$DEST"
tmp="$(mktemp -d)"
tar -xzf "$ARCHIVE" -C "$tmp"
# Accept either a folder named Design or the catalogs at the archive root.
if [[ -d "$tmp/Design/Refero" ]]; then
  rsync -a "$tmp/Design/" "$DEST/"
elif [[ -d "$tmp/Refero" ]]; then
  rsync -a "$tmp/" "$DEST/"
else
  inner="$(find "$tmp" -maxdepth 2 -type d -name Refero | head -n 1)"
  [[ -n "$inner" ]] || { echo "archive does not contain Refero/" >&2; exit 1; }
  rsync -a "$(dirname -- "$inner")/" "$DEST/"
fi
rm -rf -- "$tmp"

[[ -d "$DEST/Refero" && -d "$DEST/motionsites" ]] || {
  echo "restore finished but catalogs are missing under $DEST" >&2
  exit 1
}

echo "restored design bank to $DEST"
echo "export GROK_DESIGN_BANK=\"$DEST\""
