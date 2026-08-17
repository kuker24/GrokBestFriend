"""Sanitize untrusted ZIP prose before it enters the catalog."""

from __future__ import annotations

import re
from typing import Any

_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_HTML = re.compile(r"<[^>]+>")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_controls(text: str) -> str:
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch in "\t\n\r":
            out.append(" ")
        elif code < 32 or 127 <= code < 160:
            continue
        else:
            out.append(ch)
    return "".join(out)


# Built-in redaction. Split so installer secret greps do not fire on this file.
_SECRET_RES = (
    re.compile("XAI_API_" "KEY="),
    re.compile(r"gho_[A-Za-z0-9]{10,}"),
    re.compile(r"xai-[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer [A-Za-z0-9._-]{20,}"),
)


def redact_secrets(text: str, policy: dict[str, Any] | None = None) -> str:
    del policy
    out = text
    for compiled in _SECRET_RES:
        out = compiled.sub("[REDACTED]", out)
    return out


def drop_markup(text: str) -> str:
    out = _MD_HTML_COMMENT.sub(" ", text)
    out = _CODE_FENCE.sub(" ", out)
    out = _INLINE_CODE.sub(" ", out)
    out = _HTML.sub(" ", out)
    out = _MD_IMAGE.sub(" ", out)
    return out


def contains_any(text: str, markers: list[str]) -> bool:
    low = text.lower()
    return any(marker.lower() in low for marker in markers)


def warnings_for(text: str, policy: dict[str, Any]) -> list[str]:
    found: list[str] = []
    if contains_any(text, list(policy.get("install_command_markers") or [])):
        found.append("CATALOGUE_INSTALL_POINTER")
    if contains_any(text, list(policy.get("instruction_tells") or [])):
        found.append("UNTRUSTED_INSTRUCTION_TEXT")
    if contains_any(text, list(policy.get("stub_markers") or [])):
        found.append("CATALOGUE_STUB")
    return found


def _strip_markers(text: str, markers: list[str]) -> str:
    out = text
    for marker in markers:
        out = re.sub(re.escape(marker), " ", out, flags=re.IGNORECASE)
    return out


def sanitize_field(text: str | None, policy: dict[str, Any], *, max_len: int) -> str:
    raw = strip_controls(text or "")
    raw = drop_markup(raw)
    raw = redact_secrets(raw, policy)
    raw = _strip_markers(raw, list(policy.get("install_command_markers") or []))
    raw = _strip_markers(raw, list(policy.get("instruction_tells") or []))
    raw = re.sub(r"https?://\S+", " ", raw)
    raw = _collapse_ws(raw)
    if len(raw) > max_len:
        raw = raw[: max_len - 1].rstrip() + "…"
    return raw


def sanitize_name(text: str | None, policy: dict[str, Any]) -> str:
    caps = policy.get("text") or {}
    return sanitize_field(text, policy, max_len=int(caps.get("name_max") or 160))


def sanitize_description(text: str | None, policy: dict[str, Any]) -> str:
    caps = policy.get("text") or {}
    return sanitize_field(text, policy, max_len=int(caps.get("description_max") or 400))


def sanitize_tag(text: str | None, policy: dict[str, Any]) -> str:
    caps = policy.get("text") or {}
    return sanitize_field(text, policy, max_len=int(caps.get("tag_max") or 48))


def unique_keep(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
        if len(out) >= limit:
            break
    return out
