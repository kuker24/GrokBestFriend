#!/usr/bin/env python3
"""Summarize local learning events. Never prints prompt text."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def default_path() -> Path:
    return Path.home() / ".grok" / "runtime" / "learning" / "events.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="")
    args = parser.parse_args()
    path = Path(args.file) if args.file else default_path()
    if not path.is_file():
        print(f"no learning log at {path}")
        return 0

    primary = Counter()
    verify = Counter()
    corrections = Counter()
    failed = 0
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        total += 1
        primary[event.get("primary") or "none"] += 1
        if event.get("verify"):
            verify[event["verify"]] += 1
        if event.get("user_correction"):
            corrections[str(event["user_correction"])] += 1
        if event.get("passed") is False:
            failed += 1

    print(f"events {total}")
    print(f"failed {failed}")
    print("primary:")
    for name, count in primary.most_common():
        print(f"  {count:4d}  {name}")
    if verify:
        print("verify:")
        for name, count in verify.most_common():
            print(f"  {count:4d}  {name}")
    if corrections:
        print("user_correction:")
        for name, count in corrections.most_common():
            print(f"  {count:4d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
