# Live inventory (2026-08-16)

Product identity: **GrokBestFriend 1.2.0**. Captured from the source Linux host. See `vendor/inventory.json` for the machine-readable copy. Install preserves foreign skills/rules/hooks, journals a crash-safe transaction, and enforces `vendor/runtime-policy.json` (`yolo=false`, `permission_mode=ask`, compat off). v1.2.0 adds the pinned shadcn MCP as the UI registry hub.

Planning skills `ask-matt` `grill-with-docs` `to-spec` `to-tickets` are model-invocable. Bundled `/implement` stays slash-only. Routing allows one primary specialist plus at most one verification specialist when a risk or measured-performance trigger is on.

## Grok

- Version seen: 1.0.4
- Compat Claude / Cursor: all off
- Marketplace: xAI Official (`https://github.com/xai-org/plugin-marketplace.git`)
- Plugins installed: none

## User skills

`adhd` `ask-matt` `browser-act` `chrome-devtools-axi` `emil-design-eng` `found-this-design` `full-audit-keamanan` `full-performance-audit` `gh-axi` `grill-with-docs` `impeccable` `matt-code-review` `matt-implement` `scroll-world` `tdd` `to-spec` `to-tickets` `visual-studio`

## Rules and hook

- `00-routing.md`
- `01-verification.md`
- `hooks/impeccable.json`

## MCP

| Name | Enabled | Transport |
| --- | --- | --- |
| codebase-memory-mcp | yes | stdio, portable binary v0.9.0 |
| context7 | yes | HTTP `https://mcp.context7.com/mcp` |
| shadcn | yes | stdio, `npx -y shadcn@4.18.0 mcp` |
| exa | no | HTTP `https://mcp.exa.ai/mcp` |
| serena | no | stdio, `serena-agent` 1.6.1, context `agent` |

## Tools

| Tool | Version / note |
| --- | --- |
| serena-agent | 1.6.1 (uv, Python 3.13) |
| browser-act-cli | 1.3.0 (uv, Python 3.12) |
| semgrep | 1.171.0 |
| osv-scanner | 2.4.0 |
| gitleaks | 8.30.1 |
| gh | required, login is human |
| Node.js | `>=20.18.1` plus `npx` (shadcn 4.18.0 engines) |
| Chromium | required; Google Chrome is refused |

## Not in this repo

Sessions, logs, marketplace cache, trusted folders, login files, Claude Code. The design bank archive is a GitHub Release asset, not a git blob.
