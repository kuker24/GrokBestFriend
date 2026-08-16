# New laptop

Target: Linux x86_64, same shape as the source machine.

## 1. System packages

Need `git`, `curl`, `python3`, `tar`, and Node.js (20+). Chromium (not Google Chrome) for browser skills. GitHub CLI (`gh`) for `/gh-axi`.

Ubuntu example:

```bash
sudo apt update
sudo apt install -y git curl python3 tar chromium-browser gh
# Node: use nvm or the distro nodejs package, 20+
```

## 2. Clone and install

```bash
git clone https://github.com/kuker24/GrokBestFriend.git
cd GrokBestFriend
./install.sh --dry-run
./install.sh
```

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

Expected MCP: `codebase-memory-mcp` and `context7` enabled **and healthy**; `serena` and `exa` registered but disabled. Plugin list empty. Doctor fails if a required server is missing, disabled, on the wrong URL/command, or unhealthy.

If install fails after the swap, or the process dies mid-transaction, the installer restores **managed** surfaces (skills/rules/hooks/config/helper/manifest, plus rc snippets it added). It does **not** uninstall a Grok CLI or `uv` that this run installed. Manual rollback: `./restore.sh`. Leftover `SWAPPED` state: `./install.sh --recover`.

Foreign skills, rules, and hooks stay in place. An unowned `~/.grok/skills/implement` or `code-review` (no `.grokbestfriend-owned.json`, not listed in the GBF manifest) fails install instead of being deleted.

## 5. Optional surfaces

| Need | Action |
| --- | --- |
| Design matching (`/found-this-design`) | Included by `./install.sh` (bank → `~/Design`) |
| Exa search | Finish Exa OAuth, then `grok mcp enable exa` |
| Exact symbol MCP | `grok mcp enable serena` only when Codebase Memory is not enough |

## 6. First project

`cd` into a repo and run `grok`. Routing lives in `~/.grok/rules/`. Do not enable every MCP at once.
