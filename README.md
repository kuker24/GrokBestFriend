# GrokBestFriend

Portable snapshot of a live GrokBuild setup: skills, routing rules, hooks, MCP, helper CLIs, and the Refero + Motionsites design bank.

This is not Grok itself. It installs the official Grok CLI, then layers the same system on top.

**Current: [v1.0.0](https://github.com/kuker24/GrokBestFriend/releases/tag/v1.0.0)** · Linux x86_64 · design bank is a Release asset (`Design-bank.tgz`, ~412MB)

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
```

## What is installed

| Surface | Now |
| --- | --- |
| Grok CLI | Official installer if `grok` is missing |
| User skills | 18 skills, including the design stack |
| Rules | `00-routing.md`, `01-verification.md` |
| Hook | `~/.grok/hooks/impeccable.json` |
| Config | models, UI, official marketplace, Claude/Cursor compat **off** |
| MCP | `codebase-memory-mcp` + `context7` **on**; `serena` + `exa` registered but **off** |
| Tools | `serena`, `browser-act`, `semgrep`, `osv-scanner`, `gitleaks`, `grok-chromium-cdp` |
| Plugins | none (matches the source machine) |
| Design bank | Refero + Motionsites → `~/Design` |

### User skills

**Design:** `/found-this-design` `/impeccable` `/visual-studio` `/scroll-world` `/emil-design-eng`

**Matt:** `/ask-matt` `/grill-with-docs` `/to-spec` `/to-tickets` `/tdd` `/matt-implement` `/matt-code-review`

**Browser / GitHub / risk:** `/browser-act` `/chrome-devtools-axi` `/gh-axi` `/full-audit-keamanan` `/full-performance-audit` `/adhd`

Bundled Grok skills (`/implement`, `/review`, `/imagine`, `/design`, game-asset-*, …) come from the Grok binary, not this repo.

## Design bank

`/found-this-design` needs two catalogs:

- `Refero/bank/catalog.json`
- `motionsites/library/catalog.json`

The packed bank lives on the release, not in git:

https://github.com/kuker24/GrokBestFriend/releases/download/v1.0.0/Design-bank.tgz

SHA-256 is pinned in `vendor/sources.json`. Details: [docs/design-bank.md](docs/design-bank.md).

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

## macOS

Skills, rules, hooks, HTTP MCP, and the Grok CLI work. The pinned Codebase Memory artifact is Linux x86_64 only.
