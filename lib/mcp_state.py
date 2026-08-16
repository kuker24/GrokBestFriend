#!/usr/bin/env python3
"""Reconcile grok MCP list/doctor JSON against vendor/mcp-policy.json."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "vendor" / "mcp-policy.json"


@dataclass
class Finding:
    level: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.level} {self.code} {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def fail(self, code: str, message: str) -> None:
        self.findings.append(Finding("FAIL", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("WARN", code, message))

    @property
    def failed(self) -> bool:
        return any(item.level == "FAIL" for item in self.findings)

    def print(self, dest=sys.stderr) -> None:
        for item in self.findings:
            prefix = "ERROR: " if item.level == "FAIL" else "WARNING: "
            print(prefix + item.format(), file=dest)


def load_policy(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_POLICY
    data = json.loads(target.read_text(encoding="utf-8"))
    servers = data.get("servers")
    if not isinstance(servers, dict) or not servers:
        raise ValueError(f"invalid MCP policy: {target}")
    return data


def parse_list_payload(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        raw = json.loads(text)
    if raw is None:
        return {}
    servers = raw if isinstance(raw, list) else raw.get("servers") or raw.get("mcp_servers") or []
    if isinstance(servers, dict):
        items = [{"name": name, **(value if isinstance(value, dict) else {})} for name, value in servers.items()]
    else:
        items = servers
    by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("id")
        if name:
            by_name[str(name)] = item
    return by_name


def parse_doctor_payload(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        raw = json.loads(text)
    if not isinstance(raw, dict):
        return {}
    by_name: dict[str, dict[str, Any]] = {}
    for item in raw.get("servers") or []:
        if isinstance(item, dict) and item.get("name"):
            by_name[str(item["name"])] = item
    return by_name


def _enabled(item: dict[str, Any]) -> bool:
    value = item.get("enabled")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return False


def evaluate(
    *,
    policy: dict[str, Any],
    servers: dict[str, dict[str, Any]],
    doctor: dict[str, dict[str, Any]] | None = None,
    memory_bin: str | None = None,
    serena_bin: str | None = None,
    require_disabled: list[str] | None = None,
) -> Report:
    report = Report()
    specs: dict[str, Any] = policy["servers"]

    for name in specs:
        if name not in servers:
            report.fail("MCP_MISSING", f"{name} is not registered")

    for name, spec in specs.items():
        item = servers.get(name)
        if not item:
            continue
        want_enabled = bool(spec.get("enabled"))
        is_enabled = _enabled(item)
        if want_enabled and not is_enabled:
            report.fail("MCP_DISABLED", f"{name} must be enabled")
        elif not want_enabled and is_enabled:
            if require_disabled and name in require_disabled:
                report.fail("MCP_ENABLED", f"{name} must stay disabled")
            else:
                report.warn("MCP_OVERRIDE", f"{name} is enabled (human override)")

        want_url = spec.get("url")
        if want_url and item.get("url") != want_url:
            report.fail("MCP_URL", f"{name} url must be {want_url}")

        want_args = spec.get("args")
        if want_args is not None:
            got_args = item.get("args") or []
            if list(got_args) != list(want_args):
                report.fail("MCP_ARGS", f"{name} args do not match policy")

        want_command = spec.get("command")
        if want_command and want_command != "codebase-memory-bin":
            got_command = item.get("command") or item.get("target")
            if got_command:
                got_name = Path(str(got_command)).name
                if got_name != want_command and str(got_command) != want_command:
                    report.fail("MCP_COMMAND", f"{name} command must be {want_command}")

        if spec.get("command") == "codebase-memory-bin" and memory_bin:
            command = item.get("command") or item.get("target")
            if command and command != memory_bin:
                report.fail("MCP_COMMAND", f"{name} command must be the pinned binary")
        if name == "serena" and serena_bin:
            command = item.get("command") or item.get("target")
            if command and command != serena_bin:
                report.fail("MCP_COMMAND", f"{name} command must be {serena_bin}")

    if doctor is not None:
        for name, spec in specs.items():
            if not spec.get("enabled"):
                continue
            row = doctor.get(name)
            if not row or not row.get("healthy"):
                report.fail("MCP_UNHEALTHY", f"{name} is not healthy")
            target = (row or {}).get("target")
            if name == "context7" and spec.get("url") and target and target != spec["url"]:
                report.fail("MCP_URL", f"{name} doctor target must be {spec['url']}")
            if name == "codebase-memory-mcp" and memory_bin and target and target != memory_bin:
                report.fail("MCP_COMMAND", f"{name} doctor target must be the pinned binary")

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--list-json", default="")
    parser.add_argument("--doctor-json", default="")
    parser.add_argument("--memory-bin", default="")
    parser.add_argument("--serena-bin", default="")
    parser.add_argument(
        "--require-disabled",
        action="append",
        default=[],
        help="Treat an enabled optional server as FAIL instead of WARN",
    )
    args = parser.parse_args()

    policy = load_policy(Path(args.policy))
    list_raw = Path(args.list_json).read_text(encoding="utf-8") if args.list_json else sys.stdin.read()
    try:
        servers = parse_list_payload(list_raw)
    except json.JSONDecodeError:
        print("ERROR: FAIL MCP_LIST mcp list --json is not valid JSON", file=sys.stderr)
        return 1

    doctor = None
    if args.doctor_json:
        try:
            doctor = parse_doctor_payload(Path(args.doctor_json).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("ERROR: FAIL MCP_DOCTOR mcp doctor --json is not valid JSON", file=sys.stderr)
            return 1

    report = evaluate(
        policy=policy,
        servers=servers,
        doctor=doctor,
        memory_bin=args.memory_bin or None,
        serena_bin=args.serena_bin or None,
        require_disabled=args.require_disabled or None,
    )
    for item in report.findings:
        if item.level == "FAIL":
            print("ERROR: FAIL " + item.code + " " + item.message, file=sys.stderr)
        else:
            print("WARNING: " + item.code + " " + item.message, file=sys.stderr)
    if not report.findings:
        print("OK  mcp policy")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
