#!/usr/bin/env python3
"""Limited, fail-closed mutation of GrokBestFriend enforced config keys."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


TABLE_RE = re.compile(r"^\[([^\[\]\n]+)\]\s*$")
AOT_RE = re.compile(r"^\[\[([^\[\]\n]+)\]\]\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*=")
OFFICIAL_NAME = "xAI Official"
DEFAULT_OFFICIAL_GIT = "https://github.com/xai-org/plugin-marketplace.git"


class PolicyError(Exception):
    pass


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    raise PolicyError(f"unsupported enforced value type: {type(value).__name__}")


def _split_key(dotted: str) -> tuple[str, str]:
    if dotted == "marketplace.official.git":
        return "marketplace.sources", "git"
    if "." not in dotted:
        raise PolicyError(f"enforced key has no table: {dotted}")
    table, key = dotted.rsplit(".", 1)
    return table, key


def _sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines(keepends=True)
    sections: list[dict[str, Any]] = [
        {"kind": "root", "name": "", "start": 0, "header": ""}
    ]
    for index, line in enumerate(lines):
        stripped = line.split("#", 1)[0].rstrip()
        aot = AOT_RE.match(stripped)
        table = TABLE_RE.match(stripped)
        if aot:
            sections.append({"kind": "aot", "name": aot.group(1).strip(), "start": index, "header": line})
        elif table:
            sections.append({"kind": "table", "name": table.group(1).strip(), "start": index, "header": line})
    for index, section in enumerate(sections):
        end = sections[index + 1]["start"] if index + 1 < len(sections) else len(lines)
        section["end"] = end
        section["lines"] = lines[section["start"] : end]
    return sections


def _assignments(lines: list[str], skip_header: bool) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    start = 1 if skip_header and lines else 0
    for offset, line in enumerate(lines[start:], start=start):
        stripped = line.split("#", 1)[0].rstrip()
        match = ASSIGN_RE.match(stripped)
        if match:
            found.append((offset, match.group(1)))
    return found


def _table_sections(sections: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [section for section in sections if section["kind"] == "table" and section["name"] == name]


def _replace_assignment(lines: list[str], key: str, value: Any, skip_header: bool) -> list[str]:
    matches = [(idx, name) for idx, name in _assignments(lines, skip_header) if name == key]
    if len(matches) > 1:
        raise PolicyError(f"ambiguous key {key}: appears {len(matches)} times")
    rendered = f"{key} = {_format_toml_value(value)}\n"
    if len(matches) == 1:
        idx = matches[0][0]
        suffix = ""
        raw = lines[idx]
        if "\r\n" in raw:
            rendered = rendered.replace("\n", "\r\n")
        comment = ""
        if "#" in raw:
            after = raw.split("#", 1)[1]
            comment = " #" + after if after.startswith(" ") else "#" + after
            if not comment.endswith("\n"):
                comment += "\n"
            rendered = f"{key} = {_format_toml_value(value)}{comment}"
        lines = list(lines)
        lines[idx] = rendered
        return lines
    insert_at = 1 if skip_header and lines else len(lines)
    lines = list(lines)
    lines.insert(insert_at, rendered)
    return lines


def _rebuild(sections: list[dict[str, Any]]) -> str:
    return "".join(line for section in sections for line in section["lines"])


def _parse_simple_assignments(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in lines:
        stripped = raw.split("#", 1)[0].strip()
        match = ASSIGN_RE.match(stripped)
        if not match:
            continue
        key = match.group(1)
        rhs = stripped.split("=", 1)[1].strip()
        if len(rhs) >= 2 and rhs[0] == rhs[-1] and rhs[0] in {'"', "'"}:
            rhs = rhs[1:-1]
        values[key] = rhs
    return values


def apply_text(text: str, policy: dict[str, Any], template: str | None = None) -> str:
    if not text.strip():
        text = template or ""
        if not text.strip():
            raise PolicyError("empty config and no template")

    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise PolicyError(f"config is not valid TOML: {exc}") from exc

    enforced: dict[str, Any] = dict(policy.get("enforced") or {})
    official_git = enforced.pop("marketplace.official.git", DEFAULT_OFFICIAL_GIT)

    sections = _sections(text)
    mutated = False

    by_table: dict[str, list[tuple[str, Any]]] = {}
    for dotted, value in enforced.items():
        table, key = _split_key(dotted)
        by_table.setdefault(table, []).append((key, value))

    for table, items in by_table.items():
        matches = _table_sections(sections, table)
        if len(matches) > 1:
            raise PolicyError(f"ambiguous table [{table}]: appears {len(matches)} times")
        if not matches:
            block = [f"\n[{table}]\n"]
            for key, value in items:
                block.append(f"{key} = {_format_toml_value(value)}\n")
            sections.append(
                {
                    "kind": "table",
                    "name": table,
                    "start": 0,
                    "end": 0,
                    "header": f"[{table}]\n",
                    "lines": block,
                }
            )
            mutated = True
            continue
        section = matches[0]
        lines = list(section["lines"])
        for key, value in items:
            current = parsed
            ok = True
            for part in table.split("."):
                if not isinstance(current, dict) or part not in current:
                    ok = False
                    break
                current = current[part]
            if ok and isinstance(current, dict) and current.get(key) == value:
                continue
            lines = _replace_assignment(lines, key, value, skip_header=True)
            mutated = True
        section["lines"] = lines

    aots = [section for section in sections if section["kind"] == "aot" and section["name"] == "marketplace.sources"]
    official_hits = []
    for section in aots:
        values = _parse_simple_assignments(section["lines"][1:])
        if values.get("name") == OFFICIAL_NAME:
            official_hits.append(section)
    if len(official_hits) > 1:
        raise PolicyError("ambiguous [[marketplace.sources]] official entries")
    if official_hits:
        section = official_hits[0]
        values = _parse_simple_assignments(section["lines"][1:])
        if values.get("git") != official_git:
            section["lines"] = _replace_assignment(list(section["lines"]), "git", official_git, skip_header=True)
            mutated = True
    else:
        sections.append(
            {
                "kind": "aot",
                "name": "marketplace.sources",
                "start": 0,
                "end": 0,
                "header": "[[marketplace.sources]]\n",
                "lines": [
                    "\n[[marketplace.sources]]\n",
                    f'name = "{OFFICIAL_NAME}"\n',
                    f"git = {_format_toml_value(official_git)}\n",
                ],
            }
        )
        mutated = True

    if not mutated:
        return text
    updated = _rebuild(sections)
    if not updated.endswith("\n"):
        updated += "\n"
    try:
        tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        raise PolicyError(f"mutated config is not valid TOML: {exc}") from exc
    return updated


def check_parsed(parsed: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    enforced: dict[str, Any] = dict(policy.get("enforced") or {})
    official_git = enforced.pop("marketplace.official.git", DEFAULT_OFFICIAL_GIT)

    def lookup(dotted: str) -> Any:
        node: Any = parsed
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    for dotted, wanted in enforced.items():
        got = lookup(dotted)
        if got != wanted:
            errors.append(f"{dotted} wanted {wanted!r} got {got!r}")

    sources = (parsed.get("marketplace") or {}).get("sources") or []
    official = [
        item
        for item in sources
        if isinstance(item, dict) and item.get("name") == OFFICIAL_NAME
    ]
    if not official:
        errors.append("marketplace official source missing")
    elif len(official) > 1:
        errors.append("marketplace official source is ambiguous")
    elif official[0].get("git") != official_git:
        errors.append("marketplace official git URL mismatch")
    return errors


def check_text(text: str, policy: dict[str, Any]) -> list[str]:
    if not text.strip():
        return ["config.toml is empty"]
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return [f"config is not valid TOML: {exc}"]
    return check_parsed(parsed, policy)


def apply_file(config_path: Path, policy_path: Path, template_path: Path | None) -> int:
    policy = load_policy(policy_path)
    template = template_path.read_text(encoding="utf-8") if template_path else None
    original = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    try:
        updated = apply_text(original, policy, template)
    except PolicyError as exc:
        print(f"ERROR: FAIL runtime-policy: {exc}", file=sys.stderr)
        return 1
    if updated != original:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(updated, encoding="utf-8")
    return 0


def check_file(config_path: Path, policy_path: Path) -> int:
    policy = load_policy(policy_path)
    if not config_path.is_file():
        print("ERROR: FAIL runtime-policy: missing config.toml", file=sys.stderr)
        return 1
    errors = check_text(config_path.read_text(encoding="utf-8"), policy)
    if errors:
        for item in errors:
            print("ERROR: FAIL runtime-policy: " + item, file=sys.stderr)
        return 1
    print("OK  runtime-policy")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "check"))
    parser.add_argument("--config", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--template")
    args = parser.parse_args(argv)
    config = Path(args.config)
    policy = Path(args.policy)
    if args.command == "apply":
        template = Path(args.template) if args.template else None
        return apply_file(config, policy, template)
    return check_file(config, policy)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
