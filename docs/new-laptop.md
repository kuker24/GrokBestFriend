# New laptop

Target: Linux x86_64, same shape as the source machine.

## 1. System packages

Need `git`, `curl`, `python3`, `tar`, and Node.js `>=20.18.1` plus `npx`. Chromium (not Google Chrome) for browser skills. GitHub CLI (`gh`) for `/gh-axi`.

Ubuntu example:

```bash
sudo apt update
sudo apt install -y git curl python3 tar chromium-browser gh
# Node: use nvm or the distro nodejs package, >=20.18.1 (shadcn 4.18.0 engines)
```

## 2. Clone and install

Standard install:

```bash
git clone https://github.com/kuker24/GrokBestFriend.git
cd GrokBestFriend
./install.sh --dry-run
./install.sh
```

Result: GrokBestFriend + Refero/Motionsites Design Bank. The Design Intelligence **engine** is installed. The Design Intelligence **bank** is missing/`DEGRADED` until you import packs.

Full install, only with four local Open Design ZIPs you already have the right to use:

```bash
./install.sh --dry-run --with-design-intelligence-bank ~/OpenDesignPacks
./install.sh --with-design-intelligence-bank ~/OpenDesignPacks
```

Result: the same as standard install, plus a 906-item local catalog at `~/DesignIntelligence` when the archives match known snapshot `od-packs-2026-07-20`.

The repository does not redistribute Open Design packs. The installer only imports archives explicitly supplied by the user. Do not expect those ZIPs on GitHub or in a Release.

Open a new terminal so `~/.grok/bin` and `~/.local/bin` are on PATH, or:

```bash
export PATH="$HOME/.grok/bin:$HOME/.local/bin:$PATH"
```

## 3. Sign in

```bash
grok login
gh auth login
```

These write credentials outside this repo. Never commit them.

## 4. Confirm

```bash
./install.sh --doctor
grok --version
grok mcp list
grok plugin list
```

Expected MCP: `codebase-memory-mcp`, `context7`, and `shadcn` enabled **and healthy**; `serena` and `exa` registered but disabled. Plugin list empty. Doctor fails if a required server is missing, disabled, on the wrong URL/command, or unhealthy. `shadcn` is the pinned CLI (`npx -y shadcn@<version in vendor/sources.json> mcp`). Preflight fails with `FAIL NODE_VERSION` unless Node is `>=20.18.1` and `npx` is on PATH.

If install fails after the swap, or the process dies mid-transaction, the installer restores **managed** surfaces (skills/rules/hooks/config/helper/manifest, plus rc snippets it added). A Design Intelligence bank created in the same run is moved to a recovery directory instead of being deleted. `./install.sh --recover` and `./restore.sh` reload Design Intelligence paths from the private journal, so a crash that drops the original shell still cleans staging or moves a created bank. It does **not** uninstall a Grok CLI or `uv` that this run installed, and it does not delete a healthy reused `~/DesignIntelligence`. Manual rollback: `./restore.sh`. Leftover `SWAPPED` / `BANK_PROMOTED` state: `./install.sh --recover`. Dry-run must not create `~/DesignIntelligence` or its parent.

`./install.sh --doctor --strict` still fails on engine/CLI damage and `BANK_BLOCKED`. Expected bank content limitations stay `DEGRADED` and do not force a nonzero exit. A missing bank is `DEGRADED`, not an engine failure.

Foreign skills, rules, and hooks stay in place. An unowned `~/.grok/skills/implement` or `code-review` (no `.grokbestfriend-owned.json`, not listed in the GBF manifest) fails install instead of being deleted.

## 5. Optional surfaces

| Need | Action |
| --- | --- |
| Design matching (`/found-this-design`) | Included by `./install.sh` (bank → `~/Design`) |
| Design Intelligence catalog | Optional: `./install.sh --with-design-intelligence-bank ~/OpenDesignPacks` |
| UI registry hub (`shadcn`) | Included by `./install.sh`. Use only in a React project with `components.json` |
| Exa search | Finish Exa OAuth, then `grok mcp enable exa` |
| Exact symbol MCP | `grok mcp enable serena` only when Codebase Memory is not enough |

## 6. First project

`cd` into a repo and run `grok`. Routing lives in `~/.grok/rules/`. Do not enable every MCP at once.
