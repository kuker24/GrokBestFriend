#!/usr/bin/env bash

grt_merge_user_config() {
  local config="$GRT_HOME/config.toml"
  local template="$GRT_VENDOR/config/user.toml"
  local policy="$GRT_VENDOR/runtime-policy.json"
  [[ -f "$template" ]] || grt_die "missing $template"
  [[ -f "$policy" ]] || grt_die "missing $policy"

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_ENFORCE_CONFIG $config"
    return 0
  fi

  mkdir -p -- "$GRT_HOME"
  if [[ ! -f "$config" ]]; then
    cp -- "$template" "$config"
    chmod 600 -- "$config"
  fi

  python3 "$GRT_ROOT/lib/runtime_policy.py" apply --config "$config" --policy "$policy" --template "$template" \
    || grt_die "runtime policy refused to mutate $config"
}
