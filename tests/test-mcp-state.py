#!/usr/bin/env python3
"""MCP policy reconciler fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from mcp_state import evaluate, load_policy, parse_doctor_payload, parse_list_payload  # noqa: E402

FIXTURES = ROOT / "tests/fixtures/mcp"
MEMORY = "/home/user/.grok/runtime/components/codebase-memory/bin/codebase-memory-mcp"
SERENA = "/home/user/.local/bin/serena"


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def codes(report, level: str) -> set[str]:
    return {item.code for item in report.findings if item.level == level}


def main() -> int:
    failed = 0
    policy = load_policy()

    def check(cond: bool, label: str) -> None:
        nonlocal failed
        if cond:
            print("OK  " + label)
        else:
            failed = 1
            print("FAIL " + label, file=sys.stderr)

    healthy = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-healthy.json")),
        doctor=parse_doctor_payload(load("doctor-healthy.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(not healthy.failed, "healthy contract passes")
    check(not healthy.findings, "healthy contract has no warnings")

    override = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-exa-enabled.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(not override.failed, "enabled exa is a warning by default")
    check("MCP_OVERRIDE" in codes(override, "WARN"), "enabled exa emits MCP_OVERRIDE")

    forced = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-exa-enabled.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
        require_disabled=["exa"],
    )
    check(forced.failed, "require-disabled exa fails")
    check("MCP_ENABLED" in codes(forced, "FAIL"), "require-disabled exa emits MCP_ENABLED")

    disabled = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-context7-disabled.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(disabled.failed, "disabled context7 fails")
    check("MCP_DISABLED" in codes(disabled, "FAIL"), "disabled context7 emits MCP_DISABLED")

    wrong = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-wrong-url.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(wrong.failed, "wrong context7 url fails")
    check("MCP_URL" in codes(wrong, "FAIL"), "wrong url emits MCP_URL")

    missing = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-missing.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(missing.failed, "missing servers fail")
    check("MCP_MISSING" in codes(missing, "FAIL"), "missing servers emit MCP_MISSING")

    unhealthy = evaluate(
        policy=policy,
        servers=parse_list_payload(load("list-healthy.json")),
        doctor=parse_doctor_payload(load("doctor-unhealthy.json")),
        memory_bin=MEMORY,
        serena_bin=SERENA,
    )
    check(unhealthy.failed, "unhealthy codebase-memory fails")
    check("MCP_UNHEALTHY" in codes(unhealthy, "FAIL"), "unhealthy emits MCP_UNHEALTHY")

    if failed:
        print("test-mcp-state failed", file=sys.stderr)
        return 1
    print("test-mcp-state passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
