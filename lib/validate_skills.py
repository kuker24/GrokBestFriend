#!/usr/bin/env python3
"""Static skill + routing checks used by doctor and staged install."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ("ask-matt", "grill-with-docs", "to-spec", "to-tickets")


def check_tree(skills: Path, routing: Path) -> list[str]:
    errors: list[str] = []

    def error(msg: str) -> None:
        errors.append(msg)

    def ok(msg: str) -> None:
        print("OK  " + msg)

    routing_text = routing.read_text(encoding="utf-8")

    for name in DEFAULT_PATH:
        path = skills / name / "SKILL.md"
        if not path.is_file():
            error(f"missing skill {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"^disable-model-invocation:\s*true\s*$", text, re.MULTILINE):
            error(f"{name} still has disable-model-invocation")
        else:
            ok(f"{name} is model-invocable")

    grill_path = skills / "grill-with-docs" / "SKILL.md"
    if grill_path.is_file():
        grill = grill_path.read_text(encoding="utf-8")
        if re.search(r"`?/grilling`?|`?/domain-modeling`?", grill):
            error("grill-with-docs still names missing Matt interview primitives")
        else:
            ok("grill-with-docs has no missing-primitive stub")

    ask_path = skills / "ask-matt" / "SKILL.md"
    if ask_path.is_file():
        ask = ask_path.read_text(encoding="utf-8")
        maps = len(re.findall(r"^## GrokBuild map\s*$", ask, re.MULTILINE))
        if maps > 1:
            error(f"ask-matt has {maps} GrokBuild map sections")
        else:
            ok("ask-matt has at most one GrokBuild map")

    for name in ("to-spec", "to-tickets"):
        path = skills / name / "SKILL.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "/setup-matt-pocock-skills" in text:
            error(f"{name} still names the missing tracker-setup command")
        else:
            ok(f"{name} uses the local tracker default")

    spec_path = skills / "to-spec" / "SKILL.md"
    if spec_path.is_file():
        spec = spec_path.read_text(encoding="utf-8")
        if "Check with the user that these seams" in spec:
            error("to-spec still interviews the user about test seams")
        elif "extremely extensive" in spec or "A LONG, numbered list" in spec:
            error("to-spec still asks for an extensive user-story dump")
        else:
            ok("to-spec is non-interactive and minimum-sufficient")

    tickets_path = skills / "to-tickets" / "SKILL.md"
    if tickets_path.is_file():
        tickets = tickets_path.read_text(encoding="utf-8")
        needed = (
            "verification profile",
            "risk level",
            "definition of done",
            "rollback",
        )
        missing = [item for item in needed if item not in tickets.lower() and item not in tickets]
        # case-insensitive
        lowered = tickets.lower()
        missing = [item for item in needed if item not in lowered]
        if missing:
            error("to-tickets missing agent-ready fields: " + ", ".join(missing))
        else:
            ok("to-tickets carries agent-ready fields")

    if "If Codebase Memory has no project for cwd" not in routing_text:
        error("00-routing.md missing unindexed-cwd skip rule")
    else:
        ok("00-routing.md skips unindexed Codebase Memory")

    if "Do **not** auto-start bundled `/implement`" not in routing_text:
        error("00-routing.md missing no-auto-implement rule")
    else:
        ok("00-routing.md does not auto-start /implement")

    if "at most one verification specialist" not in routing_text:
        error("00-routing.md missing verification-specialist composition rule")
    else:
        ok("00-routing.md allows one verification specialist")

    if "Never auto-edit rules or skills from that log" not in routing_text:
        error("00-routing.md missing learning-log no-auto-edit rule")
    else:
        ok("00-routing.md does not auto-edit from the learning log")

    if "Design Intelligence is an internal, lazy retrieval stage" not in routing_text:
        error("00-routing.md missing Impeccable-owned Design Intelligence boundary")
    elif "never a primary route or specialist" not in routing_text:
        error("00-routing.md promotes Design Intelligence to a route")
    else:
        ok("00-routing.md keeps Design Intelligence inside Impeccable")

    di_path = skills / "impeccable" / "reference" / "design-intelligence.md"
    if not di_path.is_file():
        error("impeccable missing design-intelligence reference")
    else:
        di = di_path.read_text(encoding="utf-8")
        required = (
            "packages_loaded_during_search=0",
            "at most one primary system and one secondary influence",
            "not DESIGN.md",
            "no substitute specialist",
        )
        missing = [value for value in required if value not in di]
        if missing:
            error("impeccable design-intelligence boundary incomplete: " + ", ".join(missing))
        else:
            ok("impeccable Design Intelligence reference is bounded")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills", required=True)
    parser.add_argument("--routing", required=True)
    args = parser.parse_args()
    errors = check_tree(Path(args.skills), Path(args.routing))
    for msg in errors:
        print("ERROR: FAIL " + msg, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
