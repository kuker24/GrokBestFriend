#!/usr/bin/env python3
"""Node engines compare used by installer preflight."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from node_version import (  # noqa: E402
    check_node,
    load_shadcn_requirement,
    meets_minimum,
    parse_minimum,
    parse_version,
)


class NodeVersionTests(unittest.TestCase):
    def test_parse_node_version_strings(self) -> None:
        self.assertEqual(parse_version("v20.18.1"), (20, 18, 1))
        self.assertEqual(parse_version("20.18.1"), (20, 18, 1))
        self.assertEqual(parse_version("v24.18.0"), (24, 18, 0))
        self.assertEqual(parse_version("v20"), (20, 0, 0))
        self.assertIsNone(parse_version(""))
        self.assertIsNone(parse_version("not-a-version"))

    def test_parse_engines_spec(self) -> None:
        self.assertEqual(parse_minimum(">=20.18.1"), (20, 18, 1))
        self.assertEqual(parse_minimum("20.18.1"), (20, 18, 1))

    def test_compare_against_shadcn_floor(self) -> None:
        floor = ">=20.18.1"
        self.assertTrue(meets_minimum("v20.18.1", floor))
        self.assertTrue(meets_minimum("20.18.1", floor))
        self.assertTrue(meets_minimum("v20.19.0", floor))
        self.assertTrue(meets_minimum("v24.18.0", floor))
        self.assertFalse(meets_minimum("v20.18.0", floor))
        self.assertFalse(meets_minimum("v18.20.8", floor))
        self.assertFalse(meets_minimum("v20", floor))
        self.assertFalse(meets_minimum("", floor))
        self.assertFalse(meets_minimum("not-a-version", floor))

    def test_sources_pin_loads(self) -> None:
        pin, minimum = load_shadcn_requirement(ROOT / "vendor/sources.json")
        self.assertEqual(pin, "4.18.0")
        self.assertEqual(minimum, ">=20.18.1")

    def test_check_node_exit_codes(self) -> None:
        self.assertEqual(check_node("v20.18.1", ">=20.18.1", "4.18.0"), 0)
        self.assertEqual(check_node("v18.20.8", ">=20.18.1", "4.18.0"), 1)

    def test_cli_reads_sources_and_fails_old_node(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "lib/node_version.py"),
                "check",
                "--found",
                "v18.20.8",
                "--sources",
                str(ROOT / "vendor/sources.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FAIL NODE_VERSION", proc.stderr)
        self.assertIn("shadcn@4.18.0 requires Node >=20.18.1", proc.stderr)
        self.assertIn("found: v18.20.8", proc.stderr)

    def test_cli_accepts_current_floor(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "lib/node_version.py"),
                "check",
                "--found",
                "v20.18.1",
                "--sources",
                str(ROOT / "vendor/sources.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, "")

    def test_missing_engines_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            path.write_text(
                json.dumps({"sources": {"shadcn": {"version": "4.18.0"}}}),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "lib/node_version.py"),
                    "check",
                    "--found",
                    "v24.0.0",
                    "--sources",
                    str(path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL NODE_VERSION", proc.stderr)


if __name__ == "__main__":
    unittest.main()
