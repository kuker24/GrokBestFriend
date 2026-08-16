#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

fail() { echo "FAIL $*" >&2; exit 1; }

bin="$tmp/bin"
mkdir -p "$bin"
ln -s "$(command -v python3)" "$bin/python3"
# Isolate only the require_node subshell so the harness still has grep/chmod.

write_fake() {
  local name="$1" body="$2"
  printf '%s\n' "$body" >"$bin/$name"
  chmod 755 "$bin/$name"
}

require_with_fakes() {
  PATH="$bin" grt_require_node
}

rm -f -- "$bin/node" "$bin/npx"
if (require_with_fakes) >"$tmp/out" 2>"$tmp/err"; then
  fail "missing node was accepted"
fi
grep -q 'FAIL NODE_MISSING' "$tmp/err" || fail "missing node did not emit NODE_MISSING"
echo "OK  missing node fails NODE_MISSING"

write_fake node '#!/bin/bash
echo v20.18.1
'
if (require_with_fakes) >"$tmp/out" 2>"$tmp/err"; then
  fail "missing npx was accepted"
fi
grep -q 'FAIL NPX_MISSING' "$tmp/err" || fail "missing npx did not emit NPX_MISSING"
echo "OK  missing npx fails NPX_MISSING"

write_fake npx '#!/bin/bash
exit 0
'
write_fake node '#!/bin/bash
echo v18.20.8
'
if (require_with_fakes) >"$tmp/out" 2>"$tmp/err"; then
  fail "Node 18 was accepted"
fi
grep -q 'FAIL NODE_VERSION' "$tmp/err" || fail "Node 18 did not emit NODE_VERSION"
grep -q 'shadcn@4.18.0 requires Node >=20.18.1' "$tmp/err" || fail "Node 18 error missing pin"
grep -q 'found: v18.20.8' "$tmp/err" || fail "Node 18 error missing found version"
echo "OK  Node 18 fails NODE_VERSION"

write_fake node '#!/bin/bash
echo v20.18.1
'
if ! (require_with_fakes) >"$tmp/out" 2>"$tmp/err"; then
  fail "Node 20.18.1 was rejected: $(cat "$tmp/err")"
fi
echo "OK  Node 20.18.1 passes"

printf 'test-node-preflight passed\n'
