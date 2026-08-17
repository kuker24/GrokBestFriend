"""Load vendor policy and check catalog item fields with the stdlib."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VENDOR_DIR = Path(__file__).resolve().parents[2] / "vendor" / "design-intelligence"


class PolicyError(ValueError):
    pass


def vendor_dir() -> Path:
    return VENDOR_DIR


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_policy(root: Path | None = None) -> dict[str, Any]:
    base = root or VENDOR_DIR
    return load_json(base / "policy.json")


def load_taxonomy(root: Path | None = None) -> dict[str, Any]:
    base = root or VENDOR_DIR
    return load_json(base / "taxonomy.json")


def load_known_sources(root: Path | None = None) -> dict[str, Any]:
    base = root or VENDOR_DIR
    return load_json(base / "known-sources.json")


def known_hash_map(known: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for snap in known.get("snapshots") or []:
        for name, digest in (snap.get("archives") or {}).items():
            out[digest] = str(snap.get("id") or name)
            out[name] = digest
    return out


def snapshot_for_hashes(known: dict[str, Any], hashes: dict[str, str]) -> str | None:
    """Return a snapshot id only when the incoming set equals that snapshot exactly."""
    incoming = {str(name): str(digest) for name, digest in hashes.items()}
    for snap in known.get("snapshots") or []:
        archives = {str(name): str(digest) for name, digest in (snap.get("archives") or {}).items()}
        if not archives:
            continue
        if incoming == archives:
            return str(snap.get("id"))
    return None


def compile_secret_patterns(policy: dict[str, Any]) -> list[re.Pattern[str]]:
    from . import text as text_mod

    return text_mod.compile_secret_patterns(policy)


def check_lock(lock: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(lock, dict):
        return ["lock"]
    if lock.get("schema_version") != 1:
        errors.append("schema_version")
    gid = str(lock.get("generation_id") or "")
    if not re.fullmatch(r"[0-9a-f]{16,64}", gid):
        errors.append("generation_id")
    if not re.fullmatch(r"catalog-[0-9a-f]+\.sqlite3", str(lock.get("sqlite_filename") or "")):
        errors.append("sqlite_filename")
    if not re.fullmatch(r"catalog-[0-9a-f]+\.jsonl", str(lock.get("jsonl_filename") or "")):
        errors.append("jsonl_filename")
    for digest_key in ("sqlite_sha256", "jsonl_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(lock.get(digest_key) or "")):
            errors.append(digest_key)
    if not lock.get("created_at"):
        errors.append("created_at")
    hashes = lock.get("input_hashes")
    if not isinstance(hashes, dict):
        errors.append("input_hashes")
    else:
        for name, digest in hashes.items():
            if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                errors.append(f"input_hashes.{name}")
    return errors


def check_item(item: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    enums = policy.get("enums") or {}

    def need(key: str) -> None:
        if key not in item:
            errors.append(f"missing {key}")

    for key in (
        "schema_version",
        "id",
        "kind",
        "name",
        "description",
        "source",
        "license",
        "trust",
        "evidence_tier",
        "execution_class",
        "style_authority",
        "intent",
        "modes",
        "surfaces",
        "platforms",
        "categories",
        "tags",
        "capabilities_required",
        "provider",
        "search_policy",
        "selection_policy",
        "canonical_id",
        "alias_of",
        "duplicate_of",
        "dedup_reason",
        "untrusted_text",
        "normalization_status",
        "extraction_evidence",
        "warnings",
    ):
        need(key)

    if item.get("schema_version") != 1:
        errors.append("schema_version")

    def enum_ok(key: str, value: Any) -> None:
        allowed = enums.get(key)
        if allowed is None:
            return
        if value not in allowed:
            errors.append(f"{key}={value!r}")

    enum_ok("kind", item.get("kind"))
    enum_ok("trust", item.get("trust"))
    enum_ok("evidence_tier", item.get("evidence_tier"))
    enum_ok("execution_class", item.get("execution_class"))
    enum_ok("style_authority", item.get("style_authority"))
    enum_ok("search_policy", item.get("search_policy"))
    enum_ok("selection_policy", item.get("selection_policy"))
    enum_ok("normalization_status", item.get("normalization_status"))
    if item.get("dedup_reason") is not None:
        enum_ok("dedup_reason", item.get("dedup_reason"))

    source = item.get("source") or {}
    if not isinstance(source, dict):
        errors.append("source")
    else:
        digest = source.get("content_sha256") or ""
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            errors.append("content_sha256")
        path = str(source.get("path") or "")
        if path.startswith("/") or ".." in Path(path).parts:
            errors.append("source.path")

    license_obj = item.get("license") or {}
    if isinstance(license_obj, dict):
        enum_ok("license_status", license_obj.get("status"))
        enum_ok("redistribution", license_obj.get("redistribution"))
    else:
        errors.append("license")

    for key in (
        "intent",
        "modes",
        "surfaces",
        "platforms",
        "categories",
        "tags",
        "capabilities_required",
        "extraction_evidence",
        "warnings",
    ):
        if not isinstance(item.get(key), list):
            errors.append(key)

    if item.get("runtime_availability") is not None or item.get("available_via") is not None:
        errors.append("host_probe_persisted")
    if "execution_status" in item:
        errors.append("execution_status_persisted")

    pointer = item.get("alias_of") or item.get("duplicate_of")
    if pointer and pointer == item.get("id"):
        errors.append("self_pointer")

    from . import text as text_mod

    if text_mod.find_secret_hits(item, policy):
        errors.append("secret_leak")

    return errors
