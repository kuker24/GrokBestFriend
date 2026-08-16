#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

from runtime_policy import PolicyError, apply_text, check_text, load_policy  # noqa: E402


POLICY = load_policy(ROOT / "vendor/runtime-policy.json")
TEMPLATE = (ROOT / "vendor/config/user.toml").read_text(encoding="utf-8")


class RuntimePolicyTests(unittest.TestCase):
    def test_yolo_true_becomes_false_and_keeps_comment(self) -> None:
        text = (
            "# keep this comment\n"
            "[ui]\n"
            "yolo = true\n"
            'permission_mode = "always-approve"\n'
            "max_thoughts_width = 80\n"
        )
        updated = apply_text(text, POLICY, TEMPLATE)
        self.assertIn("# keep this comment", updated)
        parsed = tomllib.loads(updated)
        self.assertIs(parsed["ui"]["yolo"], False)
        self.assertEqual(parsed["ui"]["permission_mode"], "ask")
        self.assertEqual(parsed["ui"]["max_thoughts_width"], 80)

    def test_inserts_missing_yolo_key(self) -> None:
        text = '[ui]\npermission_mode = "ask"\n'
        updated = apply_text(text, POLICY, TEMPLATE)
        parsed = tomllib.loads(updated)
        self.assertIs(parsed["ui"]["yolo"], False)

    def test_marketplace_fixes_official_and_leaves_extra(self) -> None:
        text = (
            "[[marketplace.sources]]\n"
            'name = "xAI Official"\n'
            'git = "https://evil.example/plugin-marketplace.git"\n'
            "\n"
            "[[marketplace.sources]]\n"
            'name = "my-private"\n'
            'git = "https://example.com/private.git"\n'
        )
        updated = apply_text(text, POLICY, TEMPLATE)
        parsed = tomllib.loads(updated)
        sources = parsed["marketplace"]["sources"]
        official = next(item for item in sources if item["name"] == "xAI Official")
        extra = next(item for item in sources if item["name"] == "my-private")
        self.assertEqual(official["git"], "https://github.com/xai-org/plugin-marketplace.git")
        self.assertEqual(extra["git"], "https://example.com/private.git")

    def test_custom_gateway_untouched(self) -> None:
        text = (
            TEMPLATE
            + "\n[models.custom]\n"
            + 'base_url = "https://secret.example/v1"\n'
            + 'api_key = "not-a-real-token"\n'
        )
        updated = apply_text(text, POLICY, TEMPLATE)
        self.assertIn('base_url = "https://secret.example/v1"', updated)
        self.assertIn('api_key = "not-a-real-token"', updated)
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["models"]["custom"]["base_url"], "https://secret.example/v1")
        self.assertIs(parsed["ui"]["yolo"], False)

    def test_empty_uses_template(self) -> None:
        updated = apply_text("", POLICY, TEMPLATE)
        errors = check_text(updated, POLICY)
        self.assertEqual(errors, [])
        parsed = tomllib.loads(updated)
        self.assertIs(parsed["ui"]["yolo"], False)

    def test_duplicate_ui_table_fails_closed(self) -> None:
        text = "[ui]\nyolo = true\n\n[ui]\npermission_mode = \"ask\"\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(text)
            path = Path(handle.name)
        try:
            original = path.read_text(encoding="utf-8")
            with self.assertRaises(PolicyError):
                apply_text(text, POLICY, TEMPLATE)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
        finally:
            path.unlink()

    def test_already_correct_is_noop(self) -> None:
        updated = apply_text(TEMPLATE, POLICY, TEMPLATE)
        self.assertEqual(updated, TEMPLATE)

    def test_check_detects_yolo(self) -> None:
        errors = check_text('[ui]\nyolo = true\npermission_mode = "ask"\n', POLICY)
        self.assertTrue(any("yolo" in item for item in errors))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
