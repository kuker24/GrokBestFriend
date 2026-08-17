#!/usr/bin/env python3
"""Evaluate the Impeccable-owned retrieval gate over adversarial prompts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from design_intelligence import integration  # noqa: E402


def main() -> int:
    fixture = ROOT / "tests/fixtures/design-intelligence-integration.jsonl"
    rows = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]
    failures: list[str] = []
    correct = 0
    unnecessary_specialists = 0
    wrong_world_replacements = 0
    unavailable_routes = 0
    full_bank_loads = 0
    for index, row in enumerate(rows, 1):
        result = integration.plan_retrieval(
            intent=row["intent"],
            scope=row["scope"],
            mode=row["mode"],
            authority=row["authority"],
            reference=row.get("reference", "none"),
            task_kind=row.get("task_kind", "static"),
        )
        expected = row["expected"]
        if result["lane"] == expected["lane"] and result["handoff"] == expected.get("handoff"):
            correct += 1
        else:
            failures.append(f"case {index}: {row['prompt']}")
        unnecessary_specialists += int(result["specialists_activated"] != 0)
        wrong_world_replacements += int(
            row["authority"] == "established"
            and row["intent"] != "redesign"
            and row["scope"] != "world"
            and result["lane"] == "system+structure"
        )
        unavailable_routes += int(result["handoff"] not in {None, "found-this-design"})
        full_bank_loads += int(result["packages_loaded_before_selection"] != 0)
        if result["system_limit"] > 5 or result["structure_limit"] > 3:
            failures.append(f"case {index}: shortlist bound")

    total = len(rows)
    accuracy = correct / total if total else 0.0
    print(f"cases={total} correct={correct} accuracy={accuracy:.3f}")
    print(f"unnecessary_specialist={unnecessary_specialists} wrong_visual_world_replace={wrong_world_replacements}")
    print(f"unavailable_route={unavailable_routes} full_bank_context_load={full_bank_loads}")
    if total < 40 or total > 60:
        failures.append(f"case count {total} outside 40..60")
    if accuracy < 0.90:
        failures.append(f"accuracy {accuracy:.3f} below 0.90")
    if unnecessary_specialists > total * 0.10:
        failures.append("unnecessary specialist rate above 10%")
    if wrong_world_replacements or unavailable_routes or full_bank_loads:
        failures.append("zero-tolerance invariant failed")
    if failures:
        print("FAIL " + "; ".join(failures), file=sys.stderr)
        return 1
    print("test-design-intelligence-integration passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
