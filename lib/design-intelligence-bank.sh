#!/usr/bin/env bash

grt_di_cli() {
  # Installer operations must use the checkout CLI, not a stale ~/.grok copy.
  printf '%s\n' "$GRT_ROOT/scripts/design-intelligence.py"
}

grt_di_target() {
  if [[ -n "${GROK_DESIGN_INTELLIGENCE_BANK:-}" ]]; then
    printf '%s\n' "${GROK_DESIGN_INTELLIGENCE_BANK}"
    return 0
  fi
  printf '%s\n' "${HOME}/DesignIntelligence"
}

grt_di_print_status() {
  local engine="INSTALLED"
  local bank="SKIPPED"
  if [[ ! -f "$GRT_ROOT/scripts/design-intelligence.py" ]]; then
    engine="MISSING"
  fi
  if [[ "$GRT_DI_BANK_REQUEST" == 1 ]]; then
    bank="REQUESTED"
  elif [[ -d "$(grt_di_target)" ]]; then
    bank="PRESENT"
  else
    bank="MISSING"
  fi
  grt_info "Design Intelligence engine = ${engine}"
  grt_info "Design Intelligence bank = ${bank}"
}

grt_di_python() {
  local phase="$1"
  shift
  PYTHONDONTWRITEBYTECODE=1 python3 "$(grt_di_cli)" bootstrap --phase "$phase" \
    --home "$HOME" \
    --grok-home "$GRT_HOME" \
    --target "$(grt_di_target)" \
    "$@"
}

grt_di_resolve_request() {
  if [[ "$GRT_DI_BANK_SKIP" == 1 ]]; then
    GRT_DI_BANK_REQUEST=0
    GRT_DI_ARCHIVE_DIR=""
    return 0
  fi
  if [[ "$GRT_DI_BANK_REQUEST" != 1 ]]; then
    GRT_DI_ARCHIVE_DIR=""
    return 0
  fi
  if [[ -z "$GRT_DI_ARCHIVE_DIR" ]]; then
    GRT_DI_ARCHIVE_DIR="${GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR:-}"
  fi
  if [[ -z "$GRT_DI_ARCHIVE_DIR" ]]; then
    grt_die "FAIL DESIGN_INTELLIGENCE_ARCHIVE_DIR_REQUIRED"
  fi
}

grt_di_preflight() {
  GRT_DI_ACTION="skip"
  GRT_DI_CREATED=0
  GRT_DI_STAGING=""
  GRT_DI_RECOVERY=""
  GRT_DI_SNAPSHOT=""
  GRT_DI_MANIFEST_FILE=""
  grt_di_print_status
  if [[ "$GRT_DI_BANK_REQUEST" != 1 ]]; then
    grt_info "Design Intelligence bank import skipped (no --with-design-intelligence-bank)"
    return 0
  fi
  local out
  out="$(mktemp)"
  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    if ! grt_di_python preflight --archive-dir "$GRT_DI_ARCHIVE_DIR" --dry-run >"$out"; then
      rm -f -- "$out"
      grt_die "Design Intelligence bank dry-run preflight failed"
    fi
    python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for line in payload.get("would") or []:
    print(line)
PY
    rm -f -- "$out"
    return 0
  fi
  if ! grt_di_python preflight --archive-dir "$GRT_DI_ARCHIVE_DIR" >"$out"; then
    cat "$out" >&2 || true
    rm -f -- "$out"
    grt_die "Design Intelligence bank preflight failed"
  fi
  GRT_DI_ACTION="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("action") or "create")
PY
)"
  GRT_DI_SNAPSHOT="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("snapshot") or "")
PY
)"
  GRT_DI_TARGET_DISPLAY="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("target") or "~/DesignIntelligence")
PY
)"
  mkdir -p -- "$GRT_RUNTIME"
  GRT_DI_MANIFEST_FILE="$GRT_RUNTIME/di-manifest.json"
  cp -a -- "$out" "$GRT_RUNTIME/di-preflight.json"
  rm -f -- "$out"
  grt_info "Design Intelligence bank action = ${GRT_DI_ACTION}"
}

grt_di_stage() {
  if [[ "$GRT_DRY_RUN" == 1 || "$GRT_DI_BANK_REQUEST" != 1 || "$GRT_DI_ACTION" != "create" ]]; then
    return 0
  fi
  local out tx
  tx="$(python3 - <<'PY'
import os, secrets, datetime
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
print(f"{now}-{os.getpid()}-{secrets.token_hex(4)}")
PY
)"
  out="$(mktemp)"
  if ! grt_di_python stage --archive-dir "$GRT_DI_ARCHIVE_DIR" --transaction-id "$tx" >"$out"; then
    cat "$out" >&2 || true
    rm -f -- "$out"
    grt_die "Design Intelligence bank staging failed"
  fi
  GRT_DI_STAGING="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("staging_path") or "")
PY
)"
  GRT_DI_CREATED=1
  cp -a -- "$out" "$GRT_RUNTIME/di-stage.json"
  rm -f -- "$out"
  [[ -n "$GRT_DI_STAGING" && -d "$GRT_DI_STAGING" ]] || grt_die "Design Intelligence staging path missing"
}

grt_di_promote() {
  if [[ "$GRT_DRY_RUN" == 1 || "$GRT_DI_BANK_REQUEST" != 1 ]]; then
    return 0
  fi
  if [[ "$GRT_DI_ACTION" == "reuse" ]]; then
    grt_info "BANK_ACTION = REUSE_EXISTING"
    grt_di_python verify-search --archive-dir "$GRT_DI_ARCHIVE_DIR" >/dev/null
    return 0
  fi
  if [[ "$GRT_DI_ACTION" != "create" ]]; then
    return 0
  fi
  [[ -n "$GRT_DI_STAGING" && -d "$GRT_DI_STAGING" ]] || grt_die "Design Intelligence staging missing before promote"
  local out
  out="$(mktemp)"
  if ! grt_di_python promote --archive-dir "$GRT_DI_ARCHIVE_DIR" --staging "$GRT_DI_STAGING" >"$out"; then
    cat "$out" >&2 || true
    rm -f -- "$out"
    grt_die "Design Intelligence bank promotion failed"
  fi
  GRT_DI_STAGING=""
  GRT_DI_CREATED=1
  python3 - "$out" "$GRT_RUNTIME/di-manifest.json" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
manifest = payload.get("manifest") or {}
Path(sys.argv[2]).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("BANK_INTEGRITY = %s" % (payload.get("bank_integrity") or "PASS"))
print("BANK_CONTENT_READINESS = %s" % (payload.get("bank_content_readiness") or "DEGRADED"))
print("INSTALL_RESULT = %s" % (payload.get("install_result") or "SUCCESS_WITH_EXPECTED_LIMITATIONS"))
PY
  rm -f -- "$out"
}

grt_di_cleanup_staging() {
  if [[ -n "${GRT_DI_STAGING:-}" && -e "$GRT_DI_STAGING" ]]; then
    grt_di_python remove-staging --staging "$GRT_DI_STAGING" >/dev/null || true
    GRT_DI_STAGING=""
  fi
}

grt_di_recover_promoted() {
  if [[ "${GRT_DI_CREATED:-0}" != 1 ]]; then
    return 0
  fi
  local target recovery
  target="$(grt_di_target)"
  if [[ ! -e "$target" ]]; then
    return 0
  fi
  recovery="${HOME}/DesignIntelligence.recovery.$(python3 - <<'PY'
import os, secrets, datetime
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
print(f"{now}-{os.getpid()}-{secrets.token_hex(4)}")
PY
)"
  if grt_di_python recover-created --staging "$recovery" >/dev/null; then
    GRT_DI_RECOVERY="$recovery"
    grt_warn "moved Design Intelligence bank to $recovery"
  fi
}

grt_install_design_intelligence_bank() {
  grt_di_promote
}
