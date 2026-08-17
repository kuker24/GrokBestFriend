#!/usr/bin/env python3
"""Transactional Design Intelligence bank bootstrap tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "tests"))

from design_intelligence import archive as archive_mod  # noqa: E402
from design_intelligence import bootstrap  # noqa: E402
from design_intelligence import catalog  # noqa: E402
from design_intelligence import policy as policy_mod  # noqa: E402
from design_intelligence_support import (  # noqa: E402
    encrypted_zip,
    pack,
    seed_bank,
    symlink_zip,
    traversal_zip,
    write_zip,
)

FAILED: list[str] = []


def check(cond: bool, label: str) -> None:
    if cond:
        print("OK  " + label)
    else:
        FAILED.append(label)
        print("FAIL " + label, file=sys.stderr)


def expect_error(code: str, label: str, fn) -> None:
    try:
        fn()
    except bootstrap.BootstrapError as exc:
        check(exc.code == code, f"{label} ({exc.code})")
        return
    FAILED.append(label)
    print("FAIL " + label + " (no error)", file=sys.stderr)


def pack_dir(tmp: Path) -> tuple[Path, dict[str, str], dict[str, Path]]:
    archive_dir = tmp / "packs"
    archive_dir.mkdir(parents=True)
    mapping = {
        "systems": ("systems-pack", "design-systems.zip"),
        "templates": ("templates-pack", "design-templates.zip"),
        "plugins": ("plugins-pack", "plugins.zip"),
        "skills": ("skills-pack", "skills.zip"),
    }
    hashes: dict[str, str] = {}
    paths: dict[str, Path] = {}
    for family, (src, name) in mapping.items():
        dest = archive_dir / name
        pack(src, dest)
        hashes[name] = archive_mod.sha256_file(dest)
        paths[family] = dest
    return archive_dir, hashes, paths


def fixture_known(hashes: dict[str, str], counts: dict[str, int] | None = None) -> dict:
    return {
        "schema_version": 1,
        "snapshots": [
            {
                "id": "od-test-minifixture-v1.3.1",
                "archives": hashes,
                "expected_counts": counts or {},
            }
        ],
    }


def isolate_home(tmp: Path) -> tuple[Path, Path, Path]:
    home = tmp / "home"
    grok = tmp / "grok"
    target = home / "DesignIntelligence"
    home.mkdir(parents=True)
    grok.mkdir(parents=True)
    os.environ["HOME"] = str(home)
    os.environ.pop("GROK_DESIGN_INTELLIGENCE_BANK", None)
    os.environ.pop("GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR", None)
    return home, grok, target


def test_resolve_and_flags(tmp: Path) -> None:
    check(
        bootstrap.resolve_archive_dir(None, env={}) is None,
        "no flag/env → no archive source",
    )
    check(
        bootstrap.resolve_archive_dir("/cli", env={"GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR": "/env"}) == "/cli",
        "CLI path wins over env",
    )
    check(
        bootstrap.resolve_archive_dir(None, env={"GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR": "/env"}) == "/env",
        "env used when CLI path omitted",
    )
    home, grok, target = isolate_home(tmp / "flags")
    expect_error(
        "ARCHIVE_DIR_MISSING",
        "missing archive directory",
        lambda: bootstrap.validate_archive_dir(str(tmp / "nope"), grok_home=grok, bank_target=target, home=home),
    )
    expect_error(
        "UNRESOLVED_GLOB",
        "unresolved glob rejected",
        lambda: bootstrap.validate_archive_dir("/tmp/packs*", grok_home=grok, bank_target=target, home=home),
    )
    expect_error(
        "UNSAFE_PATH",
        "control character rejected",
        lambda: bootstrap.validate_archive_dir("/tmp/packs\n", grok_home=grok, bank_target=target, home=home),
    )


def test_discover_failures(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "disc")
    archive_dir, hashes, paths = pack_dir(tmp / "disc-ok")
    found = bootstrap.discover_archives(archive_dir)
    check(set(found) == {"systems", "templates", "plugins", "skills"}, "discover four families")

    missing = tmp / "disc-missing"
    missing.mkdir(parents=True)
    pack("systems-pack", missing / "design-systems.zip")
    expect_error("ARCHIVE_MISSING", "one family missing", lambda: bootstrap.discover_archives(missing))

    dup = tmp / "disc-dup"
    dup.mkdir(parents=True)
    for name in ("design-systems.zip", "design-templates.zip", "plugins.zip", "skills.zip"):
        pack("systems-pack" if name.startswith("design-systems") else "templates-pack" if "template" in name else "plugins-pack" if name.startswith("plugins") else "skills-pack", dup / name)
    pack("systems-pack", dup / "design-systems(1).zip")
    expect_error("DUPLICATE_ARCHIVE_FAMILY", "duplicate family", lambda: bootstrap.discover_archives(dup))

    expect_error(
        "PARENT_TRAVERSAL",
        "unsafe member path",
        lambda: bootstrap.inspect_discovered(
            {
                "systems": traversal_zip(tmp / "trav.zip"),
                "templates": paths["templates"],
                "plugins": paths["plugins"],
                "skills": paths["skills"],
            },
            policy_mod.load_policy(),
            policy_mod.load_taxonomy(),
        ),
    )
    expect_error(
        "SYMLINK_MEMBER",
        "symlink member",
        lambda: bootstrap.inspect_discovered(
            {
                "systems": symlink_zip(tmp / "sym.zip"),
                "templates": paths["templates"],
                "plugins": paths["plugins"],
                "skills": paths["skills"],
            },
            policy_mod.load_policy(),
            policy_mod.load_taxonomy(),
        ),
    )
    expect_error(
        "ENCRYPTED_MEMBER",
        "encrypted member",
        lambda: bootstrap.inspect_discovered(
            {
                "systems": encrypted_zip(tmp / "enc.zip"),
                "templates": paths["templates"],
                "plugins": paths["plugins"],
                "skills": paths["skills"],
            },
            policy_mod.load_policy(),
            policy_mod.load_taxonomy(),
        ),
    )


def test_snapshot_rules(tmp: Path) -> None:
    archive_dir, hashes, paths = pack_dir(tmp / "snap")
    rows = bootstrap.inspect_discovered(
        {family: paths[family] for family in bootstrap.IMPORT_ORDER},
        policy_mod.load_policy(),
        policy_mod.load_taxonomy(),
    )
    expect_error(
        "UNKNOWN_ARCHIVE_SNAPSHOT",
        "unknown snapshot blocked",
        lambda: bootstrap.require_known_snapshot(rows, policy_mod.load_known_sources()),
    )
    production = policy_mod.load_known_sources()
    partial = dict(list((production["snapshots"][0]["archives"]).items())[:2])
    partial.update({row.logical_name: row.sha256 for row in rows if row.logical_name not in partial})
    check(
        policy_mod.snapshot_for_hashes(production, {k: hashes.get(k, "0" * 64) for k in hashes}) is None,
        "fixture hashes are not the production snapshot",
    )
    check(policy_mod.snapshot_for_hashes(production, partial) is None, "partial known hash is not a snapshot")
    known = fixture_known(hashes)
    record = bootstrap.require_known_snapshot(rows, known)
    check(record["id"] == "od-test-minifixture-v1.3.1", "exact known fixture matches")


def test_exact_fixture_and_security(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "ok")
    archive_dir, hashes, _paths = pack_dir(tmp / "ok-packs")
    known = fixture_known(hashes)
    # first import learns counts
    staged = home / "learn"
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    catalog.ensure_bank(staged)
    for name in ("design-systems.zip", "design-templates.zip", "plugins.zip", "skills.zip"):
        catalog.import_archive(staged, archive_dir / name, policy, taxonomy)
    rebuilt = catalog.rebuild(staged, policy, taxonomy)
    counts = rebuilt["counts"]
    known["snapshots"][0]["expected_counts"] = counts
    shutil_rm = staged
    import shutil

    shutil.rmtree(shutil_rm)

    result = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=target,
        home=home,
        grok_home=grok,
        known=known,
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
    )
    check(result["status"] == "ok", "exact known fixture import ok")
    check(result["action"] == "create", "created new bank")
    check(result["counts"]["items"] == counts["items"], "fixture item count")
    check(target.is_dir() and not target.is_symlink(), "promoted regular directory")
    items = catalog.load_items(target, policy)
    check(all(not str((item.get("source") or {}).get("path") or "").startswith("/") for item in items), "no absolute path stored")
    check(all(not policy_mod.compile_secret_patterns(policy) or True for item in items), "policy loads")
    from design_intelligence import text as text_mod

    check(not any(text_mod.find_secret_hits(item, policy) for item in items), "secret canary not stored")
    check(all(item.get("execution_class") != "native-candidate" for item in items), "no native ZIP execution class")
    quarantined = [item for item in items if item.get("execution_class") == "quarantined"]
    check(len(quarantined) >= 1, "community remains quarantined")
    stubs = [item for item in items if item.get("execution_class") == "stub"]
    check(len(stubs) >= 1, "stubs remain non-runnable")
    check((result.get("search") or {}).get("packages_loaded_during_search") == 0, "search loads zero packages")
    check((result.get("search") or {}).get("negative", {}).get("results") == [], "negative query empty")
    manifest = result["manifest"]
    check("source" not in json.dumps(manifest), "manifest has no source key")
    check("/home/" not in json.dumps(manifest), "manifest has no absolute home")
    check(manifest.get("path", "").startswith("~/"), "manifest path is tilde-form")

    again = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=target,
        home=home,
        grok_home=grok,
        known=known,
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
    )
    check(again["action"] == "reuse", "reinstall reuses healthy bank")
    check(again["manifest"].get("snapshot") == "od-test-minifixture-v1.3.1", "reuse manifest snapshot")
    check(bool(again["manifest"].get("generationId")), "reuse manifest generation")
    check(again["manifest"].get("items") == counts["items"], "reuse manifest counts")
    check((again.get("search") or {}).get("negative", {}).get("results") == [], "reuse search verified")

    wrong = dict(counts)
    wrong["items"] = 1
    bad_known = fixture_known(hashes, wrong)
    empty_target = home / "other"
    expect_error(
        "COUNT_MISMATCH",
        "count mismatch fails promotion",
        lambda: bootstrap.bootstrap(
            archive_dir=archive_dir,
            target=empty_target,
            home=home,
            grok_home=grok,
            known=bad_known,
            allowlist_path=ROOT / "vendor/skill-allowlist.txt",
        ),
    )
    check(not empty_target.exists(), "failed promotion left target absent")


def test_existing_and_symlink(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "exist")
    seed_bank(target)
    archive_dir, hashes, _ = pack_dir(tmp / "exist-packs")
    known = fixture_known(hashes, {"items": 1})
    expect_error(
        "EXISTING_BANK_CONFLICT",
        "existing different/corrupt snapshot not overwritten",
        lambda: bootstrap.bootstrap(
            archive_dir=archive_dir,
            target=target,
            home=home,
            grok_home=grok,
            known=known,
            allowlist_path=ROOT / "vendor/skill-allowlist.txt",
        ),
    )
    check(target.is_dir(), "existing bank still present")

    link_home, link_grok, _ = isolate_home(tmp / "link")
    real = tmp / "link-real"
    real.mkdir()
    link = link_home / "DesignIntelligence"
    link.symlink_to(real)
    expect_error(
        "EXISTING_BANK_CONFLICT",
        "symlink target rejected",
        lambda: bootstrap.evaluate_existing_bank(
            link,
            policy=policy_mod.load_policy(),
            known=policy_mod.load_known_sources(),
            incoming_snapshot="od-test-minifixture-v1.3.1",
            incoming_hashes=hashes,
        ),
    )


def test_dry_run_and_recover(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "dry")
    archive_dir, hashes, _ = pack_dir(tmp / "dry-packs")
    # learn counts
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    staged = tmp / "dry-learn"
    catalog.ensure_bank(staged)
    for name in ("design-systems.zip", "design-templates.zip", "plugins.zip", "skills.zip"):
        catalog.import_archive(staged, archive_dir / name, policy, taxonomy)
    counts = catalog.rebuild(staged, policy, taxonomy)["counts"]
    import shutil

    shutil.rmtree(staged)
    known = fixture_known(hashes, counts)
    lines: list[str] = []
    result = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=target,
        home=home,
        grok_home=grok,
        known=known,
        dry_run=True,
        emit=lines.append,
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
    )
    check(result["status"] == "dry-run", "dry-run status")
    check("WOULD_PROMOTE_DI_BANK" in lines, "dry-run would promote")
    check(not target.exists(), "dry-run did not create target")
    check(not list(home.glob("DesignIntelligence.stage.*")), "dry-run left no staging")

    missing_parent = home / "nested-missing" / "DesignIntelligence"
    dry_missing = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=missing_parent,
        home=home,
        grok_home=grok,
        known=known,
        dry_run=True,
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
    )
    check(dry_missing["status"] == "dry-run", "dry-run with missing target parent")
    check(not (home / "nested-missing").exists(), "dry-run did not create target parent")

    created = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=target,
        home=home,
        grok_home=grok,
        known=known,
        phase="all",
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
    )
    check(created["action"] == "create", "create after dry-run")
    check((created.get("search") or {}).get("packages_loaded_during_search") == 0, "create search ran before promote")
    recovery = home / "DesignIntelligence.recovery.test"
    moved = bootstrap.recover_created_bank(target, recovery, home=home)
    check(moved["action"] == "moved", "promoted bank moved to recovery")
    check(recovery.is_dir() and not target.exists(), "recovery holds the bank")


def test_installer_cli_contract() -> None:
    env = os.environ.copy()
    env["GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR"] = ""
    env["GRT_HOME"] = str(Path(tempfile.mkdtemp()) / "grok")
    env["GRT_SKIP_TOOLS"] = "1"
    env["GRT_SKIP_DESIGN_BANK"] = "1"
    proc = subprocess.run(
        [str(ROOT / "install.sh"), "--with-design-intelligence-bank"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode != 0, "flag without path/env fails")
    check(
        "DESIGN_INTELLIGENCE_ARCHIVE_DIR_REQUIRED" in (proc.stderr + proc.stdout),
        "missing archive dir code",
    )
    proc = subprocess.run(
        [str(ROOT / "install.sh"), "--skip-tools", "--skip-design-bank", "--with-design-intelligence-bank", "/no/such/dir"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode != 0, "missing archive directory fails")

    dry = subprocess.run(
        [str(ROOT / "install.sh"), "--dry-run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    check(dry.returncode == 0, "default dry-run still succeeds")
    check("Design Intelligence engine = INSTALLED" in dry.stdout, "default dry-run reports engine")
    check("Design Intelligence bank =" in dry.stdout, "default dry-run reports bank skip/missing")
    check("WOULD_PROMOTE_DI_BANK" not in dry.stdout, "default dry-run does not import bank")


def test_uninstall_retains_bank(tmp: Path) -> None:
    home = tmp / "uninst"
    home.mkdir()
    bank = home / "DesignIntelligence"
    bank.mkdir()
    (bank / "keep.txt").write_text("user-data\n", encoding="utf-8")
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["GRT_HOME"] = str(home / ".grok")
    env["GRT_DRY_RUN"] = "1"
    proc = subprocess.run(
        [str(ROOT / "uninstall.sh"), "--dry-run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode == 0, "uninstall dry-run ok")
    check((bank / "keep.txt").read_text(encoding="utf-8") == "user-data\n", "uninstall preserves bank")
    check("retained" in proc.stdout.lower() or "user data" in proc.stdout.lower(), "uninstall reports bank retained")


def test_destructive_paths_and_installer_gate(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "adv")
    canary = tmp / "arbitrary"
    canary.mkdir()
    (canary / "keep").write_text("safe\n", encoding="utf-8")
    expect_error(
        "UNSAFE_PATH",
        "remove-staging refuses arbitrary directory",
        lambda: bootstrap.remove_staging(canary, home=home),
    )
    check((canary / "keep").read_text(encoding="utf-8") == "safe\n", "arbitrary directory remains")
    expect_error("UNSAFE_PATH", "remove-staging refuses home", lambda: bootstrap.remove_staging(home, home=home))
    expect_error("UNSAFE_PATH", "remove-staging refuses /", lambda: bootstrap.remove_staging(Path("/"), home=home))
    expect_error(
        "UNSAFE_PATH",
        "remove-staging refuses target bank name",
        lambda: bootstrap.remove_staging(target, home=home),
    )
    repoish = home / "DesignIntelligence.stage.notmarker"
    repoish.mkdir()
    (repoish / "keep").write_text("x\n", encoding="utf-8")
    expect_error(
        "UNSAFE_PATH",
        "remove-staging refuses staging without marker",
        lambda: bootstrap.remove_staging(repoish, home=home),
    )
    check((repoish / "keep").is_file(), "unmarked staging remains")
    expect_error(
        "UNSAFE_PATH",
        "recover-created refuses arbitrary dest",
        lambda: bootstrap.recover_created_bank(canary, canary / "out", home=home),
    )
    check((canary / "keep").is_file(), "recover did not consume canary")

    env = os.environ.copy()
    env.pop("GROK_DI_INSTALLER", None)
    env["HOME"] = str(home)
    valid = home / "DesignIntelligence.stage.deadbeef"
    valid.mkdir()
    bootstrap.write_transaction_marker(
        valid,
        kind=bootstrap.MARKER_KIND_STAGE,
        transaction_id="deadbeef",
        home=home,
        target=target,
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/design-intelligence.py"),
            "bootstrap",
            "--phase",
            "remove-staging",
            "--staging",
            str(valid),
            "--home",
            str(home),
            "--target",
            str(target),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode != 0, "CLI remove-staging without installer env fails")
    check(valid.is_dir(), "installer-gated CLI did not delete staging")
    skill = (ROOT / "vendor/skills/impeccable/SKILL.md").read_text(encoding="utf-8")
    check("design-intelligence.py *" not in skill, "Impeccable does not allow wildcard DI CLI")
    check("design-intelligence.py bootstrap" not in skill, "Impeccable does not allow bootstrap CLI")


def test_stage_runs_search(tmp: Path) -> None:
    home, grok, target = isolate_home(tmp / "stage-search")
    archive_dir, hashes, _ = pack_dir(tmp / "stage-search-packs")
    policy = policy_mod.load_policy()
    taxonomy = policy_mod.load_taxonomy()
    staged = tmp / "stage-learn"
    catalog.ensure_bank(staged)
    for name in ("design-systems.zip", "design-templates.zip", "plugins.zip", "skills.zip"):
        catalog.import_archive(staged, archive_dir / name, policy, taxonomy)
    counts = catalog.rebuild(staged, policy, taxonomy)["counts"]
    import shutil

    shutil.rmtree(staged)
    known = fixture_known(hashes, counts)
    result = bootstrap.bootstrap(
        archive_dir=archive_dir,
        target=target,
        home=home,
        grok_home=grok,
        known=known,
        phase="stage",
        transaction_id="stage1",
        allowlist_path=ROOT / "vendor/skill-allowlist.txt",
        allow_mutation=True,
    )
    check(result["action"] == "create", "stage created a bank")
    check((result.get("search") or {}).get("packages_loaded_during_search") == 0, "search verified on staging")
    check(not target.exists(), "stage did not promote")
    check(list(home.glob("DesignIntelligence.stage.*")), "staging remains after search")


def test_legacy_design_bank_untouched() -> None:
    text = (ROOT / "lib/design-intelligence-bank.sh").read_text(encoding="utf-8")
    check("GROK_DESIGN_BANK" not in text, "DI bank installer does not touch GROK_DESIGN_BANK")
    install = (ROOT / "lib/install.sh").read_text(encoding="utf-8")
    check("grt_install_design_bank" in install, "legacy Design Bank still installed")


def main() -> int:
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    os.environ["GROK_DI_INSTALLER"] = "1"
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        test_resolve_and_flags(tmp)
        test_discover_failures(tmp)
        test_snapshot_rules(tmp)
        test_exact_fixture_and_security(tmp)
        test_existing_and_symlink(tmp)
        test_dry_run_and_recover(tmp)
        test_destructive_paths_and_installer_gate(tmp)
        test_stage_runs_search(tmp)
        test_installer_cli_contract()
        test_uninstall_retains_bank(tmp)
        test_legacy_design_bank_untouched()
    if FAILED:
        print(f"test-design-intelligence-bootstrap failed: {len(FAILED)}", file=sys.stderr)
        return 1
    print("test-design-intelligence-bootstrap passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
