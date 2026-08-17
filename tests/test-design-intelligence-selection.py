#!/usr/bin/env python3
"""PR B retrieval boundaries and user-locked selection artifact."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import catalog  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence import selection  # noqa: E402
from design_intelligence_support import seed_bank  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    failed: list[str] = []
    policy = policy_mod.load_policy()
    schema = json.loads((ROOT / "vendor/design-intelligence/schemas/selection.schema.json").read_text(encoding="utf-8"))
    check(schema.get("additionalProperties") is False, "selection schema is fail-closed", failed)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bank = seed_bank(root / "bank")

        result = selection.shortlist(
            bank,
            query="acme dashboard sidebar kpi",
            intent="greenfield",
            mode="Operate",
            policy=policy,
        )
        check(result["status"] == "DEGRADED", "known limitations remain visible", failed)
        check(result["packages_loaded_during_search"] == 0, "shortlist opens no packages", failed)
        check(len(result["systems"]) <= 5 and len(result["structures"]) <= 3, "shortlists are bounded", failed)
        check(any(row["id"] == "system:acme" for row in result["systems"]), "system metadata found", failed)
        check(all(row["normalization_status"] == "complete" for row in result["systems"]),
              "only selectable complete systems are shortlisted", failed)
        check(any(row["id"] == "structure:dashboard" for row in result["structures"]), "normalized structure found", failed)

        structure_only = selection.shortlist(
            bank,
            query="dashboard sidebar kpi",
            intent="refine",
            mode="Operate",
            policy=policy,
            structure_only=True,
        )
        check(structure_only["systems"] == [], "established world does not search systems", failed)
        check(structure_only["limits"]["systems"] == 0, "structure-only limit is explicit", failed)

        missing = selection.shortlist(
            root / "missing",
            query="dashboard",
            intent="greenfield",
            mode="Operate",
            policy=policy,
        )
        check(missing["status"] == "DEGRADED" and not missing["systems"], "missing bank falls back once", failed)

        inspected = selection.inspect_system(bank, "system:acme", policy)
        check(inspected["verified_content_hash"] is True, "selected package content is verified", failed)
        check(inspected["package_files_loaded"] == 3, "selected system loads exactly three files", failed)
        check(inspected["tokens"].get("--color-primary") == "#0F766E", "safe token subset extracted", failed)
        try:
            selection.inspect_system(bank, "structure:dashboard", policy)
        except selection.SelectionError:
            check(True, "structure package cannot be opened", failed)
        else:
            check(False, "structure package cannot be opened", failed)

        try:
            selection.pin_selection(
                root / "project",
                bank,
                target="app/dashboard",
                query="acme dashboard",
                intent="greenfield",
                mode="Operate",
                policy=policy,
                primary_system="system:acme",
                structure="structure:dashboard",
            )
        except selection.SelectionError:
            check(True, "pin requires explicit user lock", failed)
        else:
            check(False, "pin requires explicit user lock", failed)

        (root / "project").mkdir()
        pinned = selection.pin_selection(
            root / "project",
            bank,
            target="app/dashboard",
            query="acme dashboard sidebar kpi",
            intent="greenfield",
            mode="Operate",
            policy=policy,
            primary_system="system:acme",
            structure="structure:dashboard",
            user_locked=True,
        )
        artifact = Path(pinned["path"])
        saved = json.loads(artifact.read_text(encoding="utf-8"))
        check(artifact.name == "design-intelligence-selection.json", "selection artifact written", failed)
        check(selection.check_selection(saved, policy) == [], "selection artifact validates", failed)
        check(len(saved["systems"]) == 1 and saved["structure"]["package_files_loaded"] == 0,
              "one system plus normalized structure provenance pinned", failed)
        check("design_evidence" not in saved["systems"][0] and "card" not in saved["structure"],
              "local-only source prose is not persisted", failed)
        check(saved["not_design_md"] is True, "selection is not DESIGN.md", failed)
        check(not policy_mod.compile_secret_patterns(policy)[0].search(artifact.read_text(encoding="utf-8")),
              "selection stores no canary secret", failed)
        valid = selection.validate_selection(bank, artifact, policy)
        check(valid["valid"] is True and valid["status"] == "DEGRADED", "current selection validates", failed)
        stale = dict(saved)
        stale["catalog_generation"] = "0" * 16
        artifact.write_text(json.dumps(stale), encoding="utf-8")
        check(selection.validate_selection(bank, artifact, policy)["status"] == "BLOCKED",
              "stale catalog generation invalidates pin", failed)
        artifact.write_text("[]", encoding="utf-8")
        check(selection.validate_selection(bank, artifact, policy)["status"] == "BLOCKED",
              "non-object selection fails closed", failed)
        artifact.write_text(json.dumps(saved), encoding="utf-8")

        brand = selection.inspect_system(bank, "system:brandco", policy)
        check("canary-from" not in json.dumps(brand), "selected raw prose is sanitized", failed)

        try:
            selection.pin_selection(
                root / "project2",
                bank,
                target="dashboard",
                query="dashboard",
                intent="greenfield",
                mode="Operate",
                policy=policy,
                secondary_system="system:acme",
                structure="structure:dashboard",
                user_locked=True,
            )
        except selection.SelectionError:
            check(True, "secondary cannot exist without primary", failed)
        else:
            check(False, "secondary cannot exist without primary", failed)

        broken = seed_bank(root / "broken")
        lock = catalog.read_lock(broken)
        raw_zip = next((broken / "raw" / "systems").glob("*.zip"))
        raw_zip.write_bytes(raw_zip.read_bytes() + b"tamper")
        check(bool(lock), "tamper fixture has lock", failed)
        try:
            selection.inspect_system(broken, "system:acme", policy)
        except selection.SelectionError:
            check(True, "raw archive tamper blocks selection", failed)
        else:
            check(False, "raw archive tamper blocks selection", failed)

    if failed:
        print(f"test-design-intelligence-selection failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-selection passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
