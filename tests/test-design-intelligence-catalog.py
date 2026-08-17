#!/usr/bin/env python3
"""Catalog identity, lineage, and generational commit."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import catalog  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence_support import seed_bank, write_zip  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def main() -> int:
    failed: list[str] = []
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    home = Path(tempfile.mkdtemp())
    os.environ["HOME"] = str(home)
    with tempfile.TemporaryDirectory() as tmp:
        bank = Path(tmp) / "bank"
        seed_bank(bank)
        items = catalog.load_items(bank)
        index = by_id(items)

        check("system:acme" in index, "stable system id", failed)
        check("system:brandco" in index, "brand fixture id", failed)
        acme = index["system:acme"]
        check(len(acme["source"]["content_sha256"]) == 64, "content SHA", failed)
        check(not str(acme["source"]["path"]).startswith("/"), "no absolute path in source", failed)
        check("runtime_availability" not in acme, "no host probe in catalog", failed)
        check("execution_status" not in acme, "no derived execution_status in catalog", failed)

        plugin = index.get("recipe:design-system-acme")
        check(plugin is not None, "plugin system row exists", failed)
        if plugin:
            check(plugin.get("alias_of") == "system:acme", "path lineage alias", failed)
            check(plugin.get("dedup_reason") == "path-lineage", "alias reason", failed)
            check(plugin["alias_of"] in index, "alias_of points at existing row", failed)

        example = index.get("recipe:example-dashboard")
        check(example is not None, "matching example exists", failed)
        if example:
            check(example.get("alias_of") == "structure:dashboard", "example aliases matching structure", failed)

        unrelated = index.get("recipe:example-unrelated")
        check(unrelated is not None, "unrelated example exists", failed)
        if unrelated:
            check(unrelated.get("alias_of") is None, "unrelated example is not aliased", failed)

        first = catalog.read_lock(bank)
        rebuilt = catalog.rebuild(bank, policy, taxonomy)
        check(rebuilt.get("reused") is True, "idempotent rebuild reuses generation", failed)
        second = catalog.read_lock(bank)
        check(first["generation_id"] == second["generation_id"], "same generation_id", failed)
        jsonl = (bank / "catalog" / first["jsonl_filename"]).read_bytes()
        jsonl2 = (bank / "catalog" / second["jsonl_filename"]).read_bytes()
        check(jsonl == jsonl2, "identical jsonl bytes", failed)
        lines = [json.loads(line) for line in jsonl.decode().splitlines() if line]
        ids = [row["id"] for row in lines]
        check(ids == sorted(ids), "deterministic ordering", failed)

        # Crash before lock: keep previous generation.
        catalog_dir = bank / "catalog"
        incoming_jsonl = catalog_dir / "catalog-deadbeefdeadbeef.jsonl"
        incoming_jsonl.write_text("{}\n", encoding="utf-8")
        still = catalog.load_items(bank)
        check(any(item["id"] == "system:acme" for item in still), "uncommitted generation is ignored", failed)
        check(catalog.read_lock(bank)["generation_id"] == first["generation_id"], "lock unchanged after stray files", failed)

        # Host independence: rebuild after allowlist-looking env
        os.environ["PATH"] = "/nonexistent"
        again = catalog.rebuild(bank, policy, taxonomy)
        check(again["generation_id"] == first["generation_id"], "catalog independent of host PATH", failed)

        orig = catalog.extract_archive

        def broken_extract(*args, **kwargs):
            rows = orig(*args, **kwargs)
            if not rows:
                return rows
            clone = [dict(row) for row in rows]
            clone[0]["kind"] = "not-a-kind"
            return clone

        catalog.extract_archive = broken_extract
        try:
            raised = False
            try:
                catalog.rebuild(bank, policy, taxonomy)
            except catalog.CatalogError as exc:
                raised = "schema_invalid" in str(exc)
            check(raised, "schema error fails rebuild", failed)
            check(catalog.read_lock(bank)["generation_id"] == first["generation_id"], "failed rebuild keeps lock", failed)
        finally:
            catalog.extract_archive = orig

        systems_zip = next((bank / "raw" / "systems").glob("*.zip"))
        with zipfile.ZipFile(systems_zip, "a") as handle:
            handle.writestr("design-systems/README.md", "padding-bytes-change-generation")
        mutated = catalog.rebuild(bank, policy, taxonomy)
        check(mutated.get("reused") is False, "archive byte change is not reused", failed)
        check(mutated["generation_id"] != first["generation_id"], "generation includes input hashes", failed)

        sqlite_path = bank / "catalog" / catalog.read_lock(bank)["sqlite_filename"]
        sqlite_path.unlink()
        missing = False
        try:
            catalog.load_items(bank)
        except catalog.CatalogError as exc:
            missing = "artifacts" in str(exc)
        check(missing, "missing sqlite fails closed", failed)

        empty = Path(tmp) / "empty-family"
        catalog.ensure_bank(empty)
        payload = catalog.import_archive(
            empty,
            write_zip(Path(tmp) / "misc.zip", {"misc/readme.txt": "nope"}),
            policy,
            taxonomy,
        )
        check(payload.get("blocked") is True, "unknown family import blocked", failed)
        check("UNSUPPORTED_ARCHIVE_FAMILY" in payload.get("issues", []), "unknown family issue", failed)
        check(list((empty / "raw" / "plugins").glob("*.zip")) == [], "unknown family not stored as plugins", failed)
        check(list((empty / "quarantine").glob("*.zip")) != [], "unknown family quarantined", failed)

        default_home = home / "DesignIntelligence"
        check(not default_home.exists(), "HOME DesignIntelligence not created", failed)

    if failed:
        print(f"test-design-intelligence-catalog failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-catalog passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
