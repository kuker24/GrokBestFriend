#!/usr/bin/env bash
# Backward-compatible entry. Prefer ./install.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/install.sh" "$@"
