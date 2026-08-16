#!/usr/bin/env python3
"""Idempotent section-aware rewrite of the shadcn MCP block."""

from __future__ import annotations

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from mcp_config import rewrite_file, rewrite_mcp_config, upsert_table_key  # noqa: E402


PIN = "4.18.0"
MEMORY = "/home/user/.grok/runtime/components/codebase-memory/bin/codebase-memory-mcp"
SERENA = "/home/user/.local/bin/serena"


def rewrite(text: str) -> str:
    return rewrite_mcp_config(text, memory_bin=MEMORY, serena_bin=SERENA, shadcn_pin=PIN)


class McpConfigTests(unittest.TestCase):
    def test_timeout_after_command_is_detected(self) -> None:
        text = (
            "[mcp_servers.shadcn]\n"
            "startup_timeout_sec = 90\n"
            'command = "npx"\n'
            'args = ["-y", "shadcn@4.18.0", "mcp"]\n'
        )
        updated = rewrite(text)
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["mcp_servers"]["shadcn"]["startup_timeout_sec"], 90)
        self.assertEqual(updated.count("startup_timeout_sec"), 1)

    def test_inserts_timeout_once_when_missing(self) -> None:
        text = (
            "[mcp_servers.shadcn]\n"
            'command = "npx"\n'
            'args = ["-y", "shadcn@4.18.0", "mcp"]\n'
        )
        updated = rewrite(text)
        self.assertEqual(updated.count("startup_timeout_sec"), 1)
        self.assertEqual(tomllib.loads(updated)["mcp_servers"]["shadcn"]["startup_timeout_sec"], 90)

    def test_replaces_wrong_timeout_value(self) -> None:
        text = "[mcp_servers.shadcn]\nstartup_timeout_sec = 30\ncommand = \"npx\"\n"
        updated = rewrite(text)
        self.assertEqual(tomllib.loads(updated)["mcp_servers"]["shadcn"]["startup_timeout_sec"], 90)
        self.assertEqual(updated.count("startup_timeout_sec"), 1)

    def test_collapses_duplicate_timeout_keys(self) -> None:
        text = (
            "[mcp_servers.shadcn]\n"
            "startup_timeout_sec = 90\n"
            "startup_timeout_sec = 90\n"
            'command = "npx"\n'
        )
        updated = rewrite(text)
        tomllib.loads(updated)
        self.assertEqual(updated.count("startup_timeout_sec"), 1)

    def test_rewrite_is_idempotent(self) -> None:
        text = (
            "[mcp_servers.codebase-memory-mcp]\n"
            'command = "/old/memory"\n'
            "\n"
            "[mcp_servers.shadcn]\n"
            'command = "npx"\n'
            "args = [\n"
            '  "-y",\n'
            '  "shadcn@latest",\n'
            '  "mcp",\n'
            "]\n"
            "\n"
            "[mcp_servers.serena]\n"
            'command = "/old/serena"\n'
            "startup_timeout_sec = 5\n"
        )
        first = rewrite(text)
        second = rewrite(first)
        third = rewrite(second)
        self.assertEqual(first, second)
        self.assertEqual(second, third)
        parsed = tomllib.loads(third)
        self.assertEqual(parsed["mcp_servers"]["codebase-memory-mcp"]["command"], MEMORY)
        self.assertEqual(parsed["mcp_servers"]["serena"]["command"], SERENA)
        self.assertEqual(parsed["mcp_servers"]["serena"]["startup_timeout_sec"], 5)
        shadcn = parsed["mcp_servers"]["shadcn"]
        self.assertEqual(shadcn["startup_timeout_sec"], 90)
        self.assertEqual(shadcn["args"], ["-y", f"shadcn@{PIN}", "mcp"])
        self.assertEqual(third.count("startup_timeout_sec = 90"), 1)
        self.assertEqual(third.count("startup_timeout_sec"), 2)

    def test_missing_shadcn_section_is_noop(self) -> None:
        text = "[mcp_servers.serena]\ncommand = \"/old/serena\"\n"
        updated = rewrite(text)
        parsed = tomllib.loads(updated)
        self.assertNotIn("shadcn", parsed.get("mcp_servers") or {})
        self.assertEqual(parsed["mcp_servers"]["serena"]["command"], SERENA)

    def test_upsert_missing_table_is_noop(self) -> None:
        text = "[other]\nvalue = 1\n"
        self.assertEqual(upsert_table_key(text, "mcp_servers.shadcn", "startup_timeout_sec", "90"), text)

    def test_rewrite_file_writes_once(self) -> None:
        text = "[mcp_servers.shadcn]\ncommand = \"npx\"\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(text, encoding="utf-8")
            self.assertTrue(
                rewrite_file(path, memory_bin=MEMORY, serena_bin=SERENA, shadcn_pin=PIN)
            )
            once = path.read_text(encoding="utf-8")
            self.assertFalse(
                rewrite_file(path, memory_bin=MEMORY, serena_bin=SERENA, shadcn_pin=PIN)
            )
            self.assertEqual(path.read_text(encoding="utf-8"), once)
            tomllib.loads(once)


if __name__ == "__main__":
    unittest.main()
