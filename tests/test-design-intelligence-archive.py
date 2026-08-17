#!/usr/bin/env python3
"""Archive safety for untrusted ZIP input."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import archive as archive_mod  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence_support import (  # noqa: E402
    absolute_zip,
    encrypted_zip,
    symlink_zip,
    traversal_zip,
    write_zip,
)


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    failed: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        trav = archive_mod.inspect_archive(traversal_zip(tmp_path / "trav.zip"), policy, taxonomy)
        check(trav.blocked and any(i.code == "traversal" for i in trav.issues), "reject traversal", failed)

        absz = archive_mod.inspect_archive(absolute_zip(tmp_path / "abs.zip"), policy, taxonomy)
        check(absz.blocked and any(i.code == "absolute" for i in absz.issues), "reject absolute path", failed)

        link = archive_mod.inspect_archive(symlink_zip(tmp_path / "link.zip"), policy, taxonomy)
        check(link.blocked and any(i.code == "symlink" for i in link.issues), "reject symlink", failed)

        enc = archive_mod.inspect_archive(encrypted_zip(tmp_path / "enc.zip"), policy, taxonomy)
        check(enc.blocked and any(i.code == "encrypted" for i in enc.issues), "reject encrypted member", failed)

        bad = write_zip(tmp_path / "bad.json.zip", {"design-systems/x/manifest.json": "{not-json"})
        # invalid JSON is detected at extract, not zip header
        inspection = archive_mod.inspect_archive(bad, policy, taxonomy)
        check(not inspection.blocked, "invalid json is still a readable zip", failed)
        with archive_mod.open_zip(bad) as handle:
            _, err = __import__("design_intelligence.normalize", fromlist=["load_json_member"]).load_json_member(
                handle, "design-systems/x/manifest.json", policy
            )
        check(err is not None and "invalid_json" in err, "reject invalid JSON member", failed)

        unsafe_decl = write_zip(
            tmp_path / "decl.zip",
            {"design-systems/ok/manifest.json": '{"id":"ok"}'},
        )
        with archive_mod.open_zip(unsafe_decl) as handle:
            raised = False
            try:
                archive_mod.read_member(handle, "../escape.txt", policy)
            except archive_mod.ArchiveError:
                raised = True
            check(raised, "reject unsafe declared path on read", failed)

        # compression abuse: member uncompressed cap
        huge = write_zip(tmp_path / "huge.zip", {"pad.bin": "A" * 100})
        # inspect uses ZipInfo.file_size; craft a zipinfo with huge size
        bomb = tmp_path / "bomb.zip"
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            info = zipfile.ZipInfo("zeros.bin")
            zf.writestr(info, b"A" * 32)
        # Can't easily lie about file_size after write; lower the policy cap instead.
        tight = dict(policy)
        tight["zip"] = dict(policy["zip"])
        tight["zip"]["max_member_uncompressed"] = 16
        small = write_zip(tmp_path / "oversize.zip", {"big.bin": "B" * 64})
        over = archive_mod.inspect_archive(small, tight, taxonomy)
        check(over.blocked and any(i.code == "member_too_large" for i in over.issues), "limit decompression abuse", failed)
        del huge, bomb

    if failed:
        print(f"test-design-intelligence-archive failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-archive passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
