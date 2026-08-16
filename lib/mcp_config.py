#!/usr/bin/env python3
"""Section-aware rewrite of Grok MCP server blocks in config.toml."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TABLE_RE = re.compile(r"^\[([^\[\]\n]+)\]\s*$")
AOT_RE = re.compile(r"^\[\[([^\[\]\n]+)\]\]\s*$")
ASSIGN_RE = re.compile(r"^[ \t]*([A-Za-z0-9_-]+)[ \t]*=")
SHADCN_TIMEOUT_SEC = 90


def _sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines(keepends=True)
    sections: list[dict[str, Any]] = [{"kind": "root", "name": "", "start": 0}]
    for index, line in enumerate(lines):
        stripped = line.split("#", 1)[0].rstrip()
        aot = AOT_RE.match(stripped)
        table = TABLE_RE.match(stripped)
        if aot:
            sections.append({"kind": "aot", "name": aot.group(1).strip(), "start": index})
        elif table:
            sections.append({"kind": "table", "name": table.group(1).strip(), "start": index})
    for index, section in enumerate(sections):
        end = sections[index + 1]["start"] if index + 1 < len(sections) else len(lines)
        section["end"] = end
        section["lines"] = lines[section["start"] : end]
    return sections


def _rebuild(sections: list[dict[str, Any]]) -> str:
    return "".join(line for section in sections for line in section["lines"])


def _newline(lines: list[str]) -> str:
    if lines and "\r\n" in lines[0]:
        return "\r\n"
    return "\n"


def _assignment_span(lines: list[str], start: int) -> int:
    stripped = lines[start].split("#", 1)[0]
    depth = stripped.count("[") - stripped.count("]")
    index = start + 1
    while index < len(lines) and depth > 0:
        piece = lines[index].split("#", 1)[0]
        depth += piece.count("[") - piece.count("]")
        index += 1
    return index


def _key_spans(lines: list[str], key: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = 1 if lines else 0
    while index < len(lines):
        stripped = lines[index].split("#", 1)[0].rstrip()
        match = ASSIGN_RE.match(stripped)
        if match and match.group(1) == key:
            end = _assignment_span(lines, index)
            spans.append((index, end))
            index = end
            continue
        index += 1
    return spans


def has_table(text: str, name: str) -> bool:
    return any(section["kind"] == "table" and section["name"] == name for section in _sections(text))


def upsert_table_key(text: str, table: str, key: str, rhs: str) -> str:
    """Set key = rhs in the first matching table. Insert once, replace, or collapse dupes.

    Missing table: no-op. rhs is the already-rendered right-hand side
    (90, "npx", ["-y", "shadcn@4.18.0", "mcp"]).
    """
    sections = _sections(text)
    target = next((section for section in sections if section["kind"] == "table" and section["name"] == table), None)
    if target is None:
        return text
    lines = list(target["lines"])
    rendered = f"{key} = {rhs}{_newline(lines)}"
    spans = _key_spans(lines, key)
    if not spans:
        insert_at = 1 if lines else 0
        lines.insert(insert_at, rendered)
    else:
        for start, end in reversed(spans[1:]):
            del lines[start:end]
        first_start, first_end = spans[0]
        lines[first_start:first_end] = [rendered]
    target["lines"] = lines
    return _rebuild(sections)


def rewrite_mcp_config(
    text: str,
    *,
    memory_bin: str,
    serena_bin: str,
    shadcn_pin: str,
    startup_timeout_sec: int = SHADCN_TIMEOUT_SEC,
) -> str:
    updated = text
    if memory_bin:
        updated = upsert_table_key(
            updated, "mcp_servers.codebase-memory-mcp", "command", json.dumps(memory_bin)
        )
    if serena_bin:
        updated = upsert_table_key(updated, "mcp_servers.serena", "command", json.dumps(serena_bin))
    if has_table(updated, "mcp_servers.shadcn"):
        args = ["-y", f"shadcn@{shadcn_pin}", "mcp"]
        updated = upsert_table_key(updated, "mcp_servers.shadcn", "args", json.dumps(args))
        updated = upsert_table_key(
            updated, "mcp_servers.shadcn", "startup_timeout_sec", str(int(startup_timeout_sec))
        )
    return updated


def rewrite_file(
    path: Path,
    *,
    memory_bin: str,
    serena_bin: str,
    shadcn_pin: str,
    startup_timeout_sec: int = SHADCN_TIMEOUT_SEC,
) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = rewrite_mcp_config(
        text,
        memory_bin=memory_bin,
        serena_bin=serena_bin,
        shadcn_pin=shadcn_pin,
        startup_timeout_sec=startup_timeout_sec,
    )
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["rewrite"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--memory-bin", default="")
    parser.add_argument("--serena-bin", default="")
    parser.add_argument("--shadcn-pin", required=True)
    parser.add_argument("--startup-timeout-sec", type=int, default=SHADCN_TIMEOUT_SEC)
    args = parser.parse_args()
    rewrite_file(
        Path(args.config),
        memory_bin=args.memory_bin,
        serena_bin=args.serena_bin,
        shadcn_pin=args.shadcn_pin,
        startup_timeout_sec=args.startup_timeout_sec,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
