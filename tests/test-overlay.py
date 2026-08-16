#!/usr/bin/env python3
"""Overlay idempotency and stub replacement."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import overlay  # noqa: E402


def write_skill(dir_path: Path, body: str) -> Path:
    dest = dir_path / "skill"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text(body, encoding="utf-8")
    return dest


def apply(dest: Path, name: str, prepend: Path | None) -> str:
    overlay.apply_skill(dest, name, prepend.read_text(encoding="utf-8") if prepend else None)
    return (dest / "SKILL.md").read_text(encoding="utf-8")


def main() -> int:
    ask_prepend = ROOT / "templates/skill-overlays/ask-matt.prepend.md"
    grill_body = ROOT / "templates/skill-overlays/grill-with-docs.body.md"
    failed = 0

    def check(cond: bool, label: str) -> None:
        nonlocal failed
        if cond:
            print("OK  " + label)
        else:
            failed = 1
            print("FAIL " + label, file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        old_ask = write_skill(
            tmp_path / "old-ask",
            "---\nname: ask-matt\ndisable-model-invocation: true\n---\n"
            "## GrokBuild map\n\nold map one\n\n## GrokBuild map\n\n"
            "Run `/setup-matt-pocock-skills` then `/grill-me`.\n",
        )
        first = apply(old_ask, "ask-matt", ask_prepend)
        second = apply(old_ask, "ask-matt", ask_prepend)
        check(first == second, "ask-matt overlay is idempotent")
        check(first.count("## GrokBuild map") <= 1, "ask-matt has at most one GrokBuild map")
        check("<!-- grokbuild-overlay:ask-matt -->" in first, "ask-matt has overlay marker")
        check("disable-model-invocation" not in first, "ask-matt dropped disable-model-invocation")
        check(first.count("<!-- grokbuild-overlay:ask-matt -->") == 1, "ask-matt marker appears once")

        stub = write_skill(
            tmp_path / "grill-stub",
            "---\nname: grill-with-docs\ndisable-model-invocation: true\n---\n\n"
            "Run a `/grilling` session, using the `/domain-modeling` skill.\n",
        )
        g1 = apply(stub, "grill-with-docs", grill_body)
        g2 = apply(stub, "grill-with-docs", grill_body)
        check(g1 == g2, "grill-with-docs overlay is idempotent")
        check("/grilling" not in g1, "grill-with-docs stub /grilling removed")
        check("/domain-modeling" not in g1, "grill-with-docs stub /domain-modeling removed")
        check("CONTEXT.md" in g1, "grill-with-docs writes CONTEXT.md")
        check("disable-model-invocation" not in g1, "grill-with-docs dropped disable-model-invocation")

        spec = write_skill(
            tmp_path / "spec",
            "---\nname: to-spec\ndisable-model-invocation: true\n---\n\n"
            "The issue tracker and triage label vocabulary should have been provided to you — "
            "run `/setup-matt-pocock-skills` if not.\n\nKeep the template.\n",
        )
        s1 = apply(spec, "to-spec", None)
        s2 = apply(spec, "to-spec", None)
        check(s1 == s2, "to-spec overlay is idempotent")
        check("/setup-matt-pocock-skills" not in s1, "to-spec dropped tracker-setup command")
        check("disable-model-invocation" not in s1, "to-spec dropped disable-model-invocation")

        live = tmp_path / "vendor-ask"
        shutil.copytree(ROOT / "vendor/skills/ask-matt", live)
        v1 = apply(live, "ask-matt", ask_prepend)
        v2 = apply(live, "ask-matt", ask_prepend)
        check(v1 == v2, "vendor ask-matt stays stable across overlay")
        check(v1.count("# Ask Matt") == 1, "vendor ask-matt keeps a single heading")

        browser = tmp_path / "browser"
        shutil.copytree(ROOT / "vendor/skills/browser-act", browser)
        # Restore a pre-overlay-shaped file from git semantics: body must survive.
        b1 = apply(browser, "browser-act", ROOT / "templates/skill-overlays/browser-act.prepend.md")
        b2 = apply(browser, "browser-act", ROOT / "templates/skill-overlays/browser-act.prepend.md")
        check(b1 == b2, "browser-act overlay is idempotent")
        check(b1.count("# browser-act") == 1, "browser-act keeps its usage body")
        check(b1.count("## GrokBuild browser contract") == 1, "browser-act contract appears once")

    if failed:
        print("test-overlay failed", file=sys.stderr)
        return 1
    print("test-overlay passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
