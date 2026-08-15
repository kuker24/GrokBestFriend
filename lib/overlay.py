#!/usr/bin/env python3
"""Apply Grok-native overlays to copied skill trees."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def upsert_frontmatter(text: str, updates: dict[str, str]) -> str:
    match = FRONTMATTER_RE.match(text)
    if not match:
        lines = ["---"]
        for key, value in updates.items():
            lines.append(f"{key}: {value}")
        lines.extend(["---", "", text])
        return "\n".join(lines)

    body = text[match.end() :]
    fm = match.group(1)
    for key, value in updates.items():
        rendered = json.dumps(value) if any(ch in value for ch in ":#{}[]&*?|>!%@`") or " " in value else value
        pattern = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
        line = f"{key}: {rendered}"
        if pattern.search(fm):
            fm = pattern.sub(line, fm, count=1)
        else:
            fm = fm.rstrip() + f"\n{line}\n"
    return f"---\n{fm}\n---\n{body}"


def prepend_after_frontmatter(text: str, extra: str) -> str:
    if extra in text:
        return text
    match = FRONTMATTER_RE.match(text)
    if not match:
        return extra + text
    head = text[: match.end()]
    body = text[match.end() :]
    return head + extra + body


def replace_all(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def apply_skill(dest: Path, name: str, prepend: str | None) -> None:
    skill = dest / "SKILL.md"
    text = skill.read_text(encoding="utf-8")

    updates: dict[str, str] = {"name": name}
    extras: list[tuple[str, str]] = []

    if name == "matt-implement":
        extras = [
            ("use /code-review", "use /matt-code-review"),
            (
                "Use /tdd where possible, at pre-agreed seams.",
                "Use /tdd where possible, at pre-agreed seams. Default Grok write path is bundled /implement; this skill is the Matt ticket loop only.",
            ),
        ]
    elif name == "tdd":
        extras = [
            ("see the `code-review` skill", "see bundled `/review`, or `/matt-code-review` for the two-axis Matt review"),
        ]
    elif name == "browser-act":
        extras = [
            ("allowed-tools: Bash(browser-act:*)", "allowed-tools: run_terminal_command"),
            ("NEVER run browser-act commands directly via Bash", "NEVER run browser-act commands until this skill is loaded. Use run_terminal_command, not a raw unguided bash one-liner"),
        ]
    elif name == "adhd":
        updates["when-to-use"] = (
            "Use only for difficult divergent decisions, fuzzy debugging, API/schema alternatives, or trap detection. Skip ordinary CRUD, typos, and bugs with a known cause."
        )
        extras = [
            ("Spawn 5 **parallel** Agent/Task tool calls", "Spawn 5 **parallel** `spawn_subagent` calls"),
            ("The Agent/Task tool gives each branch a fresh context.", "Grok `spawn_subagent` gives each branch a fresh context."),
            ("inside Claude with no install required.", "inside GrokBuild with no extra install required."),
        ]
    elif name == "emil-design-eng":
        updates["description"] = (
            "UI motion, transition, and interaction feel after Impeccable. Use when polishing animation, easing, press/hover, or interruptible chrome motion. Do not use for static UI, photoreal video, or scroll-world camera chains."
        )
        updates["when-to-use"] = (
            "Use only for motion, transition, or interaction work after Impeccable. Do not use for static UI or backend-only work."
        )
    elif name == "full-audit-keamanan":
        updates["when-to-use"] = (
            "Use on demand for auth, secrets, APIs, payment, upload, webhook, or privileged-operation risk. Do not use for ordinary product UI."
        )
    elif name == "full-performance-audit":
        updates["when-to-use"] = (
            "Use on demand for measured regressions in bundle, query, memory, latency, or Core Web Vitals (LCP, INP, CLS)."
        )
    elif name == "chrome-devtools-axi":
        updates["description"] = (
            "Control a Chromium session through chrome-devtools-axi after grok-chromium-cdp start. Use when an observed browser issue needs diagnostics (click, form, console, network). Skip if curl or web_fetch is enough. Not for exploratory multi-role QA (use browser-act)."
        )
        updates["when-to-use"] = (
            "Use when an observed browser issue needs Chromium diagnostics. Start grok-chromium-cdp first and attach via CHROME_DEVTOOLS_AXI_BROWSER_URL. Skip if curl or web_fetch is enough."
        )
        extras = [
            (
                "Agent ergonomic interface for controlling Chrome browser session. Prefer this over other browser automation tools.",
                "Agent ergonomic interface for diagnosing a Chromium session after `grok-chromium-cdp start`. Prefer `/browser-act` for exploratory multi-role QA.",
            ),
            (
                "Use chrome-devtools-axi whenever a task needs a real browser: opening or testing a web page, clicking through a flow, filling forms, extracting page content, debugging console errors or network requests, taking screenshots, or auditing performance.",
                "Use chrome-devtools-axi after an observed browser issue needs diagnostics: click, form, console, or network. Start `grok-chromium-cdp` first and attach with `CHROME_DEVTOOLS_AXI_BROWSER_URL`.",
            ),
            (
                "Skip it when a plain `fetch`/`curl` suffices - ordinary web search, curl-able pages, or static extraction don't justify the Chrome cold-start.",
                "Skip it when a plain `fetch`/`curl` or `web_fetch` suffices. Do not use it for exploratory multi-role QA (`/browser-act`) and do not fall back to Google Chrome.",
            ),
        ]
    elif name == "matt-code-review":
        updates["description"] = (
            "Two-axis Standards + Spec review of a pinned diff. Use only when the user asks for that two-axis review, or runs /matt-code-review. Default review is bundled /review."
        )
    elif name == "gh-axi":
        updates["when-to-use"] = (
            "Use for GitHub issues, PRs, Actions, and releases via npx -y gh-axi. Ask the human to run gh auth login if gh is not authenticated."
        )
    elif name == "found-this-design":
        extras = []

    text = upsert_frontmatter(text, updates)
    if prepend:
        text = prepend_after_frontmatter(text, prepend)
    if extras:
        text = replace_all(text, extras)
    skill.write_text(text, encoding="utf-8")

    if name == "found-this-design":
        lib = dest / "scripts" / "lib.mjs"
        if lib.exists():
            body = lib.read_text(encoding="utf-8")
            if "/home/" in body or "DEFAULT_BANK =" in body:
                marker = "export const REFERO_KINDS"
                rest = body.split(marker, 1)[1] if marker in body else None
                header = (
                    'import fs from "node:fs";\n'
                    'import os from "node:os";\n'
                    'import path from "node:path";\n\n'
                    "export const DEFAULT_BANK =\n"
                    '  process.env.GROK_DESIGN_BANK || path.join(os.homedir(), "Design");\n\n'
                )
                if rest is not None:
                    lib.write_text(header + marker + rest, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--prepend", default="")
    args = parser.parse_args()
    prepend = Path(args.prepend).read_text(encoding="utf-8") if args.prepend else None
    apply_skill(Path(args.dest), args.name, prepend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
