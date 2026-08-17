#!/usr/bin/env python3
"""Intent-aware authority resolver."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence import rank  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    failed: list[str] = []
    taxonomy = policy_mod.load_taxonomy()

    refine = rank.resolve_authority(
        "refine",
        {
            "explicit_scope": "header only",
            "product_truth": "checkout still works",
            "incumbent_design": "existing DESIGN.md",
            "bank": "system:brandco",
            "heuristics": "make it pop",
        },
        taxonomy,
    )
    check(refine["source"] in {"explicit_scope", "product_truth", "incumbent_design"}, "refine keeps incumbent ladder", failed)
    check(refine["preserves_incumbent"], "refine preserves incumbent", failed)
    check(refine["value"] != "make it pop", "heuristics cannot overwrite refine", failed)

    redesign = rank.resolve_authority(
        "redesign",
        {
            "explicit_scope": "replace visual",
            "product_truth": "same prices",
            "pinned_new_direction": "new world",
            "bank": "system:brandco",
        },
        taxonomy,
    )
    check(redesign["preserves_product_truth"], "redesign keeps product truth", failed)
    check(redesign["source"] != "bank" or redesign["rank"] >= 90, "redesign product truth outranks bank", failed)
    check(redesign["value"] in {"replace visual", "same prices", "new world"}, "redesign may replace visual", failed)

    green = rank.resolve_authority(
        "greenfield",
        {
            "explicit_brief": "ops console",
            "product_truth": "no fake metrics",
            "selected_direction": "system:acme",
            "heuristics": "default sauce",
        },
        taxonomy,
    )
    check(green["value"] in {"ops console", "no fake metrics", "system:acme"}, "greenfield uses selected evidence", failed)
    check(green["value"] != "default sauce", "heuristics cannot overwrite greenfield", failed)

    blocked = rank.resolve_authority(
        "greenfield",
        {
            "explicit_brief": "looks like BrandCo",
            "product_truth": "honest copy",
            "brand_pixel_copy": True,
        },
        taxonomy,
    )
    check("brand_pixel_copy" in blocked["blocked"], "pixel copy is blocked", failed)

    if failed:
        print(f"test-design-intelligence-authority failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-authority passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
