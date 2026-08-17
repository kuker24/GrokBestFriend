"""Helpers for Design Intelligence tests. Builds tiny zips at runtime."""

from __future__ import annotations

import io
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SRC = ROOT / "tests/fixtures/design-intelligence/src"


def write_zip(path: Path, files: dict[str, bytes | str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            data = body.encode("utf-8") if isinstance(body, str) else body
            archive.writestr(name, data)
    return path


def zip_tree(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(src.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(src).as_posix())
    return dest


def pack(name: str, dest: Path) -> Path:
    return zip_tree(FIXTURE_SRC / name, dest)


def traversal_zip(path: Path) -> Path:
    return write_zip(path, {"../../evil.txt": "nope"})


def absolute_zip(path: Path) -> Path:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        info = zipfile.ZipInfo("/tmp/evil.txt")
        archive.writestr(info, b"nope")
    path.write_bytes(data.getvalue())
    return path


def symlink_zip(path: Path) -> Path:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"/etc/passwd")
    path.write_bytes(data.getvalue())
    return path


def encrypted_zip(path: Path) -> Path:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("secret.json", b"{}")
        archive.getinfo("secret.json").flag_bits |= 0x1
    path.write_bytes(data.getvalue())
    return path


def seed_bank(dest: Path) -> Path:
    import sys

    sys.path.insert(0, str(ROOT / "lib"))
    from design_intelligence import catalog
    from design_intelligence import policy as policy_mod

    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    catalog.ensure_bank(dest)
    for name in ("systems-pack", "templates-pack", "plugins-pack", "skills-pack"):
        zip_path = dest / f"{name}.zip"
        pack(name, zip_path)
        catalog.import_archive(dest, zip_path, policy, taxonomy)
    catalog.rebuild(dest, policy, taxonomy)
    return dest


def bomb_zip(path: Path) -> Path:
    # High ratio: tiny stored name, huge declared size via ZipInfo.file_size.
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo("zeros.bin")
        payload = b"0" * 64
        archive.writestr(info, payload)
    raw = bytearray(data.getvalue())
    path.write_bytes(bytes(raw))
    # Re-open and patch file_size through a second writestr with huge file.
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo("zeros.bin")
        blob = b"A" * 200
        archive.writestr(info, blob)
        info = archive.getinfo("zeros.bin")
        info.file_size = 80 * 1024 * 1024
    path.write_bytes(data.getvalue())
    return path
