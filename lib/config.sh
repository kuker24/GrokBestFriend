#!/usr/bin/env bash

grt_merge_user_config() {
  local config="$GRT_HOME/config.toml"
  local template="$GRT_VENDOR/config/user.toml"
  [[ -f "$template" ]] || grt_die "missing $template"

  if [[ "$GRT_DRY_RUN" == 1 ]]; then
    grt_info "WOULD_MERGE_CONFIG $config"
    return 0
  fi

  mkdir -p -- "$GRT_HOME"
  if [[ ! -f "$config" ]]; then
    cp -- "$template" "$config"
    chmod 600 -- "$config"
    return 0
  fi

  python3 - "$config" "$template" <<'PY'
from pathlib import Path
import sys
import tomllib

config_path = Path(sys.argv[1])
template_path = Path(sys.argv[2])
text = config_path.read_text(encoding="utf-8")
existing = tomllib.loads(text)
wanted = tomllib.loads(template_path.read_text(encoding="utf-8"))
append: list[str] = []

def has_table(name: str) -> bool:
    node = existing
    for part in name.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True

# Marketplace source
sources = existing.get("marketplace", {}).get("sources") or []
has_official = any(
    isinstance(item, dict) and item.get("name") == "xAI Official"
    for item in sources
)
if not has_official:
    append.append(
        '\n[[marketplace.sources]]\nname = "xAI Official"\ngit = "https://github.com/xai-org/plugin-marketplace.git"\n'
    )

if "marketplace" not in existing:
    append.append(
        "\n[marketplace]\ndefault_skills_installs_purged = true\nofficial_marketplace_auto_installed = true\n"
    )

if "models" not in existing:
    append.append('\n[models]\ndefault = "grok-4.6"\ndefault_reasoning_effort = "high"\n')
if "ui" not in existing:
    append.append(
        '\n[ui]\nmax_thoughts_width = 120\nfork_secondary_model = "grok-4.5"\nyolo = false\ncompact_mode = false\npermission_mode = "ask"\n'
    )

for vendor in ("claude", "cursor"):
    key = f"compat.{vendor}"
    if not has_table(key):
        append.append(
            f"\n[compat.{vendor}]\nskills = false\nrules = false\nagents = false\nmcps = false\nhooks = false\n"
        )

if "skills" not in existing:
    append.append(
        '\n[skills]\nignore = [\n    "~/.claude/skills/implement",\n    "~/.claude/skills/code-review",\n]\n'
    )
elif "~/.claude/skills/implement" not in text:
    raise SystemExit("refusing to rewrite an existing [skills] section that lacks Claude ignore paths")

if append:
    config_path.write_text(text.rstrip() + "\n" + "".join(append), encoding="utf-8")
PY
}
