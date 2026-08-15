# GrokBuild runtime port

This folder snapshots the live GrokBuild system and installs it without Claude Code.

It does not turn on `[compat.claude]`.

## Install

```bash
./install.sh --dry-run
./install.sh
./install.sh --doctor
```

`install-grok-runtime.sh` is a wrapper around `install.sh`.

## What lands where

| Surface | Path |
| --- | --- |
| Routing | `~/.grok/rules/00-routing.md` |
| Verification profiles | `~/.grok/rules/01-verification.md` |
| Skills | `~/.grok/skills/` |
| Hook | `~/.grok/hooks/impeccable.json` |
| Manifest | `~/.grok/runtime/manifest.json` |
| Codebase Memory | `~/.grok/runtime/components/codebase-memory/bin/codebase-memory-mcp` |
| Chromium helper | `~/.grok/bin/grok-chromium-cdp` |
| MCP | `grok mcp` → `~/.grok/config.toml` |

Matt `implement` and `code-review` stay `/matt-implement` and `/matt-code-review` so they do not shadow bundled `/implement` and `/review`.

`[skills].ignore` hides `~/.claude/skills/implement` and `~/.claude/skills/code-review` if those Claude copies exist.

Serena and Exa are registered and then disabled.

```bash
grok mcp enable serena
grok mcp enable exa
```

## Source

Skills are vendored from the live `~/.grok/skills/` tree. Versions of downloadable binaries are in `vendor/sources.json`.

## Secrets

This installer never writes login credentials, tokens, gateway URLs, or model mappings.
