#!/usr/bin/env python3
"""Static classification contracts."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import catalog  # noqa: E402
from design_intelligence_support import seed_bank  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    failed: list[str] = []
    os.environ["HOME"] = tempfile.mkdtemp()
    with tempfile.TemporaryDirectory() as tmp:
        items = {item["id"]: item for item in catalog.load_items(seed_bank(Path(tmp) / "bank"))}

        community = items["recipe:community-evil"]
        check(community["execution_class"] == "quarantined", "community → quarantined", failed)
        check(community["search_policy"] == "never", "community search never", failed)
        desc = community["description"]
        check("npx skills add" not in desc.lower(), "install command not stored", failed)
        check("ignore previous" not in desc.lower(), "instruction tell not stored", failed)

        stub = items["specialist:creative-director"]
        check(stub["execution_class"] == "stub", "catalogue stub → stub", failed)

        brand = items["specialist:brand-extract"]
        check(brand["execution_class"] == "connector-required", "brand-extract connector-required", failed)
        check("od" in brand["capabilities_required"] or "agent-browser" in brand["capabilities_required"],
              "brand-extract records connectors", failed)
        check("execution_status" not in brand, "missing connector is not stored", failed)

        system = items["system:brandco"]
        check(system["evidence_tier"] == "E1", "curated brand → E1", failed)
        check(system["style_authority"] == "inspiration-only", "curated brand inspiration-only", failed)
        check(system["license"]["status"] == "unknown", "system license unknown", failed)
        check(system["license"]["redistribution"] == "local-only", "unknown license local-only", failed)
        check(system["license"]["redistribution"] != "allowed", "unknown license never allowed", failed)

        tom = items["system:tomlike"]
        check(tom["evidence_tier"] == "E1", "url origin still E1", failed)
        check(tom["style_authority"] == "inspiration-only", "url origin still inspiration-only", failed)
        check(tom["source"]["url"] == "https://github.com/example/tomlike", "url recorded", failed)

        emil = items["specialist:emil-design-eng"]
        check(emil["execution_class"] == "reference-only", "ZIP emil reference-only", failed)
        check(emil.get("duplicate_of") is None, "emil duplicate_of is null", failed)

        review = items["specialist:review-animations"]
        check("DISABLE_MODEL_INVOCATION" in review["warnings"], "review-animations warning", failed)

        taste = items["specialist:design-taste-frontend"]
        check(taste["execution_class"] == "reference-only", "design-taste-frontend reference-only", failed)

        licensed = items["structure:licensed"]
        check(licensed["license"]["status"] == "known", "owned MIT is known", failed)
        check(licensed["license"]["spdx"] == "MIT", "owned MIT SPDX", failed)

        hostile = items["specialist:hostile"]
        blob = json_blob(hostile)
        check("XAI_API_KEY=" not in blob, "secret redacted in catalog", failed)
        check("Bearer 0123456789" not in blob, "bearer redacted in catalog", failed)
        check("UNTRUSTED_INSTRUCTION_TEXT" in hostile["warnings"] or "CATALOGUE_INSTALL_POINTER" in hostile["warnings"],
              "hostile warnings recorded", failed)

    if failed:
        print(f"test-design-intelligence-classify failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-classify passed")
    return 0


def json_blob(item: dict) -> str:
    import json

    return json.dumps(item)


if __name__ == "__main__":
    raise SystemExit(main())
