from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .privacy import environment_mask_key, generate_mask_key, key_fingerprint

STORAGE_KEY = f"{DOMAIN}.privacy_key"
STORAGE_VERSION = 1
STATE_KEY = "privacy_key_record"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _new_record(previous_fingerprint: str | None = None) -> dict[str, Any]:
    now = _now()
    return {
        "version": STORAGE_VERSION,
        "key": generate_mask_key(),
        "created_at": now,
        "rotated_at": now if previous_fingerprint else None,
        "previous_fingerprint": previous_fingerprint,
    }


def _store(hass: HomeAssistant) -> Store[dict[str, Any]]:
    return Store(hass, STORAGE_VERSION, STORAGE_KEY)


async def async_load_or_create_privacy_key(hass: HomeAssistant) -> dict[str, Any]:
    state = hass.data.setdefault(DOMAIN, {})
    if STATE_KEY in state:
        return state[STATE_KEY]

    store = _store(hass)
    record = await store.async_load()
    if not isinstance(record, dict) or not record.get("key"):
        record = _new_record()
        await store.async_save(record)

    state[STATE_KEY] = record
    return record


async def async_get_privacy_key_context(hass: HomeAssistant) -> dict[str, Any]:
    env_key = environment_mask_key()
    if env_key:
        return {
            "mask_key": env_key,
            "key_source": "environment",
            "key_metadata": {},
        }

    record = await async_load_or_create_privacy_key(hass)
    return {
        "mask_key": record["key"],
        "key_source": "managed_storage",
        "key_metadata": {
            "created_at": record.get("created_at"),
            "rotated_at": record.get("rotated_at"),
            "previous_fingerprint": record.get("previous_fingerprint"),
        },
    }


async def async_build_privacy_key_backup(hass: HomeAssistant) -> dict[str, Any]:
    context = await async_get_privacy_key_context(hass)
    mask_key = context["mask_key"]
    return {
        "schema_version": "1.0.0",
        "product": DOMAIN,
        "type": "mask_key_backup",
        "exported_at": _now(),
        "key_source": context["key_source"],
        "key_fingerprint": key_fingerprint(mask_key),
        "key_created_at": context["key_metadata"].get("created_at"),
        "key_rotated_at": context["key_metadata"].get("rotated_at"),
        "key": mask_key,
        "restore_note": "Store this backup outside Git. Reusing the same key keeps masked aliases stable across exports.",
    }


async def async_rotate_privacy_key(hass: HomeAssistant) -> dict[str, Any]:
    if environment_mask_key():
        raise ValueError("Cannot rotate managed privacy key while HCX_MASK_KEY environment override is active")

    current = await async_load_or_create_privacy_key(hass)
    record = _new_record(previous_fingerprint=key_fingerprint(current.get("key")))
    await _store(hass).async_save(record)
    hass.data.setdefault(DOMAIN, {})[STATE_KEY] = record
    return {
        "rotated": True,
        "key_source": "managed_storage",
        "key_fingerprint": key_fingerprint(record["key"]),
        "key_created_at": record.get("created_at"),
        "key_rotated_at": record.get("rotated_at"),
        "previous_fingerprint": record.get("previous_fingerprint"),
    }
