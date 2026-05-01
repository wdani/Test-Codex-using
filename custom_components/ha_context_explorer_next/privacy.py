from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
IPV6_RE = re.compile(r"\b(?=[0-9A-Fa-f:]{3,39}\b)(?=(?:[0-9A-Fa-f]*:){2})[0-9A-Fa-f:]+\b")
DEFAULT_MASK_KEY = "ha_context_explorer_next_default_mask_key"
MASKED_TEXT_PATTERNS = ("email", "ipv4", "ipv6", "mac")
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
        return stable_mask(mask_text(value), prefix)
    if isinstance(value, (int, float, bool)) or value is None:
        return stable_mask(str(value), prefix)
    if isinstance(value, list):
        return [_mask_sensitive_value(v, prefix) for v in value]
    if isinstance(value, dict):
        return {k: _mask_sensitive_value(v, prefix) for k, v in value.items()}
    return stable_mask(str(value), prefix)


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


def build_privacy_status() -> dict[str, Any]:
    return {
        "exports_enabled": has_custom_mask_key(),
        "mask_key": "custom" if has_custom_mask_key() else "missing",
        "masked_text_patterns": list(MASKED_TEXT_PATTERNS),
        "sensitive_key_hints": list(SENSITIVE_KEY_HINTS),
    }
