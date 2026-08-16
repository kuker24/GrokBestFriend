#!/usr/bin/env python3
"""Codebase Memory index freshness for the current working directory."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git_head(cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def list_projects(binary: Path) -> list[dict]:
    out = subprocess.run(
        [str(binary), "cli", "list_projects"],
        check=False,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError(out.stderr.strip() or "list_projects failed")
    data = json.loads(out.stdout)
    return list(data.get("projects") or [])


def match_project(projects: list[dict], cwd: Path) -> dict | None:
    resolved = cwd.resolve()
    for item in projects:
        raw = item.get("root_path") or ""
        if not raw:
            continue
        try:
            if Path(raw).resolve() == resolved:
                return item
        except OSError:
            continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", required=True)
    parser.add_argument("--cwd", default=".")
    args = parser.parse_args()
    binary = Path(args.bin)
    cwd = Path(args.cwd)
    if not binary.is_file():
        print("WARNING: WARN INDEX_TOOL Codebase Memory binary missing")
        return 0
    try:
        projects = list_projects(binary)
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"WARNING: WARN INDEX_TOOL list_projects failed: {exc}")
        return 0

    print(f"OK  INDEX_PROJECTS {len(projects)}")
    item = match_project(projects, cwd)
    if item is None:
        print("WARNING: WARN INDEX_MISSING no Codebase Memory project for cwd")
        return 0
    indexed = (item.get("git") or {}).get("head_sha")
    head = git_head(cwd)
    if indexed and head and indexed != head:
        print(f"WARNING: WARN INDEX_STALE indexed {indexed[:12]} cwd {head[:12]}")
        return 0
    print("OK  INDEX_FRESH cwd is indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
