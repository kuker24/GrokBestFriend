#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export GRT_HOME="$tmp/home"
export HOME="$tmp/home-user"
export GRT_DRY_RUN=0
mkdir -p "$HOME"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/design-bank.sh"

fail() { echo "FAIL $*" >&2; exit 1; }

valid="$tmp/valid"
mkdir -p "$valid/Refero/bank" "$valid/motionsites/library"
echo '{}' > "$valid/Refero/bank/catalog.json"
echo '{}' > "$valid/motionsites/library/catalog.json"
[[ "$(grt_design_bank_action "$valid")" == reuse ]] || fail "valid bank should reuse"

missing="$tmp/missing"
[[ "$(grt_design_bank_action "$missing")" == create ]] || fail "absent dest should create"

empty="$tmp/empty"
mkdir -p "$empty"
[[ "$(grt_design_bank_action "$empty")" == create ]] || fail "empty dest should create"

invalid="$tmp/invalid"
mkdir -p "$invalid/leftover"
echo junk > "$invalid/leftover/file"
[[ "$(grt_design_bank_action "$invalid")" == fail ]] || fail "invalid nonempty dest should fail"

echo "OK  design-bank dest policy"
printf 'test-design-bank passed\n'
