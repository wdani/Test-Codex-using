from __future__ import annotations

import hashlib
import re

IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")


def stable_mask(value: str, prefix: str = "masked") -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{digest}"


def mask_text(value: str) -> str:
    value = IPV4_RE.sub(lambda m: stable_mask(m.group(0), "ip"), value)
    value = MAC_RE.sub(lambda m: stable_mask(m.group(0), "mac"), value)
    return value
