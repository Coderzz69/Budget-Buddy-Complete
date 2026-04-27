"""Normalization helpers for raw UPI exports."""

from __future__ import annotations

import hashlib
import re


DISPLAY_NAME_RE = re.compile(r"\(([^()]*)\)")
NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")
SPACE_RE = re.compile(r"\s+")


def safe_upper(value: str | None) -> str:
    return (value or "").strip().upper()


def short_hash(value: str | None) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        return ""
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]


def extract_upi_handle(raw_value: str | None) -> str:
    raw = (raw_value or "").strip()
    if not raw:
        return ""
    handle = raw.split("(", 1)[0].strip()
    return handle


def extract_display_name(raw_value: str | None) -> str:
    raw = (raw_value or "").strip()
    if not raw:
        return ""

    match = DISPLAY_NAME_RE.search(raw)
    if match:
        return match.group(1).strip()

    handle = extract_upi_handle(raw)
    if "@" in handle:
        return handle.split("@", 1)[0].strip()
    return handle


def normalize_counterparty(raw_value: str | None) -> str:
    """Produce a stable merchant/counterparty key from noisy UPI strings."""

    base = extract_display_name(raw_value)
    if not base:
        base = extract_upi_handle(raw_value)

    cleaned = safe_upper(base)
    cleaned = NON_ALNUM_RE.sub(" ", cleaned)
    cleaned = SPACE_RE.sub(" ", cleaned).strip()
    return cleaned or "UNKNOWN"
