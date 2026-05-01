from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections import Counter
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IPV6_RE = re.compile(r"\b(?=[0-9A-Fa-f:]{3,39}\b)(?=(?:[0-9A-Fa-f]*:){2})[0-9A-Fa-f:]+\b")
DEFAULT_MASK_KEY = "ha_context_explorer_next_default_mask_key"
MASKED_TEXT_PATTERNS = ("email", "ipv4", "ipv6", "mac")
TEXT_PATTERN_RULES = (
    ("email", EMAIL_RE),
    ("ipv4", IPV4_RE),
    ("mac", MAC_RE),
    ("ipv6", IPV6_RE),
)
SENSITIVE_KEY_HINTS = (
    "address",
    "bssid",
    "email",
    "exact_location",
    "friendly_name",
    "gps",
    "host",
    "hostname",
    "ip",
    "ip_address",
    "lat",
    "latitude",
    "lng",
    "lon",
    "longitude",
    "location",
    "mac",
    "name",
    "person",
    "serial",
    "ssid",
    "unique_id",
    "user",
    "username",
    "uuid",
    "zone",
)


def _mask_key() -> bytes:
    return os.getenv("HCX_MASK_KEY", DEFAULT_MASK_KEY).encode("utf-8")


def stable_mask(value: str, prefix: str = "masked") -> str:
    digest = hmac.new(_mask_key(), value.encode("utf-8"), hashlib.sha256).hexdigest()[:10]
    return f"{prefix}_{digest}"


def mask_text(value: str) -> str:
    value = EMAIL_RE.sub(lambda m: stable_mask(m.group(0), "email"), value)
    value = IPV4_RE.sub(lambda m: stable_mask(m.group(0), "ip"), value)
    value = MAC_RE.sub(lambda m: stable_mask(m.group(0), "mac"), value)
    value = IPV6_RE.sub(lambda m: stable_mask(m.group(0), "ip6"), value)
    return value


def _text_pattern_counts(value: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    remaining = value
    for name, regex in TEXT_PATTERN_RULES:
        matches = list(regex.finditer(remaining))
        if matches:
            counts[name] += len(matches)
            chars = list(remaining)
            for match in matches:
                chars[match.start() : match.end()] = " " * (match.end() - match.start())
            remaining = "".join(chars)
    return counts


def _mask_exact_text_pattern(value: str) -> str | None:
    stripped = value.strip()
    if EMAIL_RE.fullmatch(stripped):
        return stable_mask(stripped, "email")
    if IPV4_RE.fullmatch(stripped):
        return stable_mask(stripped, "ip")
    if MAC_RE.fullmatch(stripped):
        return stable_mask(stripped, "mac")
    if IPV6_RE.fullmatch(stripped):
        return stable_mask(stripped, "ip6")
    return None


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _mask_prefix_for_key(key: Any) -> str | None:
    normalized = _normalize_key(key)
    if normalized not in SENSITIVE_KEY_HINTS:
        return None
    if normalized in {"lat", "latitude", "lng", "lon", "longitude", "gps", "location", "exact_location", "address", "zone"}:
        return "location"
    if normalized in {"ip", "ip_address", "host", "hostname"}:
        return "network"
    if normalized in {"mac", "bssid"}:
        return "mac"
    if normalized == "email":
        return "email"
    return "identity"


def _mask_sensitive_value(value: Any, prefix: str) -> Any:
    if isinstance(value, str):
        return _mask_exact_text_pattern(value) or stable_mask(value, prefix)
    if isinstance(value, (int, float, bool)) or value is None:
        return stable_mask(str(value), prefix)
    if isinstance(value, list):
        return [_mask_sensitive_value(v, prefix) for v in value]
    if isinstance(value, dict):
        return {k: _mask_sensitive_value(v, prefix) for k, v in value.items()}
    return stable_mask(str(value), prefix)


def _value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def _scan_attribute_value(
    value: Any,
    *,
    key_counts: dict[str, dict[str, Any]],
    pattern_counts: Counter[str],
) -> bool:
    has_signal = False
    if isinstance(value, dict):
        for key, item in value.items():
            prefix = _mask_prefix_for_key(key)
            if prefix:
                entry = key_counts.setdefault(
                    str(key),
                    {"key": str(key), "prefix": prefix, "count": 0, "value_types": Counter()},
                )
                entry["count"] += 1
                entry["value_types"][_value_type(item)] += 1
                has_signal = True

            has_signal = _scan_attribute_value(item, key_counts=key_counts, pattern_counts=pattern_counts) or has_signal
    elif isinstance(value, list):
        for item in value:
            has_signal = _scan_attribute_value(item, key_counts=key_counts, pattern_counts=pattern_counts) or has_signal
    elif isinstance(value, str):
        counts = _text_pattern_counts(value)
        pattern_counts.update(counts)
        has_signal = bool(counts)
    return has_signal


def build_privacy_coverage(states: list[Any]) -> dict[str, Any]:
    key_counts: dict[str, dict[str, Any]] = {}
    pattern_counts: Counter[str] = Counter()
    entities_with_sensitive_signals = 0

    for state in states:
        entity_has_signal = False
        for value in (
            getattr(state, "entity_id", ""),
            getattr(state, "state", ""),
            getattr(state, "name", ""),
        ):
            if isinstance(value, str):
                counts = _text_pattern_counts(value)
                pattern_counts.update(counts)
                entity_has_signal = entity_has_signal or bool(counts)

        attrs = getattr(state, "attributes", {}) or {}
        entity_has_signal = _scan_attribute_value(
            attrs,
            key_counts=key_counts,
            pattern_counts=pattern_counts,
        ) or entity_has_signal
        if entity_has_signal:
            entities_with_sensitive_signals += 1

    sensitive_key_hits = []
    for entry in key_counts.values():
        sensitive_key_hits.append(
            {
                "key": entry["key"],
                "prefix": entry["prefix"],
                "count": entry["count"],
                "value_types": dict(sorted(entry["value_types"].items())),
            }
        )
    sensitive_key_hits.sort(key=lambda item: (-int(item["count"]), item["key"]))

    pattern_hits = dict(sorted(pattern_counts.items()))
    return {
        "entities_scanned": len(states),
        "entities_with_sensitive_signals": entities_with_sensitive_signals,
        "sensitive_key_hits_total": sum(int(item["count"]) for item in sensitive_key_hits),
        "text_pattern_hits_total": sum(pattern_hits.values()),
        "text_pattern_hits": pattern_hits,
        "sensitive_key_hits": sensitive_key_hits,
    }


def mask_payload(value: Any) -> Any:
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, list):
        return [mask_payload(v) for v in value]
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, item in value.items():
            prefix = _mask_prefix_for_key(key)
            masked[key] = _mask_sensitive_value(item, prefix) if prefix else mask_payload(item)
        return masked
    return value


def has_custom_mask_key() -> bool:
    return os.getenv("HCX_MASK_KEY") not in {None, "", DEFAULT_MASK_KEY}


def build_privacy_status(coverage: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "exports_enabled": has_custom_mask_key(),
        "mask_key": "custom" if has_custom_mask_key() else "missing",
        "masked_text_patterns": list(MASKED_TEXT_PATTERNS),
        "sensitive_key_hints": list(SENSITIVE_KEY_HINTS),
        "coverage": coverage or {
            "entities_scanned": 0,
            "entities_with_sensitive_signals": 0,
            "sensitive_key_hits_total": 0,
            "text_pattern_hits_total": 0,
            "text_pattern_hits": {},
            "sensitive_key_hits": [],
        },
    }
