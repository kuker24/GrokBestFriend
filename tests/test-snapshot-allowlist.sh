#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
live="$tmp/live"
dest="$tmp/vendor"
mkdir -p "$live/skills" "$live/hooks" "$live/rules"

while IFS= read -r name; do
  [[ -z "$name" || "$name" == \#* ]] && continue
  cp -a "$ROOT/vendor/skills/$name" "$live/skills/$name"
done < "$ROOT/vendor/skill-allowlist.txt"
cp -a "$ROOT/vendor/hooks/impeccable.json" "$live/hooks/impeccable.json"
cp -a "$ROOT/vendor/rules/00-routing.md" "$live/rules/00-routing.md"
cp -a "$ROOT/vendor/rules/01-verification.md" "$live/rules/01-verification.md"

mkdir -p "$live/skills/personal-experiment"
echo "secret" > "$live/skills/personal-experiment/SKILL.md"

if GROK_HOME="$live" SNAPSHOT_VENDOR="$dest" "$ROOT/scripts/snapshot-live.sh" >/tmp/gbf-snap.out 2>/tmp/gbf-snap.err; then
  echo "FAIL snapshot accepted an extra live skill" >&2
  exit 1
fi
grep -q 'personal-experiment' /tmp/gbf-snap.err
echo "OK  extra live skill is refused"

rm -rf "$live/skills/personal-experiment"
GROK_HOME="$live" SNAPSHOT_VENDOR="$dest" "$ROOT/scripts/snapshot-live.sh" >/tmp/gbf-snap.out
[[ -f "$dest/skills/impeccable/SKILL.md" ]]
[[ ! -d "$dest/skills/personal-experiment" ]]
echo "OK  allowlisted snapshot writes only official skills"
printf 'test-snapshot-allowlist passed\n'
