# GrokBestFriend

Portable snapshot of the GrokBuild system running on the source Linux machine: user skills, routing rules, hooks, MCP registrations, helper CLIs, and a one-command installer.

This is not Grok itself. It installs the official Grok CLI, then layers the same system on top.

## New laptop

Linux x86_64:

```bash
git clone https://github.com/kuker24/GrokBestFriend.git
cd GrokBestFriend
./install.sh --dry-run
./install.sh
```

Then, as you:

```bash
grok login
gh auth login
```

Optional later:

```bash
grok mcp enable exa       # after Exa OAuth
grok mcp enable serena    # only for exact symbol work
```

Doctor:

```bash
./install.sh --doctor
```

## What you get

| Surface | Result |
| --- | --- |
| Grok CLI | Official installer if `grok` is missing |
| Skills | 18 user skills in `~/.grok/skills/` |
| Rules | `00-routing.md`, `01-verification.md` |
| Hook | `~/.grok/hooks/impeccable.json` |
| Config | models, UI, marketplace, compat off, Claude skill ignore |
| MCP | `codebase-memory-mcp` and `context7` on; `serena` and `exa` registered but off |
| Tools | `serena`, `browser-act`, `semgrep`, `osv-scanner`, `gitleaks`, `grok-chromium-cdp` |
| Plugins | none (matches the source machine) |
| Design bank | Refero + Motionsites restored to `~/Design` (or kept if already present) |

Bundled Grok skills (`/implement`, `/review`, `/imagine`, …) come from the Grok binary, not this repo.

## What is never copied

- Login files and tokens
- Session history, logs, caches
- Trusted-folder list
- Custom gateway URLs or model-mapping tables
See [docs/secrets-policy.md](docs/secrets-policy.md) and [docs/new-laptop.md](docs/new-laptop.md).

## Design bank

`./install.sh` downloads the packed Refero + Motionsites bank from the GitHub Release and restores it to `~/Design`. The archive is not stored in git (about 412MB compressed). Skip with `--skip-design-bank`. See [docs/design-bank.md](docs/design-bank.md).

## Refresh this snapshot

On the source machine, after you change skills or rules:

```bash
./scripts/snapshot-live.sh
```

## macOS

Skills, rules, hooks, HTTP MCP, and the Grok CLI work. The pinned Codebase Memory artifact is Linux x86_64 only. Do not claim a full match on macOS.
