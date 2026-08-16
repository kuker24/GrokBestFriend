#!/usr/bin/env python3
"""Compare a Node version against the shadcn engines pin."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


VERSION_RE = re.compile(r"v?(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = ROOT / "vendor" / "sources.json"


def parse_version(raw: str) -> tuple[int, int, int] | None:
    text = (raw or "").strip()
    if not text:
        return None
    match = VERSION_RE.search(text)
    if not match:
        return None
    return (
        int(match.group("major")),
        int(match.group("minor") or 0),
        int(match.group("patch") or 0),
    )


def parse_minimum(spec: str) -> tuple[int, int, int] | None:
    text = (spec or "").strip()
    if text.startswith(">="):
        text = text[2:].strip()
    return parse_version(text)


def meets_minimum(found: str, minimum: str) -> bool:
    have = parse_version(found)
    need = parse_minimum(minimum)
    if have is None or need is None:
        return False
    return have >= need


def load_shadcn_requirement(sources: Path | None = None) -> tuple[str, str]:
    path = sources or DEFAULT_SOURCES
    data = json.loads(path.read_text(encoding="utf-8"))
    shadcn = (data.get("sources") or {}).get("shadcn") or {}
    pin = str(shadcn.get("version") or "").strip()
    minimum = str((shadcn.get("engines") or {}).get("node") or "").strip()
    if not pin:
        raise ValueError("sources.shadcn.version is missing")
    if not minimum:
        raise ValueError("sources.shadcn.engines.node is missing")
    return pin, minimum


def format_node_version_failure(found: str, pin: str, minimum: str) -> str:
    display = (found or "").strip() or "missing"
    return (
        f"ERROR: FAIL NODE_VERSION\n"
        f"shadcn@{pin} requires Node {minimum}\n"
        f"found: {display}\n"
    )


def check_node(found: str, minimum: str, pin: str) -> int:
    if meets_minimum(found, minimum):
        return 0
    sys.stderr.write(format_node_version_failure(found, pin, minimum))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--found", default="")
    check.add_argument("--sources", default="")
    check.add_argument("--minimum", default="")
    check.add_argument("--pin", default="")
    args = parser.parse_args()

    pin = args.pin
    minimum = args.minimum
    if args.sources or not (pin and minimum):
        try:
            loaded_pin, loaded_min = load_shadcn_requirement(Path(args.sources) if args.sources else None)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"ERROR: FAIL NODE_VERSION {exc}", file=sys.stderr)
            return 1
        pin = pin or loaded_pin
        minimum = minimum or loaded_min
    return check_node(args.found, minimum, pin)


if __name__ == "__main__":
    raise SystemExit(main())
