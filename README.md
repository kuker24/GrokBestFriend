# GrokBestFriend

Portable snapshot of a live GrokBuild setup: skills, routing rules, hooks, MCP, helper CLIs, the Refero + Motionsites design bank, and the Design Intelligence engine.

This is not Grok itself. It installs the official Grok CLI, then layers the same system on top.

```text
product                 = 1.3.1
host                    = Linux x86_64
grok_cli_seen           = 1.0.4
user_skills             = 18
rules                   = 00-routing.md, 01-verification.md
mcp_on                  = codebase-memory-mcp, context7, shadcn
mcp_off                 = serena, exa
plugins                 = none
design_bank             = ~/Design  (Refero + Motionsites)
design_intelligence     = engine packaged; bank optional
```

**Current: [v1.3.1](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.3.1)** · Linux x86_64 · Refero/Motionsites archive is still the [v1.0.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.0.0) asset (`Design-bank.tgz`, ~412MB). Refero/Motionsites redistribution is **not cleared** — see `THIRD_PARTY_NOTICES.md`. Open Design packs are **not** in git and are **not** a Release asset.

## New laptop

Standard install (engine + Refero/Motionsites; Design Intelligence bank stays missing/`DEGRADED`):

```bash
git clone https://github.com/kuker24/GrokBestFriend.git
cd GrokBestFriend
./install.sh
```

Full install, only if you already have the four Open Design ZIPs locally:

```bash
./install.sh --with-design-intelligence-bank ~/OpenDesignPacks
```

The folder must contain exactly one `design-systems*.zip`, `design-templates*.zip`, `plugins*.zip`, and `skills*.zip`. Automation can set `GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR` instead of the path argument. `./install.sh` without the flag does not search the home directory for those ZIPs.

Then sign in:

```bash
grok login
gh auth login
```

`./install.sh` also downloads the design bank, checksums it, restores it to `~/Design`, and sets `GROK_DESIGN_BANK`. Skip that with `--skip-design-bank`. Skip the intelligence-bank import with `--skip-design-intelligence-bank` (the default).

Check:

```bash
./install.sh --dry-run
./install.sh --doctor
./restore.sh --list
```

CI on `main` runs overlay, doctor dry-run, secret scan, MCP policy fixtures, routing eval, source integrity, snapshot allowlist, Design Intelligence catalog/bootstrap tests, and transactional install tests.

`./uninstall.sh` removes **owned** skills/rules/hooks/helper/manifest and leaves the Grok CLI, credentials, foreign skills, the learning log, and `~/DesignIntelligence` in place. `./restore.sh` rolls back the last **managed** backup (skills/rules/hooks/config/helper/manifest, plus rc snippets this run added). Grok CLI, `uv`, and host tools are residual and are not uninstalled on rollback.

## What is installed

| Surface | Now |
| --- | --- |
| Grok CLI | Official installer if `grok` is missing (source machine saw **1.0.4**) |
| User skills | 18 skills, including the design stack |
| Rules | `00-routing.md`, `01-verification.md` |
| Hook | `~/.grok/hooks/impeccable.json` |
| Config | models, UI, official marketplace, Claude/Cursor compat **off** |
| MCP | `codebase-memory-mcp` + `context7` + `shadcn` **on**; `serena` + `exa` registered but **off** |
| Tools | `serena` 1.6.1, `browser-act` 1.3.0, `semgrep` 1.171.0, `osv-scanner` 2.4.0, `gitleaks` 8.30.1, `grok-chromium-cdp` |
| Node | `>=20.18.1` plus `npx` (shadcn 4.18.0 engines) |
| Plugins | none (matches the source machine) |
| Design bank | Refero + Motionsites → `~/Design` (`GROK_DESIGN_BANK`) |
| Design Intelligence | Impeccable-owned lazy retrieval; optional local bank → `~/DesignIntelligence` |

### User skills

**Design:** `/found-this-design` `/impeccable` `/visual-studio` `/scroll-world` `/emil-design-eng`

**Matt:** `/ask-matt` `/grill-with-docs` `/to-spec` `/to-tickets` `/tdd` `/matt-implement` `/matt-code-review`

**Browser / GitHub / risk:** `/browser-act` `/chrome-devtools-axi` `/gh-axi` `/full-audit-keamanan` `/full-performance-audit` `/adhd`

Bundled Grok skills (`/implement`, `/review`, `/imagine`, `/design`, game-asset-*, …) come from the Grok binary, not this repo. Ordinary writes stay in-session; `/implement` is user-explicit.

## Two design banks

These are separate. Do not merge them.

| Bank | Env | Default | Used by |
| --- | --- | --- | --- |
| Refero + Motionsites | `GROK_DESIGN_BANK` | `~/Design` | `/found-this-design` |
| Design Intelligence catalog | `GROK_DESIGN_INTELLIGENCE_BANK` | `~/DesignIntelligence` | Impeccable `new-work` only |

`/found-this-design` needs two catalogs inside `~/Design`:

- `Refero/bank/catalog.json`
- `motionsites/library/catalog.json`

The packed Refero/Motionsites bank lives on the **v1.0.0** release, not in git:

https://github.com/kuker24/GrokBestFriend/releases/download/v1.0.0/Design-bank.tgz

SHA-256 is pinned in `vendor/sources.json`. Details: [docs/design-bank.md](docs/design-bank.md).

Design Intelligence is not a second primary router. Narrow refinement skips it, established worlds retrieve structure only, and new/replacement worlds may retrieve at most five systems and three structures. It does not change `/found-this-design` or `~/Design`, activate ZIP specialists, or redistribute the raw packs.

The installer only imports archives the operator supplies. A successful known-snapshot import (`od-packs-2026-07-20`) indexes **906** catalog items (151 systems, 114 structures, 479 recipes, 162 specialists; 256 aliases, 85 stubs, 7 quarantined) and stays `DEGRADED` for unknown licenses, stubs, quarantine, and missing optional connectors. That `DEGRADED` state is an expected content limitation, not an install blocker.

The bank target cannot be `/`, `$HOME`, `~/.grok` or anything inside it, a Git repository, the archive directory, or a path that reaches those locations through a symlink. Dry-run never creates the target or its parent. See [docs/design-intelligence.md](docs/design-intelligence.md).

## After install (human only)

```bash
grok mcp enable exa       # after Exa OAuth
grok mcp enable serena    # only for exact symbol work
```

## What is never copied

- Login files and tokens
- Session history, logs, caches
- Trusted-folder list
- Custom gateway URLs or model-mapping tables
- Open Design ZIP packs

See [docs/secrets-policy.md](docs/secrets-policy.md) and [docs/new-laptop.md](docs/new-laptop.md).

## Releases

| Version | Date | What shipped |
| --- | --- | --- |
| [v1.3.1](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.3.1) | 2026-08-17 | Optional transactional Design Intelligence bank bootstrap from local Open Design ZIPs |
| [v1.3.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.3.0) | 2026-08-17 | Design Intelligence catalog + bounded Impeccable `new-work` retrieval |
| [v1.2.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.2.0) | 2026-08-16 | Pinned shadcn MCP as the UI registry hub |
| [v1.1.1](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.1.1) | 2026-08-16 | Foreign-skill preserve, ownership markers, crash-safe install journal |
| [v1.1.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.1.0) | 2026-08-16 | CI, routing eval, transactional install, measured MCP/routing |
| [v1.0.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.0.0) | 2026-08-15 | First public snapshot + `Design-bank.tgz` (Refero + Motionsites) |

Full notes live on the [Releases](https://github.com/kuker24/GrokBestFriend/releases) page. `Design-bank.tgz` stays attached only to **v1.0.0**. Later software tags do not re-upload it.

## Refresh this snapshot

On the source machine, after skills or rules change:

```bash
./scripts/snapshot-live.sh
```

Snapshot copies only the 18 official user skills. Extra live skills abort the snapshot unless you pass `--ignore-extra NAME` (they are never copied). New skills enter vendor only through the allowlist. `/to-spec` and `/to-tickets` write under `.scratch/`, which is gitignored.

Install is exclusive-locked and journaled (`PREPARING` → `BANK_STAGED` → `GROK_SWAPPED` → `BANK_PROMOTED` → `COMMITTED` when a bank is created). A leftover `SWAPPED` / `GROK_SWAPPED` / `BANK_PROMOTED` transaction refuses a new install; recover with `./install.sh --recover` or `./restore.sh`. `./restore.sh --list` says whether a backup created a Design Intelligence bank. `./uninstall.sh` keeps `~/DesignIntelligence`. Unowned `skills/implement` / `skills/code-review` (no GBF marker, not in the GBF manifest) fail the install instead of being deleted. After `main` is protected, run `./scripts/enable-main-protection.sh` anytime (repo admin); the script reconciles a single `main-ci` ruleset and fails if duplicates exist.

## macOS

Skills, rules, hooks, HTTP MCP, and the Grok CLI work. The pinned Codebase Memory artifact is Linux x86_64 only.
