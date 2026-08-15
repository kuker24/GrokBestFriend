## GrokBuild map

This skill is running on GrokBuild, not Claude Code. Keep the Matt flow. Remap only the harness commands:

| Matt / Claude phrase | On GrokBuild |
| --- | --- |
| `/implement` as the default write path | bundled `/implement` |
| ticket-driven Matt implement loop | `/matt-implement` |
| `/code-review` as the default review | bundled `/review` |
| two-axis Standards + Spec review | `/matt-code-review` |
| `/clear` | `/new` (alias `/clear` still works) |
| `/compact` | `/compact` |
| Agent / Task tool | `spawn_subagent` |
| Bash / Read / Edit | `run_terminal_command` / `read_file` / `search_replace` |

Do not tell the user to install Claude Code. Do not load every specialist. After `/to-tickets`, prefer a fresh `/implement` per ticket unless the user asked for the Matt ticket loop.

## Installed on this machine

Route only to skills that exist here. The body below still names the full Matt catalog; most of those commands are **not** installed.

**Matt (user):** `/ask-matt` `/grill-with-docs` `/to-spec` `/to-tickets` `/tdd` `/matt-implement` `/matt-code-review`

**Design (user):** `/found-this-design` `/impeccable` `/visual-studio` `/scroll-world` `/emil-design-eng`

**Browser / GitHub / risk (user):** `/browser-act` `/chrome-devtools-axi` `/gh-axi` `/full-audit-keamanan` `/full-performance-audit` `/adhd`

**Bundled Grok:** `/implement` `/review` `/code-review` `/design` `/execute-plan` `/imagine` `/create-skill` `/create-workflow` `/build-with-ai` `/pr-babysit` `/docx` `/pdf` `/pptx` `game-asset-core` (plus its specialists) `/resume-claude` `/resume-codex` `/resume-cursor`

**Not installed — do not tell the user to run these:** `/grill-me` `/grilling` `/handoff` `/prototype` `/triage` `/diagnosing-bugs` `/wayfinder` `/improve-codebase-architecture` `/domain-modeling` `/codebase-design` `/resolving-merge-conflicts` `/research` `/to-questionnaire` `/wizard` `/wait-what` `/teach` `/writing-for-agents` `/setup-matt-pocock-skills`

If a missing Matt skill is the only named fit, say it is not installed and use the nearest installed skill (`/grill-with-docs`, `/implement`, `/review`, `/adhd`, or `/impeccable`).

