#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
failed=0

fail() { printf 'FAIL %s\n' "$*" >&2; failed=1; }
ok() { printf 'OK  %s\n' "$*"; }

if grep -R -n --exclude-dir=.git --exclude='PRD-CLAUDE-CODE-SYSTEM.md' \
    -E '/home/[^/]+/' "$ROOT/vendor" "$ROOT/templates" >/dev/null; then
  fail "machine home path leaked"
  grep -R -n --exclude-dir=.git --exclude='PRD-CLAUDE-CODE-SYSTEM.md' -E '/home/[^/]+/' \
    "$ROOT/vendor" "$ROOT/templates" || true
else
  ok "no machine home path in installer surfaces"
fi

if grep -R -n --exclude-dir=.git \
    -E 'XAI_API_KEY=|gho_[A-Za-z0-9]{10,}|xai-[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9._-]{20,}' \
    "$ROOT/vendor" "$ROOT/lib" "$ROOT/templates" "$ROOT/docs" >/dev/null; then
  fail "secret-like token pattern found"
  grep -R -n --exclude-dir=.git \
    -E 'XAI_API_KEY=|gho_[A-Za-z0-9]{10,}|xai-[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9._-]{20,}' \
    "$ROOT/vendor" "$ROOT/lib" "$ROOT/templates" "$ROOT/docs" || true
else
  ok "no token-like strings in vendor/docs/lib"
fi

if [[ -e "$ROOT/auth.json" ]]; then
  fail "auth.json must not be in the repo"
else
  ok "no auth.json"
fi

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi
printf 'test-no-secrets passed\n'
