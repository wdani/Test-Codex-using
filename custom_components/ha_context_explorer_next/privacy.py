from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Any

IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
DEFAULT_MASK_KEY = "ha_context_explorer_next_default_mask_key"


def _mask_key() -> bytes:
    return os.getenv("HCX_MASK_KEY", DEFAULT_MASK_KEY).encode("utf-8")


def stable_mask(value: str, prefix: str = "masked") -> str:
    digest = hmac.new(_mask_key(), value.encode("utf-8"), hashlib.sha256).hexdigest()[:10]
    return f"{prefix}_{digest}"


def mask_text(value: str) -> str:
    value = IPV4_RE.sub(lambda m: stable_mask(m.group(0), "ip"), value)
    value = MAC_RE.sub(lambda m: stable_mask(m.group(0), "mac"), value)
    return value


def mask_payload(value: Any) -> Any:
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, list):
        return [mask_payload(v) for v in value]
    if isinstance(value, dict):
        return {k: mask_payload(v) for k, v in value.items()}
    return value


def has_custom_mask_key() -> bool:
    return os.getenv("HCX_MASK_KEY") not in {None, "", DEFAULT_MASK_KEY}
