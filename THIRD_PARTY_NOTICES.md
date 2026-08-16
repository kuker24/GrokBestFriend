# Third-party notices

This file covers **vendored** components. First-party installer, docs, overlays, and tests are MIT (see `LICENSE`).

Licenses below are taken from vendored frontmatter or an obvious upstream statement. If a skill has no license in tree, this file says so. That is not a grant.

| Component | Upstream | License in this tree | Modified | Redistribution |
| --- | --- | --- | --- | --- |
| `vendor/skills/adhd` | vendored skill frontmatter | MIT | yes (GrokBuild overlay/routing) | follow MIT |
| `vendor/skills/impeccable` | vendored skill frontmatter | Apache-2.0 | yes (GrokBuild overlay/routing) | follow Apache-2.0 |
| Other `vendor/skills/*` | see each `SKILL.md` | **not stated** in vendored frontmatter | yes | unknown — see upstream |
| `vendor/hooks/impeccable.json` | Impeccable hook | Apache-2.0 (with Impeccable) | no | follow Apache-2.0 |
| Design bank (`Design-bank.tgz` Release asset) | Refero + Motionsites catalogs packed by this project | **not cleared** | packed | **unknown**. The installer still downloads the existing v1.0.0 asset. The next public release must verify terms or default to a user-supplied bank. |
| Codebase Memory, serena, browser-act, semgrep, gitleaks, osv-scanner, uv, Grok CLI | see `vendor/sources.json` | their upstream licenses | no (downloaded at install) | follow upstream |

See `vendor/provenance.json` for the machine-readable copy.
