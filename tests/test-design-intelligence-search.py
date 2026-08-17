#!/usr/bin/env python3
"""Search eligibility, bounds, and determinism."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import catalog  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence import rank  # noqa: E402
from design_intelligence_support import seed_bank  # noqa: E402


def check(cond: bool, label: str, failed: list[str]) -> None:
    if cond:
        print("OK  " + label)
    else:
        failed.append(label)
        print("FAIL " + label, file=sys.stderr)


def main() -> int:
    failed: list[str] = []
    os.environ["HOME"] = tempfile.mkdtemp()
    policy = policy_mod.load_policy()
    with tempfile.TemporaryDirectory() as tmp:
        bank = seed_bank(Path(tmp) / "bank")
        items = catalog.load_items(bank)
        allowlist = {"emil-design-eng"}

        systems = rank.search(
            items, kind="system", query="marketplace coral brand", policy=policy, allowlist=allowlist
        )
        check(systems["packages_loaded_during_search"] == 0, "no full package load", failed)
        check(len(systems["results"]) <= 5, "systems <= 5", failed)
        ids = [row["id"] for row in systems["results"]]
        check(all(not any(item["id"] == rid and (item.get("alias_of") or item.get("duplicate_of")) for item in items) for rid in ids),
              "aliases absent from default results", failed)
        check(any(row["id"] == "system:brandco" for row in systems["results"]), "local-only inspiration system is eligible", failed)

        structures = rank.search(
            items, kind="structure", query="dashboard sidebar kpi", policy=policy, allowlist=allowlist
        )
        check(len(structures["results"]) <= 3, "structures <= 3", failed)
        check(any(row["id"] == "structure:dashboard" for row in structures["results"]), "dashboard structure found", failed)

        recipes = rank.search(items, kind="recipe", query="community evil", policy=policy, allowlist=allowlist)
        check(all(row["id"] != "recipe:community-evil" for row in recipes["results"]), "community not in default results", failed)

        specialists = rank.search(
            items, kind="specialist", query="creative director", policy=policy, allowlist=allowlist
        )
        check(specialists["results"] == [], "unavailable specialist not selected", failed)
        inspection = rank.search(
            items,
            kind="specialist",
            query="creative director",
            policy=policy,
            allowlist=allowlist,
            include_unavailable=True,
        )
        check(any(row["id"] == "specialist:creative-director" for row in inspection["results"]),
              "stub visible only with include-unavailable", failed)
        check(all(row["execution_status"] != "native" for row in inspection["results"]),
              "ZIP specialists are not native", failed)

        again = rank.search(
            items, kind="system", query="marketplace coral brand", policy=policy, allowlist=allowlist
        )
        check([row["id"] for row in again["results"]] == [row["id"] for row in systems["results"]],
              "same ranking", failed)
        check(all(row["score"] > 0 for row in systems["results"]), "positive scores only", failed)

        miss = rank.search(
            items, kind="system", query="quantum-banana-xyz", policy=policy, allowlist=allowlist
        )
        check(miss["results"] == [], "no-match → results=[]", failed)
        empty = rank.search(items, kind="system", query="   ", policy=policy, allowlist=allowlist)
        check(empty["results"] == [], "empty query → results=[]", failed)

        # diversity: two systems share no category with query tokens still bounded
        check(len({row["id"] for row in systems["results"]}) == len(systems["results"]), "unique hits", failed)

    if failed:
        print(f"test-design-intelligence-search failed: {len(failed)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-search passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
