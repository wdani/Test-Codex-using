from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import re
import secrets
from collections import Counter
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IPV6_RE = re.compile(r"(?<![0-9A-Fa-f:])(?=[0-9A-Fa-f:]{3,39}(?![0-9A-Fa-f:]))(?=(?:[0-9A-Fa-f]*:){2})[0-9A-Fa-f:]+")
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


def generate_mask_key() -> str:
    return secrets.token_urlsafe(32)


def environment_mask_key() -> str | None:
    value = os.getenv("HCX_MASK_KEY")
    if value in {None, "", DEFAULT_MASK_KEY}:
        return None
    return value


def key_fingerprint(mask_key: str | None) -> str | None:
    if not mask_key:
        return None
    return hashlib.sha256(mask_key.encode("utf-8")).hexdigest()[:12]


def _effective_mask_key(mask_key: str | None = None) -> str:
    return mask_key or environment_mask_key() or DEFAULT_MASK_KEY


def _mask_key(mask_key: str | None = None) -> bytes:
    return _effective_mask_key(mask_key).encode("utf-8")


def _is_ipv6(value: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(value), ipaddress.IPv6Address)
    except ValueError:
        return False


def _iter_text_pattern_matches(name: str, regex: re.Pattern[str], value: str) -> list[re.Match[str]]:
    matches = list(regex.finditer(value))
    if name != "ipv6":
        return matches
    return [match for match in matches if _is_ipv6(match.group(0))]


def stable_mask(value: str, prefix: str = "masked", mask_key: str | None = None) -> str:
    digest = hmac.new(_mask_key(mask_key), value.encode("utf-8"), hashlib.sha256).hexdigest()[:10]
    return f"{prefix}_{digest}"


def mask_text(value: str, mask_key: str | None = None) -> str:
    value = EMAIL_RE.sub(lambda m: stable_mask(m.group(0), "email", mask_key), value)
    value = IPV4_RE.sub(lambda m: stable_mask(m.group(0), "ip", mask_key), value)
    value = MAC_RE.sub(lambda m: stable_mask(m.group(0), "mac", mask_key), value)
    value = IPV6_RE.sub(lambda m: stable_mask(m.group(0), "ip6", mask_key) if _is_ipv6(m.group(0)) else m.group(0), value)
    return value


def _text_pattern_counts(value: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    remaining = value
    for name, regex in TEXT_PATTERN_RULES:
        matches = _iter_text_pattern_matches(name, regex, remaining)
        if matches:
            counts[name] += len(matches)
            chars = list(remaining)
            for match in matches:
                chars[match.start() : match.end()] = " " * (match.end() - match.start())
            remaining = "".join(chars)
    return counts


def _mask_exact_text_pattern(value: str, mask_key: str | None = None) -> str | None:
    stripped = value.strip()
    if EMAIL_RE.fullmatch(stripped):
        return stable_mask(stripped, "email", mask_key)
    if IPV4_RE.fullmatch(stripped):
        return stable_mask(stripped, "ip", mask_key)
    if MAC_RE.fullmatch(stripped):
        return stable_mask(stripped, "mac", mask_key)
    if IPV6_RE.fullmatch(stripped) and _is_ipv6(stripped):
        return stable_mask(stripped, "ip6", mask_key)
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


def _mask_sensitive_value(value: Any, prefix: str, mask_key: str | None = None) -> Any:
    if isinstance(value, str):
        return _mask_exact_text_pattern(value, mask_key) or stable_mask(value, prefix, mask_key)
    if isinstance(value, (int, float, bool)) or value is None:
        return stable_mask(str(value), prefix, mask_key)
    if isinstance(value, list):
        return [_mask_sensitive_value(v, prefix, mask_key) for v in value]
    if isinstance(value, dict):
        return {k: _mask_sensitive_value(v, prefix, mask_key) for k, v in value.items()}
    return stable_mask(str(value), prefix, mask_key)


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


def mask_payload(value: Any, mask_key: str | None = None) -> Any:
    if isinstance(value, str):
        return mask_text(value, mask_key)
    if isinstance(value, list):
        return [mask_payload(v, mask_key) for v in value]
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, item in value.items():
            prefix = _mask_prefix_for_key(key)
            masked[key] = _mask_sensitive_value(item, prefix, mask_key) if prefix else mask_payload(item, mask_key)
        return masked
    return value


def has_custom_mask_key(mask_key: str | None = None) -> bool:
    return _effective_mask_key(mask_key) != DEFAULT_MASK_KEY


def build_privacy_status(
    coverage: dict[str, Any] | None = None,
    mask_key: str | None = None,
    key_source: str | None = None,
    key_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    effective_key = _effective_mask_key(mask_key)
    exports_enabled = effective_key != DEFAULT_MASK_KEY
    source = key_source or ("environment" if environment_mask_key() else "missing")
    metadata = key_metadata or {}
    return {
        "exports_enabled": exports_enabled,
        "mask_key": "custom" if exports_enabled else "missing",
        "key_source": source,
        "key_managed": source == "managed_storage",
        "key_fingerprint": key_fingerprint(effective_key) if exports_enabled else None,
        "key_created_at": metadata.get("created_at"),
        "key_rotated_at": metadata.get("rotated_at"),
        "backup_available": exports_enabled,
        "rotation_available": source == "managed_storage",
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
