"""Catalog doctor. Does not write host probes into the catalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import archive as archive_mod
from . import policy as policy_mod
from .catalog import listed_raw, load_items, read_lock, resolve_bank
from .rank import derive_hit, load_allowlist, probe_item


def doctor(
    bank: Path | None,
    policy: dict[str, Any],
    known: dict[str, Any],
    *,
    allowlist_path: Path | None = None,
    expected_sha: dict[str, str] | None = None,
    claimed_snapshot: str | None = None,
    host_commands: set[str] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    status = "PASS"

    def add(name: str, level: str, detail: str = "") -> None:
        nonlocal status
        checks.append({"name": name, "level": level, "detail": detail})
        if level == "BLOCKED":
            status = "BLOCKED"
        elif level == "DEGRADED" and status != "BLOCKED":
            status = "DEGRADED"

    if bank is None:
        bank = resolve_bank(None, env=env)
    if not bank.exists():
        add("bank_root", "DEGRADED", "missing")
        return {"status": status, "checks": checks, "bank": str(bank)}

    add("bank_root", "PASS", str(bank))
    lock = read_lock(bank)
    if lock is None:
        add("catalog_lock", "DEGRADED", "missing")
        return {"status": status, "checks": checks, "bank": str(bank)}

    if lock.get("schema_version") != 1:
        add("schema_version", "BLOCKED", str(lock.get("schema_version")))
    else:
        add("schema_version", "PASS", "1")

    try:
        items = load_items(bank)
        add("index_parse", "PASS", str(len(items)))
    except Exception as exc:
        add("index_parse", "BLOCKED", str(exc))
        return {"status": status, "checks": checks, "bank": str(bank)}

    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        add("duplicate_ids", "BLOCKED", "catalog ids are not unique")
    else:
        add("duplicate_ids", "PASS")

    catalog_ids = set(ids)
    dangling = []
    for item in items:
        for key in ("alias_of", "duplicate_of"):
            pointer = item.get(key)
            if pointer and pointer not in catalog_ids:
                dangling.append(f"{item['id']}:{key}:{pointer}")
    if dangling:
        add("lineage_pointers", "BLOCKED", ",".join(dangling[:8]))
    else:
        add("lineage_pointers", "PASS")

    leaked = [item["id"] for item in items if str((item.get("source") or {}).get("path") or "").startswith("/")]
    if leaked:
        add("absolute_path_leak", "BLOCKED", ",".join(leaked[:8]))
    else:
        add("absolute_path_leak", "PASS")

    persisted_probe = [
        item["id"]
        for item in items
        if "runtime_availability" in item or "available_via" in item or "execution_status" in item
    ]
    if persisted_probe:
        add("host_probe_persisted", "BLOCKED", ",".join(persisted_probe[:8]))
    else:
        add("host_probe_persisted", "PASS")

    if any(item.get("execution_class") in {"stub", "quarantined"} or (item.get("license") or {}).get("status") == "unknown" for item in items):
        add("reference_limitations", "DEGRADED", "stubs, quarantine, or unknown license present")

    hashes = {row[2].get("logical_name") or row[1].name: archive_mod.sha256_file(row[1]) for row in listed_raw(bank)}
    snapshot = policy_mod.snapshot_for_hashes(known, hashes)
    if hashes and snapshot:
        add("archive_hashes", "PASS", snapshot)
    elif hashes:
        add("archive_hashes", "DEGRADED", "unknown snapshot")
    else:
        add("archive_hashes", "PASS", "no-raw-archives")

    if expected_sha:
        for name, digest in expected_sha.items():
            actual = hashes.get(name)
            if actual != digest:
                add("expected_sha", "BLOCKED", f"{name}")
    if claimed_snapshot:
        known_ids = {snap.get("id") for snap in known.get("snapshots") or []}
        if claimed_snapshot not in known_ids:
            add("claimed_snapshot", "BLOCKED", claimed_snapshot)
        elif snapshot != claimed_snapshot:
            add("claimed_snapshot", "BLOCKED", f"have {snapshot}")

    allowlist = load_allowlist(allowlist_path) if allowlist_path else set()
    missing_native = 0
    for item in items:
        if item.get("kind") != "specialist":
            continue
        probe = probe_item(item, allowlist=allowlist, host_commands=host_commands)
        derived = derive_hit(item, probe)
        if derived["execution_status"] in {"provider-missing", "connector-missing"}:
            missing_native += 1
    if missing_native:
        add("provider_connector", "DEGRADED", str(missing_native))
    else:
        add("provider_connector", "PASS")

    failed = bank / "reports" / "rebuild-failed.json"
    if failed.is_file() and lock:
        add("rebuild_failed_report", "DEGRADED", "present")

    return {
        "status": status,
        "checks": checks,
        "bank": str(bank),
        "generation_id": lock.get("generation_id"),
        "counts": {
            "items": len(items),
            "aliases": sum(1 for item in items if item.get("alias_of")),
            "duplicates": sum(1 for item in items if item.get("duplicate_of")),
        },
    }
