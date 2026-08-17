#!/usr/bin/env python3
"""Design Intelligence catalog CLI. Not a router and not a skill runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from design_intelligence import archive as archive_mod  # noqa: E402
from design_intelligence import catalog  # noqa: E402
from design_intelligence import doctor as doctor_mod  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence import rank  # noqa: E402
from design_intelligence import report  # noqa: E402


def emit(payload: object) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    known = policy_mod.load_known_sources()
    inspection = archive_mod.inspect_archive(Path(args.archive), policy, taxonomy)
    snapshot = policy_mod.snapshot_for_hashes(known, {inspection.logical_name: inspection.sha256})
    payload = report.inspect_payload(inspection, snapshot)
    emit(payload)
    return 2 if inspection.blocked else 0


def cmd_import(args: argparse.Namespace) -> int:
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    bank = catalog.resolve_bank(args.bank)
    archives = []
    blocked = False
    for raw in args.archive:
        payload = catalog.import_archive(bank, Path(raw), policy, taxonomy)
        archives.append(payload)
        blocked = blocked or bool(payload.get("blocked"))
    rebuilt = catalog.rebuild(bank, policy, taxonomy)
    status = "blocked" if blocked else "ok"
    emit(
        report.import_payload(
            status=status,
            generation_id=rebuilt.get("generation_id"),
            archives=archives,
            counts=rebuilt.get("counts") or {},
            warnings=rebuilt.get("warnings") or [],
        )
    )
    return 2 if blocked else 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    bank = catalog.resolve_bank(args.bank)
    rebuilt = catalog.rebuild(bank, policy, taxonomy)
    emit(
        {
            "status": rebuilt.get("status"),
            "generation_id": rebuilt.get("generation_id"),
            "reused": rebuilt.get("reused"),
            "counts": rebuilt.get("counts"),
            "warnings": rebuilt.get("warnings"),
        }
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    policy = policy_mod.load_policy()
    bank = catalog.resolve_bank(args.bank)
    allowlist = rank.load_allowlist(Path(args.allowlist) if args.allowlist else ROOT / "vendor/skill-allowlist.txt")
    payload = rank.search_bank(
        bank,
        kind=args.kind,
        query=args.query,
        policy=policy,
        allowlist=allowlist,
        include_unavailable=args.include_unavailable,
    )
    emit(payload)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    policy = policy_mod.load_policy()
    known = policy_mod.load_known_sources()
    bank = catalog.resolve_bank(args.bank)
    expected = None
    if args.expected_sha:
        expected = {}
        for item in args.expected_sha:
            if "=" not in item:
                raise SystemExit("--expected-sha needs name=hex")
            name, digest = item.split("=", 1)
            expected[name] = digest
    payload = doctor_mod.doctor(
        bank,
        policy,
        known,
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
        expected_sha=expected,
        claimed_snapshot=args.claimed_snapshot,
    )
    emit(payload)
    if payload.get("status") == "BLOCKED":
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="design-intelligence")
    sub = parser.add_subparsers(dest="cmd", required=True)

    inspect_p = sub.add_parser("inspect-archive")
    inspect_p.add_argument("archive")
    inspect_p.set_defaults(func=cmd_inspect)

    import_p = sub.add_parser("import")
    import_p.add_argument("--bank")
    import_p.add_argument("--archive", action="append", required=True)
    import_p.set_defaults(func=cmd_import)

    rebuild_p = sub.add_parser("rebuild")
    rebuild_p.add_argument("--bank")
    rebuild_p.set_defaults(func=cmd_rebuild)

    search_p = sub.add_parser("search")
    search_p.add_argument("--bank")
    search_p.add_argument("--kind", required=True, choices=["system", "structure", "recipe", "specialist"])
    search_p.add_argument("--query", required=True)
    search_p.add_argument("--allowlist")
    search_p.add_argument("--include-unavailable", action="store_true")
    search_p.set_defaults(func=cmd_search)

    doctor_p = sub.add_parser("doctor")
    doctor_p.add_argument("--bank")
    doctor_p.add_argument("--expected-sha", action="append", default=[])
    doctor_p.add_argument("--claimed-snapshot")
    doctor_p.set_defaults(func=cmd_doctor)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
