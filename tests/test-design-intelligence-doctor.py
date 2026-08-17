#!/usr/bin/env python3
"""Doctor statuses for fixture banks."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import catalog  # noqa: E402
from design_intelligence import doctor as doctor_mod  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence_support import seed_bank, traversal_zip  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    failed: list[str] = []
    os.environ["HOME"] = tempfile.mkdtemp()
    policy = policy_mod.load_policy()
    known = policy_mod.load_known_sources()
    taxonomy = policy_mod.load_taxonomy()

    missing = doctor_mod.doctor(Path("/tmp/di-missing-bank-does-not-exist"), policy, known)
    check(missing["status"] == "DEGRADED", "missing bank DEGRADED", failed)

    with tempfile.TemporaryDirectory() as tmp:
        bank = seed_bank(Path(tmp) / "bank")
        report = doctor_mod.doctor(bank, policy, known, allowlist_path=ROOT / "vendor/skill-allowlist.txt")
        check(report["status"] == "DEGRADED", "fixture with stubs/unknown license DEGRADED", failed)
        names = {row["name"]: row["level"] for row in report["checks"]}
        check(names.get("lineage_pointers") == "PASS", "lineage pointers pass", failed)
        check(names.get("host_probe_persisted") == "PASS", "no persisted probe", failed)
        check(names.get("archive_hashes") == "DEGRADED", "unknown snapshot DEGRADED", failed)
        check(names.get("catalog_rows") == "PASS", "fixture rows valid", failed)
        check(names.get("generation_identity") == "PASS", "generation identity valid", failed)
        check(names.get("lock_artifacts") == "PASS", "lock artifacts present", failed)
        check(names.get("duplicate_logical_name") == "PASS", "fixture logical names unique", failed)

        snap = known["snapshots"][0]["archives"]
        check(policy_mod.snapshot_for_hashes(known, dict(snap)) == "od-packs-2026-07-20", "exact snapshot matches", failed)
        partial = dict(list(snap.items())[:2])
        check(policy_mod.snapshot_for_hashes(known, partial) is None, "partial snapshot is not known", failed)
        extra = dict(snap)
        extra["other.zip"] = "a" * 64
        check(policy_mod.snapshot_for_hashes(known, extra) is None, "extra archive is not known", failed)

        broken = Path(tmp) / "missing-sqlite"
        seed_bank(broken)
        lock = catalog.read_lock(broken)
        (broken / "catalog" / lock["sqlite_filename"]).unlink()
        missing = doctor_mod.doctor(broken, policy, known)
        check(missing["status"] == "BLOCKED", "missing sqlite BLOCKED", failed)

        blocked = doctor_mod.doctor(
            bank,
            policy,
            known,
            expected_sha={"design-systems.zip": "0" * 64},
        )
        check(blocked["status"] == "BLOCKED", "--expected-sha mismatch BLOCKED", failed)

        unsafe_bank = Path(tmp) / "unsafe"
        catalog.ensure_bank(unsafe_bank)
        payload = catalog.import_archive(unsafe_bank, traversal_zip(Path(tmp) / "bad.zip"), policy, taxonomy)
        check(payload.get("blocked") is True, "unsafe archive quarantined on import", failed)
        rebuilt = catalog.rebuild(unsafe_bank, policy, taxonomy)
        check(rebuilt.get("counts", {}).get("items", 0) == 0, "blocked archive adds no items", failed)

    if failed:
        print(f"test-design-intelligence-doctor failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-doctor passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
