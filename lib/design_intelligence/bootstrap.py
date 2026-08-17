"""Transactional Design Intelligence bank bootstrap.

Data-only. Never execute ZIP members, recipes, specialists, stubs, or
community plugins. Does not scan the filesystem for archives.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import stat
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import archive as archive_mod
from . import catalog
from . import doctor as doctor_mod
from . import policy as policy_mod
from . import rank
from . import text as text_mod


ALLOWED_DEGRADED_CHECKS = frozenset({"reference_limitations", "provider_connector"})
NEGATIVE_QUERY = "quantum-banana-xyz"
SEARCH_QUERIES = (
    "developer operations dashboard",
    "editorial technical documentation",
    "expressive AI product landing page",
    "trading analysis dashboard",
)
FAMILY_PATTERNS = {
    "systems": re.compile(r"^design-systems.*\.zip$", re.IGNORECASE),
    "templates": re.compile(r"^design-templates.*\.zip$", re.IGNORECASE),
    "plugins": re.compile(r"^plugins.*\.zip$", re.IGNORECASE),
    "skills": re.compile(r"^skills.*\.zip$", re.IGNORECASE),
}
IMPORT_ORDER = ("systems", "templates", "plugins", "skills")
CATALOG_OVERHEAD_BYTES = 64 * 1024 * 1024
SAFETY_MARGIN = 0.20
GLOB_CHARS = set("*?[]")


class BootstrapError(ValueError):
    def __init__(self, code: str, message: str = "") -> None:
        detail = message or code
        super().__init__(f"{code}: {detail}" if message else code)
        self.code = code
        self.detail = detail


@dataclass
class DiscoveredArchive:
    family: str
    path: Path
    logical_name: str
    sha256: str
    compressed_bytes: int
    uncompressed_bytes: int
    members: int
    blocked: bool
    issues: list[str] = field(default_factory=list)


def new_transaction_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{secrets.token_hex(4)}"


def tilde_display(path: Path, home: Path) -> str:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(home.resolve())
        return f"~/{rel.as_posix()}" if str(rel) != "." else "~"
    except ValueError:
        return resolved.name


def expand_tilde(value: str, home: Path) -> Path:
    if value == "~":
        return home
    if value.startswith("~/"):
        return home / value[2:]
    return Path(value)


def has_control_chars(value: str) -> bool:
    return any(ord(ch) < 32 for ch in value)


def contains_glob(value: str) -> bool:
    return any(ch in GLOB_CHARS for ch in value)


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def is_inside_git_repo(path: Path) -> bool:
    current = path.resolve()
    for parent in (current, *current.parents):
        if (parent / ".git").exists():
            return True
    return False


def default_bank_target(home: Path | None = None, env: dict[str, str] | None = None) -> Path:
    environ = env if env is not None else os.environ
    explicit = (environ.get("GROK_DESIGN_INTELLIGENCE_BANK") or "").strip()
    if explicit:
        if has_control_chars(explicit) or contains_glob(explicit):
            raise BootstrapError("UNSAFE_PATH", "bank target contains control or glob characters")
        return Path(explicit).expanduser()
    root = home if home is not None else Path.home()
    return root / "DesignIntelligence"


def resolve_archive_dir(
    cli_path: str | None,
    env: dict[str, str] | None = None,
) -> str | None:
    """CLI path wins. Environment is used only when the flag requested a bank."""
    if cli_path is not None and str(cli_path).strip():
        return str(cli_path).strip()
    environ = env if env is not None else os.environ
    alt = (environ.get("GROK_DESIGN_INTELLIGENCE_ARCHIVE_DIR") or "").strip()
    return alt or None


def validate_archive_dir(
    raw: str,
    *,
    grok_home: Path,
    bank_target: Path,
    home: Path,
) -> Path:
    if not raw or has_control_chars(raw):
        raise BootstrapError("UNSAFE_PATH", "archive directory has control characters")
    if contains_glob(raw):
        raise BootstrapError("UNRESOLVED_GLOB", "archive directory must not contain glob characters")
    path = Path(raw).expanduser()
    if path.is_symlink():
        raise BootstrapError("UNSAFE_PATH", "archive directory is a symlink")
    if not path.exists():
        raise BootstrapError("ARCHIVE_DIR_MISSING", "archive directory does not exist")
    if not path.is_dir():
        raise BootstrapError("UNSAFE_PATH", "archive path is not a directory")
    if not os.access(path, os.R_OK):
        raise BootstrapError("UNSAFE_PATH", "archive directory is not readable")
    resolved = path.resolve()
    if is_inside(resolved, grok_home):
        raise BootstrapError("UNSAFE_PATH", "archive directory is inside ~/.grok")
    if is_inside(resolved, bank_target):
        raise BootstrapError("UNSAFE_PATH", "archive directory is inside the bank target")
    if is_inside(resolved, home / "DesignIntelligence"):
        raise BootstrapError("UNSAFE_PATH", "archive directory is inside ~/DesignIntelligence")
    return resolved


def discover_archives(directory: Path) -> dict[str, Path]:
    if directory.is_symlink() or not directory.is_dir():
        raise BootstrapError("UNSAFE_PATH", "archive directory is not a regular directory")
    buckets: dict[str, list[Path]] = {family: [] for family in FAMILY_PATTERNS}
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        raise BootstrapError("UNSAFE_PATH", f"cannot read archive directory: {exc}") from exc
    for entry in entries:
        name = entry.name
        if has_control_chars(name):
            raise BootstrapError("UNSAFE_PATH", "archive filename has control characters")
        matched = [family for family, pattern in FAMILY_PATTERNS.items() if pattern.fullmatch(name)]
        if not matched:
            continue
        if len(matched) != 1:
            raise BootstrapError("UNSUPPORTED_ARCHIVE_FAMILY", name)
        if entry.is_symlink():
            raise BootstrapError("UNSAFE_PATH", f"archive is a symlink: {name}")
        if not entry.is_file():
            raise BootstrapError("UNSAFE_PATH", f"archive is not a regular file: {name}")
        buckets[matched[0]].append(entry)

    found: dict[str, Path] = {}
    missing: list[str] = []
    duplicates: list[str] = []
    for family, items in buckets.items():
        if not items:
            missing.append(family)
        elif len(items) > 1:
            duplicates.append(family)
        else:
            found[family] = items[0]
    if missing:
        raise BootstrapError("ARCHIVE_MISSING", ",".join(missing))
    if duplicates:
        raise BootstrapError("DUPLICATE_ARCHIVE_FAMILY", ",".join(duplicates))

    logicals: dict[str, str] = {}
    for family, path in found.items():
        name = archive_mod.logical_name(path)
        if name in logicals:
            raise BootstrapError("DUPLICATE_LOGICAL_NAME", name)
        logicals[name] = family
    return found


def _zip_sizes(path: Path) -> tuple[int, int]:
    compressed = 0
    uncompressed = 0
    try:
        with zipfile.ZipFile(path) as handle:
            for info in handle.infolist():
                if info.is_dir():
                    continue
                compressed += int(info.compress_size)
                uncompressed += int(info.file_size)
    except zipfile.BadZipFile as exc:
        raise BootstrapError("CORRUPT_ZIP", path.name) from exc
    return compressed, uncompressed


def inspect_discovered(
    found: dict[str, Path],
    policy: dict[str, Any],
    taxonomy: dict[str, Any],
) -> list[DiscoveredArchive]:
    rows: list[DiscoveredArchive] = []
    for family in IMPORT_ORDER:
        path = found[family]
        try:
            inspection = archive_mod.inspect_archive(path, policy, taxonomy)
        except archive_mod.ArchiveError as exc:
            raise BootstrapError("CORRUPT_ZIP", str(exc)) from exc
        compressed, uncompressed = _zip_sizes(path)
        issues = [f"{item.code}:{item.path}" if item.path else item.code for item in inspection.issues]
        if any(item.code == "absolute" for item in inspection.issues):
            raise BootstrapError("ABSOLUTE_MEMBER_PATH", path.name)
        if any(item.code == "traversal" for item in inspection.issues):
            raise BootstrapError("PARENT_TRAVERSAL", path.name)
        if any(item.code == "symlink" for item in inspection.issues):
            raise BootstrapError("SYMLINK_MEMBER", path.name)
        if any(item.code == "encrypted" for item in inspection.issues):
            raise BootstrapError("ENCRYPTED_MEMBER", path.name)
        if inspection.family is None:
            raise BootstrapError("UNSUPPORTED_ARCHIVE_FAMILY", path.name)
        if inspection.family != family:
            raise BootstrapError("UNSUPPORTED_ARCHIVE_FAMILY", f"{path.name}:{inspection.family}")
        if inspection.blocked:
            raise BootstrapError("UNSAFE_PATH", ",".join(issues) or path.name)
        rows.append(
            DiscoveredArchive(
                family=family,
                path=path,
                logical_name=inspection.logical_name,
                sha256=inspection.sha256,
                compressed_bytes=compressed,
                uncompressed_bytes=uncompressed,
                members=inspection.members,
                blocked=False,
                issues=issues,
            )
        )
    names = [row.logical_name for row in rows]
    if len(names) != len(set(names)):
        raise BootstrapError("DUPLICATE_LOGICAL_NAME", ",".join(names))
    return rows


def snapshot_record(known: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any] | None:
    incoming = {str(name): str(digest) for name, digest in hashes.items()}
    for snap in known.get("snapshots") or []:
        archives = {str(name): str(digest) for name, digest in (snap.get("archives") or {}).items()}
        if archives and incoming == archives:
            return snap if isinstance(snap, dict) else None
    return None


def require_known_snapshot(rows: list[DiscoveredArchive], known: dict[str, Any]) -> dict[str, Any]:
    hashes = {row.logical_name: row.sha256 for row in rows}
    record = snapshot_record(known, hashes)
    if record is None:
        raise BootstrapError("UNKNOWN_ARCHIVE_SNAPSHOT", "exact known snapshot required")
    return record


def disk_preflight(
    rows: list[DiscoveredArchive],
    *,
    staging_parent: Path,
    target_parent: Path,
) -> dict[str, int]:
    compressed = sum(row.compressed_bytes for row in rows)
    uncompressed = sum(row.uncompressed_bytes for row in rows)
    staging_parent.mkdir(parents=True, exist_ok=True)
    target_parent.mkdir(parents=True, exist_ok=True)
    if os.stat(staging_parent).st_dev != os.stat(target_parent).st_dev:
        raise BootstrapError("INSUFFICIENT_DISK_SPACE", "staging and target are on different filesystems")
    usage = os.statvfs(str(target_parent))
    available = usage.f_bavail * usage.f_frsize
    base = uncompressed + CATALOG_OVERHEAD_BYTES
    required = int(base + base * SAFETY_MARGIN)
    payload = {
        "compressed_bytes": compressed,
        "estimated_uncompressed_bytes": uncompressed,
        "catalog_overhead_estimate": CATALOG_OVERHEAD_BYTES,
        "available_bytes": available,
        "required_bytes": required,
    }
    if available < required:
        raise BootstrapError("INSUFFICIENT_DISK_SPACE", f"need {required} have {available}")
    return payload


def _doctor_payload(
    bank: Path,
    policy: dict[str, Any],
    known: dict[str, Any],
    *,
    claimed_snapshot: str | None = None,
    expected_sha: dict[str, str] | None = None,
    allowlist_path: Path | None = None,
) -> dict[str, Any]:
    return doctor_mod.doctor(
        bank,
        policy,
        known,
        allowlist_path=allowlist_path,
        expected_sha=expected_sha,
        claimed_snapshot=claimed_snapshot,
    )


def classify_doctor(
    report: dict[str, Any],
    *,
    expected_snapshot: str | None = None,
) -> str:
    if not report:
        return "BANK_MISSING"
    if report.get("status") == "BLOCKED":
        return "BANK_BLOCKED"
    checks = {row.get("name"): row for row in report.get("checks") or []}
    if checks.get("bank_root", {}).get("detail") == "missing" or report.get("status") is None:
        return "BANK_MISSING"
    if report.get("status") == "PASS":
        return "BANK_READY_WITH_LIMITATIONS"
    degraded = [row for row in report.get("checks") or [] if row.get("level") == "DEGRADED"]
    unexpected = [row["name"] for row in degraded if row.get("name") not in ALLOWED_DEGRADED_CHECKS]
    snapshot_ok = True
    if expected_snapshot:
        archive = checks.get("archive_hashes") or {}
        snapshot_ok = archive.get("level") == "PASS" and archive.get("detail") == expected_snapshot
    if unexpected or not snapshot_ok:
        return "BANK_DEGRADED"
    return "BANK_READY_WITH_LIMITATIONS"


def evaluate_existing_bank(
    target: Path,
    *,
    policy: dict[str, Any],
    known: dict[str, Any],
    incoming_snapshot: str | None,
    incoming_hashes: dict[str, str] | None,
    allowlist_path: Path | None = None,
) -> dict[str, Any]:
    if target.is_symlink():
        raise BootstrapError("EXISTING_BANK_CONFLICT", "target bank is a symlink")
    if not target.exists():
        return {"action": "create", "reason": None, "doctor": None, "code": "BANK_MISSING"}
    if not target.is_dir():
        raise BootstrapError("EXISTING_BANK_CONFLICT", "target exists and is not a directory")
    report = _doctor_payload(
        target,
        policy,
        known,
        claimed_snapshot=incoming_snapshot,
        expected_sha=incoming_hashes,
        allowlist_path=allowlist_path,
    )
    code = classify_doctor(report, expected_snapshot=incoming_snapshot)
    if code == "BANK_BLOCKED" or code == "BANK_DEGRADED":
        raise BootstrapError("EXISTING_BANK_CONFLICT", code)
    if incoming_snapshot:
        lock = catalog.read_lock(target) or {}
        lock_hashes = {str(k): str(v) for k, v in (lock.get("input_hashes") or {}).items()}
        if incoming_hashes and lock_hashes != incoming_hashes:
            raise BootstrapError("EXISTING_BANK_CONFLICT", "snapshot differs")
        if report.get("status") == "BLOCKED":
            raise BootstrapError("EXISTING_BANK_CONFLICT", "existing bank blocked")
    return {
        "action": "reuse",
        "reason": None,
        "doctor": report,
        "code": code,
        "generation_id": report.get("generation_id"),
        "counts": report.get("counts") or {},
    }


def prepare_staging(home: Path, transaction_id: str, target: Path) -> Path:
    if has_control_chars(transaction_id) or contains_glob(transaction_id) or "/" in transaction_id:
        raise BootstrapError("UNSAFE_PATH", "transaction id is not trusted")
    staging = home / f"DesignIntelligence.stage.{transaction_id}"
    if staging.exists() or staging.is_symlink():
        raise BootstrapError("UNSAFE_PATH", "staging path already exists")
    if is_inside_git_repo(home):
        raise BootstrapError("UNSAFE_PATH", "refusing to stage a bank inside a git repository")
    if is_inside(staging, target):
        raise BootstrapError("UNSAFE_PATH", "staging would sit inside the target bank")
    staging.mkdir(mode=0o700)
    if staging.is_symlink() or not staging.is_dir():
        raise BootstrapError("UNSAFE_PATH", "staging is not a regular directory")
    os.chmod(staging, 0o700)
    return staging


def _security_scan(bank: Path, policy: dict[str, Any], home: Path) -> None:
    items = catalog.load_items(bank, policy)
    secret_ids = [item.get("id") for item in items if text_mod.find_secret_hits(item, policy)]
    if secret_ids:
        raise BootstrapError("SECRET_LEAK", ",".join(str(item) for item in secret_ids[:8]))
    leaked = []
    home_s = str(home.resolve())
    for item in items:
        src = str((item.get("source") or {}).get("path") or "")
        if src.startswith("/"):
            leaked.append(str(item.get("id")))
        blob = json.dumps(item, ensure_ascii=False)
        if home_s in blob or "/home/" in src:
            leaked.append(str(item.get("id")))
    if leaked:
        raise BootstrapError("ABSOLUTE_HOME_PATH_LEAK", ",".join(leaked[:8]))
    dirs = catalog.bank_dirs(bank)
    for path in dirs["normalized"].rglob("*"):
        if not path.is_file():
            continue
        mode = path.stat().st_mode
        if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) and path.suffix != ".zip":
            raise BootstrapError("UNEXPECTED_EXECUTABLE", path.name)
        if path.name == "SKILL.md":
            raise BootstrapError("UNEXPECTED_EXECUTABLE", "extracted SKILL.md")


def _assert_expected_counts(items: list[dict[str, Any]], expected: dict[str, Any]) -> dict[str, int]:
    counts = catalog._counts(items)
    wanted = {
        key: int(expected[key])
        for key in (
            "items",
            "systems",
            "structures",
            "recipes",
            "specialists",
            "aliases",
            "stubs",
            "quarantined",
        )
        if key in expected
    }
    for key, value in wanted.items():
        if int(counts.get(key) or 0) != value:
            raise BootstrapError("COUNT_MISMATCH", f"{key}:{counts.get(key)}!={value}")
    return counts


def _assert_content_classes(items: list[dict[str, Any]]) -> None:
    for item in items:
        execution = item.get("execution_class")
        if execution in {"native-candidate", "adapted-candidate"}:
            raise BootstrapError("COMMUNITY_EXECUTION_POSSIBLE", str(item.get("id")))
        if item.get("kind") == "recipe" and execution not in {"quarantined", "reference-only", "stub"}:
            raise BootstrapError("COMMUNITY_EXECUTION_POSSIBLE", str(item.get("id")))


def import_into_staging(
    staging: Path,
    rows: list[DiscoveredArchive],
    policy: dict[str, Any],
    taxonomy: dict[str, Any],
    known: dict[str, Any],
    snapshot: dict[str, Any],
    *,
    allowlist_path: Path | None = None,
    home: Path,
) -> dict[str, Any]:
    catalog.ensure_bank(staging)
    for row in rows:
        payload = catalog.import_archive(staging, row.path, policy, taxonomy)
        if payload.get("blocked"):
            raise BootstrapError("UNSAFE_PATH", ",".join(payload.get("issues") or [row.logical_name]))
    rebuilt = catalog.rebuild(staging, policy, taxonomy)
    items = catalog.load_items(staging, policy)
    lock = catalog.read_lock(staging)
    if not lock:
        raise BootstrapError("CATALOG_LOCK_INVALID", "missing lock")
    lock_errors = policy_mod.check_lock(lock)
    if lock_errors:
        raise BootstrapError("CATALOG_LOCK_INVALID", ",".join(lock_errors))
    for item in items:
        row_errors = policy_mod.check_item(item, policy)
        if row_errors:
            raise BootstrapError("SCHEMA_INVALID", f"{item.get('id')}:{','.join(row_errors)}")
    expected = snapshot.get("expected_counts") or {}
    counts = _assert_expected_counts(items, expected) if expected else catalog._counts(items)
    _assert_content_classes(items)
    _security_scan(staging, policy, home)
    incoming = {row.logical_name: row.sha256 for row in rows}
    report = _doctor_payload(
        staging,
        policy,
        known,
        claimed_snapshot=str(snapshot.get("id") or ""),
        expected_sha=incoming,
        allowlist_path=allowlist_path,
    )
    if report.get("status") == "BLOCKED":
        raise BootstrapError("BANK_BLOCKED", "doctor blocked staged bank")
    code = classify_doctor(report, expected_snapshot=str(snapshot.get("id") or ""))
    if code not in {"BANK_READY_WITH_LIMITATIONS", "BANK_DEGRADED"} and report.get("status") != "DEGRADED":
        raise BootstrapError("BANK_BLOCKED", code)
    if code == "BANK_DEGRADED":
        unexpected = [
            row.get("name")
            for row in report.get("checks") or []
            if row.get("level") == "DEGRADED" and row.get("name") not in ALLOWED_DEGRADED_CHECKS
        ]
        if unexpected:
            raise BootstrapError("BANK_BLOCKED", ",".join(str(item) for item in unexpected))
    for path, dirs, files in os.walk(staging):
        del dirs
        for name in files:
            full = Path(path) / name
            os.chmod(full, 0o600)
    for path, dirs, files in os.walk(staging, topdown=False):
        del files
        os.chmod(path, 0o700)
    os.chmod(staging, 0o700)
    return {
        "generation_id": rebuilt.get("generation_id") or lock.get("generation_id"),
        "counts": counts,
        "doctor": report,
        "lock": {
            "generation_id": lock.get("generation_id"),
            "jsonl_sha256": lock.get("jsonl_sha256"),
            "sqlite_sha256": lock.get("sqlite_sha256"),
        },
    }


def promote_staging(staging: Path, target: Path) -> Path:
    if target.exists() or target.is_symlink():
        raise BootstrapError("EXISTING_BANK_CONFLICT", "refusing to overwrite target")
    if staging.is_symlink() or not staging.is_dir():
        raise BootstrapError("UNSAFE_PATH", "staging is not a regular directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    if os.stat(staging).st_dev != os.stat(target.parent).st_dev:
        raise BootstrapError("ATOMIC_PROMOTION_FAILURE", "cannot rename across filesystems")
    try:
        os.rename(staging, target)
    except OSError as exc:
        raise BootstrapError("ATOMIC_PROMOTION_FAILURE", str(exc)) from exc
    if target.is_symlink():
        raise BootstrapError("ATOMIC_PROMOTION_FAILURE", "promoted target is a symlink")
    os.chmod(target, 0o700)
    return target


def recover_created_bank(target: Path, recovery: Path) -> dict[str, str]:
    if target.is_symlink():
        raise BootstrapError("UNSAFE_PATH", "refusing to touch a symlink bank")
    if not target.exists():
        return {"action": "none"}
    if recovery.exists() or recovery.is_symlink():
        raise BootstrapError("UNSAFE_PATH", "recovery path already exists")
    recovery.parent.mkdir(parents=True, exist_ok=True)
    os.rename(target, recovery)
    return {"action": "moved"}


def remove_staging(staging: Path) -> None:
    if not staging.exists():
        return
    if staging.is_symlink():
        staging.unlink()
        return
    shutil.rmtree(staging)


def verify_search(
    bank: Path,
    policy: dict[str, Any],
    *,
    allowlist_path: Path | None = None,
) -> dict[str, Any]:
    allowlist = rank.load_allowlist(allowlist_path) if allowlist_path else set()
    queries: list[dict[str, Any]] = []
    for query in SEARCH_QUERIES:
        systems = rank.search_bank(bank, kind="system", query=query, policy=policy, allowlist=allowlist)
        structures = rank.search_bank(bank, kind="structure", query=query, policy=policy, allowlist=allowlist)
        if int(systems.get("packages_loaded_during_search") or 0) != 0:
            raise BootstrapError("SEARCH_PACKAGE_LOAD", query)
        if int(structures.get("packages_loaded_during_search") or 0) != 0:
            raise BootstrapError("SEARCH_PACKAGE_LOAD", query)
        system_hits = systems.get("results") or []
        structure_hits = structures.get("results") or []
        if len(system_hits) > 5 or len(structure_hits) > 3:
            raise BootstrapError("SEARCH_BOUNDS", query)
        if any(float(row.get("score") or 0) <= 0 for row in system_hits + structure_hits):
            raise BootstrapError("ZERO_SCORE_HITS", query)
        queries.append(
            {
                "query": query,
                "systems": len(system_hits),
                "structures": len(structure_hits),
                "packages_loaded_during_search": 0,
            }
        )
    negative = rank.search_bank(bank, kind="system", query=NEGATIVE_QUERY, policy=policy, allowlist=allowlist)
    if negative.get("results"):
        raise BootstrapError("NEGATIVE_QUERY", NEGATIVE_QUERY)
    return {
        "queries": queries,
        "negative": {"query": NEGATIVE_QUERY, "results": []},
        "packages_loaded_during_search": 0,
        "specialists_activated": 0,
        "community_execution": 0,
        "stub_execution": 0,
        "zero_score_hits": 0,
    }


def safe_manifest_fragment(
    *,
    action: str,
    target: Path,
    home: Path,
    snapshot_id: str | None,
    generation_id: str | None,
    counts: dict[str, Any] | None,
    content_status: str,
    archives: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    bank_state = {
        "create": "installed",
        "reuse": "installed",
        "skip": "skipped",
    }.get(action, "missing")
    payload: dict[str, Any] = {
        "engine": "installed",
        "bank": bank_state,
        "path": tilde_display(target, home) if action != "skip" else "~/DesignIntelligence",
        "snapshot": snapshot_id,
        "generationId": generation_id,
        "contentStatus": content_status,
    }
    if counts:
        for key in ("items", "systems", "structures", "recipes", "specialists"):
            if key in counts:
                payload[key] = int(counts[key])
    if archives:
        payload["archives"] = [
            {"logical_name": row["logical_name"], "sha256": row["sha256"]} for row in archives
        ]
    return payload


def preflight(
    *,
    archive_dir: Path,
    target: Path,
    home: Path,
    grok_home: Path,
    policy: dict[str, Any],
    taxonomy: dict[str, Any],
    known: dict[str, Any],
    allowlist_path: Path | None = None,
) -> dict[str, Any]:
    directory = validate_archive_dir(str(archive_dir), grok_home=grok_home, bank_target=target, home=home)
    found = discover_archives(directory)
    rows = inspect_discovered(found, policy, taxonomy)
    snapshot = require_known_snapshot(rows, known)
    disk = disk_preflight(rows, staging_parent=home, target_parent=target.parent)
    existing = evaluate_existing_bank(
        target,
        policy=policy,
        known=known,
        incoming_snapshot=str(snapshot.get("id") or ""),
        incoming_hashes={row.logical_name: row.sha256 for row in rows},
        allowlist_path=allowlist_path,
    )
    return {
        "action": existing["action"],
        "snapshot": snapshot.get("id"),
        "expected_counts": snapshot.get("expected_counts") or {},
        "archives": [
            {
                "family": row.family,
                "logical_name": row.logical_name,
                "sha256": row.sha256,
                "members": row.members,
                "compressed_bytes": row.compressed_bytes,
                "uncompressed_bytes": row.uncompressed_bytes,
            }
            for row in rows
        ],
        "disk": disk,
        "existing": {key: existing[key] for key in existing if key != "doctor"},
        "rows": rows,
        "snapshot_record": snapshot,
    }


def bootstrap(
    *,
    archive_dir: str | Path,
    target: Path | None = None,
    home: Path | None = None,
    grok_home: Path | None = None,
    transaction_id: str | None = None,
    dry_run: bool = False,
    phase: str = "all",
    staging: Path | None = None,
    policy: dict[str, Any] | None = None,
    taxonomy: dict[str, Any] | None = None,
    known: dict[str, Any] | None = None,
    allowlist_path: Path | None = None,
    emit: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    talk = emit or (lambda _line: None)
    home_path = (home or Path.home()).expanduser()
    grok_path = (grok_home or (home_path / ".grok")).expanduser()
    target_path = (target or default_bank_target(home_path)).expanduser()
    policy = policy or policy_mod.load_policy()
    taxonomy = taxonomy or policy_mod.load_taxonomy()
    known = known or policy_mod.load_known_sources()
    allow = allowlist_path or (policy_mod.vendor_dir() / "skill-allowlist.txt")
    tx_id = transaction_id or new_transaction_id()

    if phase == "doctor-status":
        if not target_path.exists():
            return {"code": "BANK_MISSING", "status": "DEGRADED", "bank": tilde_display(target_path, home_path)}
        report = _doctor_payload(target_path, policy, known, allowlist_path=allow)
        code = classify_doctor(report)
        return {
            "code": code,
            "status": report.get("status"),
            "generation_id": report.get("generation_id"),
            "counts": report.get("counts") or {},
            "bank": tilde_display(target_path, home_path),
            "checks": report.get("checks") or [],
        }

    if phase == "recover-created":
        if staging is None:
            raise BootstrapError("UNSAFE_PATH", "recovery path required")
        moved = recover_created_bank(target_path, staging)
        return {"status": "ok", "recovery": tilde_display(staging, home_path), **moved}

    if phase == "remove-staging":
        if staging is None:
            raise BootstrapError("UNSAFE_PATH", "staging path required")
        remove_staging(staging)
        return {"status": "ok"}

    prepared = preflight(
        archive_dir=Path(archive_dir),
        target=target_path,
        home=home_path,
        grok_home=grok_path,
        policy=policy,
        taxonomy=taxonomy,
        known=known,
        allowlist_path=allow,
    )
    action = prepared["action"]
    snapshot_id = str(prepared["snapshot"])
    archives_meta = prepared["archives"]

    if dry_run:
        if action == "reuse":
            talk("WOULD_REUSE_EXISTING_DI_BANK")
        else:
            talk("WOULD_VERIFY_ARCHIVES")
            talk("WOULD_CREATE_DI_STAGING")
            talk("WOULD_IMPORT_4_ARCHIVES")
            talk("WOULD_REBUILD_CATALOG")
            talk("WOULD_RUN_DI_DOCTOR")
            talk("WOULD_PROMOTE_DI_BANK")
        return {
            "status": "dry-run",
            "action": action,
            "snapshot": snapshot_id,
            "archives": archives_meta,
            "disk": prepared["disk"],
            "would": [
                "WOULD_VERIFY_ARCHIVES",
                "WOULD_CREATE_DI_STAGING",
                "WOULD_IMPORT_4_ARCHIVES",
                "WOULD_REBUILD_CATALOG",
                "WOULD_RUN_DI_DOCTOR",
                "WOULD_PROMOTE_DI_BANK",
            ]
            if action == "create"
            else ["WOULD_REUSE_EXISTING_DI_BANK"],
        }

    if phase == "preflight":
        return {
            "status": "ok",
            "action": action,
            "snapshot": snapshot_id,
            "expected_counts": prepared["expected_counts"],
            "archives": archives_meta,
            "disk": prepared["disk"],
            "target": tilde_display(target_path, home_path),
        }

    if action == "reuse":
        existing = prepared["existing"]
        search = verify_search(target_path, policy, allowlist_path=allow) if phase in {"all", "verify-search"} else {}
        return {
            "status": "ok",
            "action": "reuse",
            "install_result": "SUCCESS_WITH_EXPECTED_LIMITATIONS",
            "bank_integrity": "PASS",
            "bank_content_readiness": "DEGRADED",
            "snapshot": snapshot_id,
            "generation_id": existing.get("generation_id"),
            "counts": existing.get("counts") or {},
            "search": search,
            "manifest": safe_manifest_fragment(
                action="reuse",
                target=target_path,
                home=home_path,
                snapshot_id=snapshot_id,
                generation_id=existing.get("generation_id"),
                counts=existing.get("counts") or {},
                content_status="degraded-with-expected-limitations",
                archives=archives_meta,
            ),
        }

    if phase == "existing":
        return {"status": "ok", "action": action, "snapshot": snapshot_id}

    stage_path = staging or prepare_staging(home_path, tx_id, target_path)
    imported: dict[str, Any] = {}
    if phase in {"all", "stage"}:
        try:
            imported = import_into_staging(
                stage_path,
                prepared["rows"],
                policy,
                taxonomy,
                known,
                prepared["snapshot_record"],
                allowlist_path=allow,
                home=home_path,
            )
        except Exception:
            if staging is None:
                remove_staging(stage_path)
            raise
        if phase == "stage":
            return {
                "status": "ok",
                "action": "create",
                "staging": tilde_display(stage_path, home_path),
                "staging_path": str(stage_path),
                "snapshot": snapshot_id,
                "generation_id": imported.get("generation_id"),
                "counts": imported.get("counts") or {},
                "transaction_id": tx_id,
            }

    if phase in {"all", "promote"}:
        promote_staging(stage_path, target_path)

    search = {}
    if phase in {"all", "verify-search"}:
        search = verify_search(target_path, policy, allowlist_path=allow)

    counts = imported.get("counts") if imported else (catalog._counts(catalog.load_items(target_path, policy)))
    generation_id = imported.get("generation_id") if imported else (catalog.read_lock(target_path) or {}).get("generation_id")
    return {
        "status": "ok",
        "action": "create",
        "install_result": "SUCCESS_WITH_EXPECTED_LIMITATIONS",
        "bank_integrity": "PASS",
        "bank_content_readiness": "DEGRADED",
        "snapshot": snapshot_id,
        "generation_id": generation_id,
        "counts": counts,
        "search": search,
        "staging": None,
        "transaction_id": tx_id,
        "target": tilde_display(target_path, home_path),
        "manifest": safe_manifest_fragment(
            action="create",
            target=target_path,
            home=home_path,
            snapshot_id=snapshot_id,
            generation_id=generation_id,
            counts=counts,
            content_status="degraded-with-expected-limitations",
            archives=archives_meta,
        ),
    }
