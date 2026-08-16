#!/usr/bin/env python3
"""Policy eval for 00-routing.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from routing_eval import evaluate_case, load_cases  # noqa: E402

CASES = ROOT / "tests/fixtures/routing-cases.jsonl"
MIN_CASES = 80


def main() -> int:
    cases = load_cases(CASES)
    if len(cases) < MIN_CASES:
        print(f"FAIL need at least {MIN_CASES} routing cases, have {len(cases)}", file=sys.stderr)
        return 1
    failed = 0
    for case in cases:
        errors = evaluate_case(case)
        if errors:
            failed += 1
            print(f"FAIL {case['id']}: {'; '.join(errors)}", file=sys.stderr)
            print(f"     prompt: {case['prompt']}", file=sys.stderr)
        else:
            print(f"OK  {case['id']}")
    if failed:
        print(f"test-routing-eval failed: {failed}/{len(cases)}", file=sys.stderr)
        return 1
    print(f"test-routing-eval passed ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
