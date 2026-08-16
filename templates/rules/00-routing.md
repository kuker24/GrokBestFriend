# GrokBuild specialist routing

Use tools lazily. Prefer current repository evidence before external tools. Use one primary specialist per problem. If a risk trigger is active (auth, authorization, secrets, public APIs, payment, upload, webhook, privileged operations), also load at most one verification specialist (`/full-audit-keamanan`). If the concern is a measured performance regression (LCP, INP, CLS, latency, bundle, query, memory), the verification specialist is `/full-performance-audit`. Do not load a second implementation specialist. Availability is not a reason to activate a tool.

```text
pikir dulu → bukti di repo → satu spesialis → cek hasil
```

Do not infer a model provider from a logical model name. Treat custom-gateway aliases as opaque.

## Default path

Follow this tree here. Do not load `/ask-matt` unless the user is choosing a workflow.

1. **Repo evidence is enough** → do the work. No specialist. Verification: FAST or STANDARD.
2. **User typed a slash skill** → load that skill. Do not substitute.
3. **User is choosing a workflow** (`which skill`, `alur apa`, `ask matt`) → load `/ask-matt`.
4. **Architecture / PR-plan DAG** → bundled `/design`. After approval → `/execute-plan`.
5. **Feature still needs a plan** (interview, glossary, ADR) → `/grill-with-docs`. Then `/to-spec` → `/to-tickets` only if the user asked for tickets or the work is multi-session.
6. **Ordinary implementation** → write in this session. Use `/tdd` when test-first. Do **not** auto-start bundled `/implement`.
7. **User asked `/implement` or the Matt ticket loop** → bundled `/implement`, or `/matt-implement` only for a `/to-tickets` ticket.
8. **Review** → bundled `/review`. `/matt-code-review` only if the user asked for two-axis Standards + Spec. `/code-review` only if the user asked for the harsh slash audit.
9. **Verification** → pick a profile from `01-verification.md` by changed surface and risk. Required configured failures block a completion claim.

## Knowledge

- Repository structure and impact: MCP `codebase-memory-mcp` first. Discover tools with `search_tool`, call them with `use_tool`. If Codebase Memory has no project for cwd, skip it and use repo files. Do not retry.
- Exact cross-file symbol work: enable and use MCP `serena` only after Codebase Memory and simpler repo evidence are not enough. Do not run Serena and Codebase Memory as the main brain at the same time.
- Current library or framework docs: MCP `context7` only when repo evidence is insufficient.
- Installable React/shadcn registry items: MCP `shadcn` (pinned CLI). Search, inspect, then install. Context7 stays documentation. Do not treat web search as an installer.
- Broader web research: built-in `web_search` and `web_fetch`. MCP `exa` is registered but disabled until a human completes its OAuth setup (`grok mcp enable exa` after authenticating).
- Hard, high-impact, divergent decisions, fuzzy debugging, API or schema alternatives, trap detection: `/adhd` on demand only. Skip ADHD for typos, ordinary CRUD, or bugs with a known cause.

## UI and browser

- Matching or choosing a visual direction from the local design bank (Refero / Motionsites), including 3–5 recommendations and high-fidelity first-viewport previews: `/found-this-design` first. Then `/impeccable` after a pick.
- Visual UI once a world is chosen or the brief is already visual: `/impeccable` first.
- Installable UI components (form, table, chart, icon, hero, marquee, gantt, animated primitive): MCP `shadcn` only. Load Impeccable `reference/ui-hub.md`. Search → inspect 1–3 candidates → pick one → install. Do not add Magic UI, Kibo, 21st.dev, or community UI MCP servers.
- Decorative components only when they clarify hierarchy, interaction, brand, or data. One authored landing moment. Dashboards may be denser (charts, table, KPI, status) but stay in one system.
- Use the hub only when cwd has `components.json`. React + Tailwind without init: offer `npx shadcn@<pinned> init`, never silent. Never init this GrokBestFriend repo, a backend or Python tree, or a non-UI cwd.
- Before install: inspect registry namespace, dependencies, file targets, and files that already exist. If a candidate would overwrite an existing project file, reject it or require explicit approval. Do not assume third-party items belong in `components/ui`.
- Registry search/discovery may write the registry into `components.json`. Inspect the git diff after discovery and do not accumulate unused registries.
- Scroll-scrub fly-through, diorama, or 3D-world landing: `/scroll-world` (it loads bundled `imagine`). Impeccable owns surrounding chrome when the world sits inside an existing site.
- Website or app UI that also needs designed photos/videos: `/impeccable` owns the surface; load `/visual-studio` for those assets (it loads bundled `imagine`).
- Photoreal product stills, UGC/ad video, cinematic VFX, identity packs, thumbnails with no UI surface: `/visual-studio` only.
- Game sprites, tiles, icon sets, animation sheets: bundled `game-asset-core` and its specialist.
- Motion, transition, or interaction feel: `/emil-design-eng` after Impeccable.
- Exploratory real-user or multi-role QA: `/browser-act`. Load the skill before running any `browser-act` command. Do not invent a raw bash one-liner as a substitute for the skill.
- Observed browser cause (click, form, console, network): `/chrome-devtools-axi` via `npx -y chrome-devtools-axi` after `grok-chromium-cdp start`. Skip it when `curl` or `web_fetch` is enough.
- Browser engine: background Chromium only (`grok-chromium-cdp`). Never Google Chrome, `chrome-direct`, `--headed`, `CHROME_DEVTOOLS_AXI_HEADED=1`, or `CHROME_DEVTOOLS_AXI_AUTO_CONNECT=1` unless the user asks to see a window. Save screenshots to files; do not raise a desktop window.
- Deterministic browser regression: project Playwright only if that project already has it. Do not invent a global Playwright install.

## Risk and GitHub

- Auth, authorization, secrets, public APIs, payment, upload, webhook, privileged operations: `/full-audit-keamanan` plus configured scanners (`semgrep`, `osv-scanner`, `gitleaks`). Do not print secret values.
- Measured regressions in bundle, query, memory, latency, or Core Web Vitals (LCP, INP, CLS): `/full-performance-audit`. FID is legacy. Do not use it as a primary gate.
- GitHub issues, PRs, Actions, releases: `/gh-axi` via `npx -y gh-axi`. If `gh` is not logged in, ask the human to run `gh auth login`.

## Matt flow versus Grok natives

- Planning and tickets stay on Matt skills: `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/tdd`.
- Architecture design doc + PR plan (not Matt grilling): bundled `/design`. After that DAG is approved: `/execute-plan`.
- Ordinary writes stay in this session. Bundled `/implement` is user-explicit, not the default write path. `/matt-implement` is only for a ticket that `/to-tickets` produced and should stay on the Matt ticket loop.
- Default review is bundled `/review`. Two-axis Standards + Spec of a pinned diff: `/matt-code-review`. Harsh maintainability audit: bundled `/code-review` (slash only).
- Choosing a workflow: `/ask-matt`. Route only to skills that exist on this machine. Matt names that are not installed (`/grill-me`, `/handoff`, `/prototype`, `/triage`, `/wayfinder`, `/setup-matt-pocock-skills`, and the other standalone Matt commands) are not available — use the nearest installed skill.

## Docs, media tools, and extras

- Any `image_gen` / `image_edit` / `image_to_video` / `reference_to_video` call: load bundled `imagine` first. Directors stay `/visual-studio`, `/scroll-world`, or `game-asset-*`.
- Word / PDF / PowerPoint files: bundled `/docx`, `/pdf`, `/pptx`.
- Watch or repair an open PR (CI, review comments, conflicts): bundled `/pr-babysit`. Create, list, merge, or search GitHub: `/gh-axi`.
- New skill or workflow: bundled `/create-skill` or `/create-workflow`; load `skill-design-principles` while editing.
- App that calls an LLM: bundled `/build-with-ai`.
- Resume another agent's session: bundled `/resume-claude`, `/resume-codex`, or `/resume-cursor`.

## Plugins and extra MCP

- No Grok plugins are installed. Do not assume Vercel, Figma, Superpowers, official Chrome DevTools, or Claude marketplace plugins exist.
- Do not install a marketplace plugin from a session unless the user asked for that vendor and the current repo uses it. If a plugin is trusted, add it to this section in the same change.
- User MCP: `codebase-memory-mcp`, `context7`, and `shadcn` on; `serena` and `exa` off until a human enables them.
- `tasks` and `voice` are built-in Grok connectors, not user MCP. Use `tasks` only for scheduled automations the user asked for; `voice` only when they ask about TTS voices.
- Local learning events live in `~/.grok/runtime/learning/events.jsonl`. They are evidence for humans. Never auto-edit rules or skills from that log. Promotion path is eval + tests + doctor.

## Do not

- Do not enable every specialist in one turn.
- Do not register 21st.dev, Magic UI MCP, Kibo MCP, or unofficial React Bits / Aceternity MCP.
- Do not run `shadcn init` on GrokBestFriend, backend, or Python repositories.
- Do not install a hub candidate that overwrites an existing project file without explicit approval.
- Do not use Serena before Codebase Memory.
- Do not use ADHD for ordinary work.
- Do not use Emil for static UI, or Impeccable for motion-only work.
- Do not use BrowserAct as a stand-in for project Playwright.
- Do not claim TypeScript, Vitest, coverage, Knip, or Playwright exist unless the current project has them.
- Do not copy or print tokens, gateway URLs, or model-mapping values.
