#!/usr/bin/env python3
"""Ownership checks for GrokBestFriend-managed names."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PRODUCT = "GrokBestFriend"
SKILL_MARKER = ".grokbestfriend-owned.json"
DIR_MARKER = ".grokbestfriend-owned.json"


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def load_manifest(path: Path) -> dict | None:
    data = _load_json(path)
    if not data or data.get("product") != PRODUCT:
        return None
    return data


def _manifest_basenames(manifest: dict | None, key: str) -> set[str]:
    if not manifest:
        return set()
    names: set[str] = set()
    for item in manifest.get(key) or []:
        names.add(Path(str(item)).name)
    return names


def skill_owned(skill_dir: Path, manifest: dict | None, name: str) -> bool:
    marker = _load_json(skill_dir / SKILL_MARKER)
    if marker and marker.get("product") == PRODUCT:
        return True
    if not skill_dir.exists():
        return True
    return name in _manifest_basenames(manifest, "skills")


def listed_file_owned(path: Path, manifest: dict | None, key: str, name: str) -> bool:
    marker = _load_json(path.parent / DIR_MARKER)
    if marker and marker.get("product") == PRODUCT:
        files = marker.get("files") or []
        if name in files:
            return True
    if not path.exists():
        return True
    return name in _manifest_basenames(manifest, key)


def write_skill_marker(skill_dir: Path, name: str, version: str) -> None:
    payload = {
        "product": PRODUCT,
        "productVersion": version,
        "name": name,
    }
    path = skill_dir / SKILL_MARKER
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_dir_marker(directory: Path, files: list[str], version: str) -> None:
    payload = {
        "product": PRODUCT,
        "productVersion": version,
        "files": files,
    }
    directory.mkdir(parents=True, exist_ok=True)
    (directory / DIR_MARKER).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: ownership.py check-skill|check-rule|check-hook ...", file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "check-skill":
        skill_dir = Path(argv[2])
        name = argv[3]
        manifest = load_manifest(Path(argv[4])) if len(argv) > 4 else None
        ok = skill_owned(skill_dir, manifest, name)
        print("owned" if ok else "foreign")
        return 0 if ok else 1
    if cmd == "check-rule":
        path = Path(argv[2])
        manifest = load_manifest(Path(argv[3])) if len(argv) > 3 else None
        ok = listed_file_owned(path, manifest, "rules", path.name)
        print("owned" if ok else "foreign")
        return 0 if ok else 1
    if cmd == "check-hook":
        path = Path(argv[2])
        manifest = load_manifest(Path(argv[3])) if len(argv) > 3 else None
        ok = listed_file_owned(path, manifest, "hooks", path.name)
        print("owned" if ok else "foreign")
        return 0 if ok else 1
    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
