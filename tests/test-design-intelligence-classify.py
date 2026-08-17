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
from design_intelligence import classify  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence import text as text_mod  # noqa: E402
from design_intelligence_support import seed_bank  # noqa: E402

CANARIES = (
    "canary-from-manifest-do-not-keep",
    "canary-from-design-do-not-keep",
    "canary-from-template-do-not-keep",
    "canary-from-frontmatter-do-not-keep",
    "canary-from-opendesign-do-not-keep",
    "sk-test-should-not-persist-in-catalog",
    "super-secret",
)


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

        decoy = items["structure:decoy-apache"]
        check(decoy["license"]["status"] != "known", "decoy Apache is not known", failed)
        check(decoy["license"]["redistribution"] != "allowed", "decoy Apache never allowed", failed)

        conflicted = items["system:conflicted"]
        check(conflicted["license"]["status"] == "conflicting", "declared vs file conflict", failed)
        check(conflicted["license"]["redistribution"] == "blocked", "conflict is blocked", failed)

        policy = policy_mod.load_policy()
        decoy_text = (
            "This work is not distributed under the Apache License, Version 2.0.\n"
            "See http://www.apache.org/licenses/LICENSE-2.0\n"
        )
        decoy_hit = classify.detect_license(decoy_text, None, policy, item_owned=True)
        check(decoy_hit["status"] != "known", "unit decoy is not known", failed)
        check(decoy_hit["redistribution"] != "allowed", "unit decoy not allowed", failed)

        apache_text = (
            "Apache License\nVersion 2.0, January 2004\n"
            "http://www.apache.org/licenses/LICENSE-2.0\n\n"
            "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION\n"
            'Licensed under the Apache License, Version 2.0 (the "License");\n'
        )
        apache_hit = classify.detect_license(apache_text, None, policy, item_owned=True)
        check(apache_hit == {"spdx": "Apache-2.0", "status": "known", "redistribution": "allowed"},
              "canonical Apache is known", failed)

        redacted = text_mod.redact_secrets("prefix XAI_API_" "KEY=super-secret suffix", policy)
        check("super-secret" not in redacted, "secret value redacted", failed)
        check("[REDACTED]" in redacted, "redaction marker present", failed)
        check("XAI_API_" "KEY=" not in redacted, "secret assignment not stored", failed)

        hostile = items["specialist:hostile"]
        blob = json_blob(hostile)
        check("XAI_API_KEY=" not in blob, "secret redacted in catalog", failed)
        check("Bearer 0123456789" not in blob, "bearer redacted in catalog", failed)
        check("sk-test-should-not-persist-in-catalog" not in blob, "hostile secret value gone", failed)
        check("UNTRUSTED_INSTRUCTION_TEXT" in hostile["warnings"] or "CATALOGUE_INSTALL_POINTER" in hostile["warnings"],
              "hostile warnings recorded", failed)

        catalog_blob = "\n".join(json_blob(item) for item in items.values())
        for canary in CANARIES:
            check(canary not in catalog_blob, f"canary absent:{canary}", failed)
        brand = items["system:brandco"]
        dash = items["structure:dashboard"]
        taste = items["specialist:design-taste-frontend"]
        check(brand["description"], "brand description still present", failed)
        check("marketplace" in brand["description"].lower(), "brand searchable after redact", failed)
        check(any("sidebar" in str(region).lower() for region in (dash.get("summary") or {}).get("required_data_regions") or []),
              "template regions kept after redact", failed)
        check("anti-slop" in taste["description"].lower(), "frontmatter description kept after redact", failed)

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
