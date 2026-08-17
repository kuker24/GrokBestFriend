#!/usr/bin/env python3
"""Optional live-archive audit. Skips unless GROK_DESIGN_INTELLIGENCE_ARCHIVES is set."""

from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from design_intelligence import archive as archive_mod  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402


def main() -> int:
    raw = os.environ.get("GROK_DESIGN_INTELLIGENCE_ARCHIVES", "").strip()
    if not raw:
        print("SKIP_OPTIONAL_ARCHIVE_AUDIT reason=env-not-set")
        return 0

    paths: list[Path] = []
    for part in raw.replace("\n", ":").split(":"):
        if not part:
            continue
        candidate = Path(part)
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob("*.zip")))
        else:
            paths.append(candidate)
    if not paths:
        print("SKIP_OPTIONAL_ARCHIVE_AUDIT reason=env-not-set")
        return 0

    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    known = policy_mod.load_known_sources()
    report: dict[str, object] = {"archives": []}
    for path in paths:
        if not path.is_file():
            print(f"FAIL missing {path}", file=sys.stderr)
            return 1
        inspection = archive_mod.inspect_archive(path, policy, taxonomy)
        counts = audit_zip(path, inspection.family)
        entry = {
            "logical_name": inspection.logical_name,
            "sha256": inspection.sha256,
            "blocked": inspection.blocked,
            "family": inspection.family,
            "counts": counts,
        }
        report["archives"].append(entry)
        print(json.dumps(entry, sort_keys=True))
        snapshot = None
        for snap in known.get("snapshots") or []:
            digest = (snap.get("archives") or {}).get(inspection.logical_name)
            if digest == inspection.sha256:
                snapshot = snap.get("id")
        if snapshot:
            print(f"OK  {inspection.logical_name} matches {snapshot}")
        else:
            print(f"OK  {inspection.logical_name} unknown snapshot (DEGRADED, not fail)")
        if inspection.blocked:
            print(f"FAIL unsafe archive {inspection.logical_name}", file=sys.stderr)
            return 1
    print("test-design-intelligence-optional-audit passed")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def audit_zip(path: Path, family: str | None) -> dict[str, int]:
    with zipfile.ZipFile(path) as zf:
        names = [name.replace("\\", "/") for name in zf.namelist()]
    counts: dict[str, int] = {"members": len(names)}
    if family == "systems":
        counts["systems"] = sum(
            1
            for name in names
            if name.endswith("/manifest.json") and name.count("/") == 2
        )
    if family == "templates":
        counts["templates"] = sum(1 for name in names if name.endswith("/SKILL.md") and name.count("/") == 2)
        counts["template_license"] = sum(
            1
            for name in names
            if name.count("/") == 2 and name.split("/")[-1] in {"LICENSE", "LICENSE.txt", "LICENSE.md"}
        )
    if family == "skills":
        counts["skills"] = sum(1 for name in names if name.endswith("/SKILL.md") and name.count("/") == 2)
        stubs = 0
        with zipfile.ZipFile(path) as zf:
            for name in names:
                if name.endswith("/SKILL.md") and name.count("/") == 2:
                    text = zf.read(name).decode("utf-8", "replace")
                    if "This catalogue entry advertises the skill in Open Design" in text or "install the upstream" in text:
                        stubs += 1
        counts["stubs"] = stubs
    if family == "plugins":
        counts["open_design_json"] = sum(1 for name in names if name.endswith("open-design.json"))
        counts["root_skill_md"] = sum(
            1
            for name in names
            if name.endswith("/SKILL.md")
            and (
                name.startswith("plugins/_official/")
                and name.count("/") == 4
                or name.startswith("plugins/community/")
                and name.count("/") == 3
                or name.startswith("plugins/spec/examples/")
                and name.count("/") == 4
            )
        )
        counts["community"] = len(
            {
                name.split("/")[2]
                for name in names
                if name.startswith("plugins/community/") and name.count("/") >= 2 and name.split("/")[2]
            }
        )
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
