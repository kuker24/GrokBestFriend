# GrokBestFriend

Portable snapshot of a live GrokBuild setup: skills, routing rules, hooks, MCP, helper CLIs, and the Refero + Motionsites design bank.

This is not Grok itself. It installs the official Grok CLI, then layers the same system on top.

**Current: v1.2.0** · Linux x86_64 · design bank is still the [v1.0.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.0.0) Release asset (`Design-bank.tgz`, ~412MB). Refero/Motionsites redistribution is **not cleared** — see `THIRD_PARTY_NOTICES.md`.

## New laptop

```bash
git clone https://github.com/kuker24/GrokBestFriend.git
cd GrokBestFriend
./install.sh
```

Then sign in:

```bash
grok login
gh auth login
```

`./install.sh` also downloads the design bank, checksums it, restores it to `~/Design`, and sets `GROK_DESIGN_BANK`. Skip that with `--skip-design-bank`.

Check:

```bash
./install.sh --dry-run
./install.sh --doctor
./restore.sh --list
```

CI on `main` runs overlay, doctor dry-run, secret scan, MCP policy fixtures, routing eval, source integrity, snapshot allowlist, and transactional install tests.

`./uninstall.sh` removes **owned** skills/rules/hooks/helper/manifest and leaves the Grok CLI, credentials, foreign skills, and the learning log in place. `./restore.sh` rolls back the last **managed** backup (skills/rules/hooks/config/helper/manifest, plus rc snippets this run added). Grok CLI, `uv`, and host tools are residual and are not uninstalled on rollback.

## What is installed

| Surface | Now |
| --- | --- |
| Grok CLI | Official installer if `grok` is missing |
| User skills | 18 skills, including the design stack |
| Rules | `00-routing.md`, `01-verification.md` |
| Hook | `~/.grok/hooks/impeccable.json` |
| Config | models, UI, official marketplace, Claude/Cursor compat **off** |
| MCP | `codebase-memory-mcp` + `context7` + `shadcn` **on**; `serena` + `exa` registered but **off** |
| Tools | `serena`, `browser-act`, `semgrep`, `osv-scanner`, `gitleaks`, `grok-chromium-cdp` |
| Plugins | none (matches the source machine) |
| Design bank | Refero + Motionsites → `~/Design` |

### User skills

**Design:** `/found-this-design` `/impeccable` `/visual-studio` `/scroll-world` `/emil-design-eng`

**Matt:** `/ask-matt` `/grill-with-docs` `/to-spec` `/to-tickets` `/tdd` `/matt-implement` `/matt-code-review`

**Browser / GitHub / risk:** `/browser-act` `/chrome-devtools-axi` `/gh-axi` `/full-audit-keamanan` `/full-performance-audit` `/adhd`

Bundled Grok skills (`/implement`, `/review`, `/imagine`, `/design`, game-asset-*, …) come from the Grok binary, not this repo. Ordinary writes stay in-session; `/implement` is user-explicit.

## Design bank

`/found-this-design` needs two catalogs:

- `Refero/bank/catalog.json`
- `motionsites/library/catalog.json`

The packed bank lives on the release, not in git:

https://github.com/kuker24/GrokBestFriend/releases/download/v1.0.0/Design-bank.tgz

SHA-256 is pinned in `vendor/sources.json`. Details: [docs/design-bank.md](docs/design-bank.md).

A separate **Design Intelligence** catalog (`GROK_DESIGN_INTELLIGENCE_BANK`, default `~/DesignIntelligence`) is a v1.2.0 candidate library. It is not active routing, it does not change `/found-this-design` or `~/Design`, and `VERSION` stays 1.2.0. See [docs/design-intelligence.md](docs/design-intelligence.md).

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

See [docs/secrets-policy.md](docs/secrets-policy.md) and [docs/new-laptop.md](docs/new-laptop.md).

## Refresh this snapshot

On the source machine, after skills or rules change:

```bash
./scripts/snapshot-live.sh
```

Snapshot copies only the 18 official user skills. Extra live skills abort the snapshot unless you pass `--ignore-extra NAME` (they are never copied). New skills enter vendor only through the allowlist. `/to-spec` and `/to-tickets` write under `.scratch/`, which is gitignored.

Install is exclusive-locked and journaled (`PREPARING` → `COMMITTED`). A leftover `SWAPPED` transaction refuses a new install; recover with `./install.sh --recover` or `./restore.sh`. Unowned `skills/implement` / `skills/code-review` (no GBF marker, not in the GBF manifest) fail the install instead of being deleted. After `main` is protected, run `./scripts/enable-main-protection.sh` anytime (repo admin); the script reconciles a single `main-ci` ruleset and fails if duplicates exist.

## macOS

Skills, rules, hooks, HTTP MCP, and the Grok CLI work. The pinned Codebase Memory artifact is Linux x86_64 only.
