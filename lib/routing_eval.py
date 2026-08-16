#!/usr/bin/env python3
"""Deterministic encoder of templates/rules/00-routing.md.

This is a policy eval, not a live-Grok judge. CI runs it against
tests/fixtures/routing-cases.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SLASH_SKILLS = (
    "ask-matt",
    "grill-with-docs",
    "to-spec",
    "to-tickets",
    "tdd",
    "implement",
    "matt-implement",
    "review",
    "matt-code-review",
    "code-review",
    "design",
    "execute-plan",
    "impeccable",
    "found-this-design",
    "visual-studio",
    "scroll-world",
    "emil-design-eng",
    "browser-act",
    "chrome-devtools-axi",
    "gh-axi",
    "full-audit-keamanan",
    "full-performance-audit",
    "adhd",
    "create-skill",
    "create-workflow",
    "build-with-ai",
    "pr-babysit",
    "imagine",
    "docx",
    "pdf",
    "pptx",
)

SLASH_RE = re.compile(r"/(found_this_design|" + "|".join(re.escape(name) for name in SLASH_SKILLS) + r")\b")

WORKFLOW_RE = re.compile(
    r"\b(which skill|which flow|which workflow|alur apa|skill mana|ask matt|pilih skill|alur mana)\b",
    re.IGNORECASE,
)

DESIGN_RE = re.compile(
    r"\b(arsitektur|architecture|system design|design doc|technical architecture|"
    r"pr[- ]plan|pr plan dag|arsitektur sistem)\b",
    re.IGNORECASE,
)

GRILL_RE = re.compile(
    r"\b(belum tahu requirement|belum tau requirement|requirements? unclear|"
    r"saya belum tahu|interview (dulu|user|the (plan|feature))|"
    r"tulis glossary|write (a |the )?glossary|adr\b|sharpen (the )?plan|"
    r"grill|butuh wawancara|need an interview|feature still needs a plan)\b",
    re.IGNORECASE,
)

SPEC_RE = re.compile(
    r"\b(tulis spec|write (a |the )?spec|to-spec|jadiin spec|jadikan spec|"
    r"synthesize (a |the )?spec)\b",
    re.IGNORECASE,
)

TICKET_RE = re.compile(
    r"\b(pecah jadi tiket|break( it)? into tickets|to-tickets|jadi tiket|"
    r"tracer[- ]bullet tickets|buat tiket)\b",
    re.IGNORECASE,
)

TDD_RE = re.compile(r"\b(tdd|test-first|red-green-refactor|red green refactor)\b", re.IGNORECASE)

REVIEW_RE = re.compile(
    r"\b(code review|review (this|my|the) (pr|diff|changes|code)?|review (pr|diff|changes))\b",
    re.IGNORECASE,
)
MATT_REVIEW_RE = re.compile(r"\b(two-axis|standards \+ spec|matt-code-review)\b", re.IGNORECASE)
HARSH_REVIEW_RE = re.compile(r"\b(harsh (slash )?audit|code-review skill)\b", re.IGNORECASE)

IMPLEMENT_RE = re.compile(
    r"\b(run (/)?implement|start (/)?implement|matt ticket loop|matt-implement)\b",
    re.IGNORECASE,
)

AUDIT_PRIMARY_RE = re.compile(
    r"\b(audit (authorization|auth|keamanan|security|oauth|payment|upload|webhook)|"
    r"security audit|full-audit|audit keamanan)\b",
    re.IGNORECASE,
)

PERF_PRIMARY_RE = re.compile(
    r"\b((measured )?(lcp|inp|cls)( regression)?|full-performance-audit|"
    r"performance audit|ukur (lcp|latency|bundle)|bundle size regression)\b",
    re.IGNORECASE,
)

FOUND_DESIGN_RE = re.compile(
    r"\b(cari desain|rekomendasi desain|design bank|refero|motionsites|"
    r"which visual|preview desain|found-this-design|pilih arah visual)\b",
    re.IGNORECASE,
)

IMPECCABLE_RE = re.compile(
    r"\b(padding|button style|polish (the )?(ui|page|button)|redesign|"
    r"visual hierarchy|landing page ui|percantik| rapikan ui|ubah (warna|spacing|padding))\b",
    re.IGNORECASE,
)

EMIL_RE = re.compile(r"\b(motion|easing|hover feel|transition feel|interaction feel|micro-?interaction)\b", re.IGNORECASE)

VISUAL_STUDIO_RE = re.compile(
    r"\b(product (photo|still)|thumbnail|ugc video|cinematic vfx|studio shot|youtube thumbnail)\b",
    re.IGNORECASE,
)

SCROLL_RE = re.compile(r"\b(scroll-?scrub|diorama|3d world landing|scroll world|isometric world)\b", re.IGNORECASE)

BROWSER_ACT_RE = re.compile(r"\b(exploratory qa|multi-role (qa|browser)|browser-act)\b", re.IGNORECASE)

CHROME_DEVTOOLS_RE = re.compile(
    r"\b(console error|network tab|observed (click|browser) (bug|issue)|chrome-devtools)\b",
    re.IGNORECASE,
)

GH_RE = re.compile(r"\b(github (issue|pr|actions|release)|buat issue|create (a )?pr|gh-axi)\b", re.IGNORECASE)

ADHD_RE = re.compile(
    r"\b(brainstorm alternatives|trap detection|fuzzy (debug|architecture)|"
    r"divergent (options|design)|adhd mode|open-ended design forks)\b",
    re.IGNORECASE,
)

SIMPLE_WORK_RE = re.compile(
    r"\b(sederhana|simple|typo|fix bug|bug api|crud|tambah tombol|add button|"
    r"rename|whitespace|padding button)\b",
    re.IGNORECASE,
)

RISK_VERIFY_RE = re.compile(
    r"\b(oauth|jwt|authorization|rbac|payment|stripe|webhook|upload|"
    r"privileged|public api|secrets?)\b",
    re.IGNORECASE,
)

PERF_VERIFY_RE = re.compile(
    r"\b(lcp|inp|cls|measured (latency|regression)|bundle size|query regression)\b",
    re.IGNORECASE,
)

NEGATE_RE = re.compile(r"\b(jangan|don't|do not|bukan|skip|tanpa)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Route:
    primary: str
    verify: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"primary": self.primary, "verify": self.verify}


def _negated(prompt: str, needle: str) -> bool:
    for match in re.finditer(re.escape(needle), prompt, re.IGNORECASE):
        window = prompt[max(0, match.start() - 24) : match.start()]
        if NEGATE_RE.search(window):
            return True
    return False


def _has_unnegated(prompt: str, regex: re.Pattern[str]) -> bool:
    for match in regex.finditer(prompt):
        if not _negated(prompt, match.group(0)):
            return True
    return False


def _first_slash(prompt: str) -> str | None:
    for match in SLASH_RE.finditer(prompt):
        name = match.group(1).replace("_", "-")
        if name == "found-this-design" or name == "found_this_design":
            name = "found-this-design"
        if _negated(prompt, match.group(0)):
            continue
        return name
    return None


def route(prompt: str) -> Route:
    text = " ".join(prompt.strip().split())
    if not text:
        return Route("none")

    slash = _first_slash(text)
    if slash:
        return _with_verify(slash, text)

    if WORKFLOW_RE.search(text) and not _negated(text, "ask matt"):
        return Route("ask-matt")

    if ADHD_RE.search(text) and not _negated(text, "adhd"):
        return Route("adhd")

    if _has_unnegated(text, AUDIT_PRIMARY_RE):
        return Route("full-audit-keamanan")
    if _has_unnegated(text, PERF_PRIMARY_RE):
        return Route("full-performance-audit")

    if DESIGN_RE.search(text):
        return _with_verify("design", text)

    if SPEC_RE.search(text):
        return Route("to-spec")
    if TICKET_RE.search(text):
        return Route("to-tickets")

    if MATT_REVIEW_RE.search(text):
        return Route("matt-code-review")
    if HARSH_REVIEW_RE.search(text):
        return Route("code-review")
    if REVIEW_RE.search(text):
        return Route("review")

    if IMPLEMENT_RE.search(text):
        primary = "matt-implement" if "matt-implement" in text.lower() or "matt ticket" in text.lower() else "implement"
        return _with_verify(primary, text)

    if TDD_RE.search(text) and not SIMPLE_WORK_RE.search(text):
        return _with_verify("tdd", text)
    if TDD_RE.search(text):
        return _with_verify("tdd", text)

    if GRILL_RE.search(text):
        return Route("grill-with-docs")

    if FOUND_DESIGN_RE.search(text):
        return Route("found-this-design")
    if SCROLL_RE.search(text):
        return Route("scroll-world")
    if VISUAL_STUDIO_RE.search(text):
        return Route("visual-studio")
    if EMIL_RE.search(text):
        return Route("emil-design-eng")
    if IMPECCABLE_RE.search(text):
        return Route("impeccable")

    if BROWSER_ACT_RE.search(text):
        return Route("browser-act")
    if CHROME_DEVTOOLS_RE.search(text):
        return Route("chrome-devtools-axi")
    if GH_RE.search(text):
        return Route("gh-axi")

    return _with_verify("none", text)


def _with_verify(primary: str, prompt: str) -> Route:
    if primary in {"full-audit-keamanan", "full-performance-audit"}:
        return Route(primary)
    if primary in {"ask-matt", "review", "matt-code-review", "code-review", "impeccable", "found-this-design", "emil-design-eng", "visual-studio", "scroll-world", "browser-act", "chrome-devtools-axi", "gh-axi", "adhd"}:
        return Route(primary)
    if _has_unnegated(prompt, PERF_VERIFY_RE) and primary in {"none", "implement", "tdd", "design"}:
        return Route(primary, "full-performance-audit")
    if _has_unnegated(prompt, RISK_VERIFY_RE) and primary in {
        "none",
        "implement",
        "matt-implement",
        "tdd",
        "design",
        "grill-with-docs",
    }:
        return Route(primary, "full-audit-keamanan")
    return Route(primary)


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
        item["_line"] = line_no
        cases.append(item)
    return cases


def evaluate_case(case: dict[str, Any]) -> list[str]:
    got = route(case["prompt"])
    errors: list[str] = []
    expect = case.get("expect", "none")
    if got.primary != expect:
        errors.append(f"primary expected {expect}, got {got.primary}")
    expect_verify = case.get("verify")
    if expect_verify != got.verify:
        errors.append(f"verify expected {expect_verify}, got {got.verify}")
    for name in case.get("forbid") or []:
        if got.primary == name or got.verify == name:
            errors.append(f"forbidden skill fired: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?")
    args = parser.parse_args()
    if not args.prompt:
        print(json.dumps(Route("none").as_dict()))
        return 0
    print(json.dumps(route(args.prompt).as_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
