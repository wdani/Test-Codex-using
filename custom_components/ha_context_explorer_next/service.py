from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .analysis import (
    build_battery_summary,
    build_domain_health,
    build_entity_activity_summary,
    build_noise_summary,
    build_recorder_advice,
    build_recorder_volume_summary,
    generate_recommendations,
)
from .const import DOMAIN, PANEL_MODULE_URL, PANEL_URL
from .exporter import build_ai_context_bundle
from .privacy import build_privacy_coverage, build_privacy_status, has_custom_mask_key, mask_payload

EXPORT_LEVELS = {"short", "deep"}


def build_snapshot_payload(
    states: list[Any],
    mask_key: str | None = None,
    key_source: str | None = None,
    key_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = build_entity_activity_summary(states)
    noise = build_noise_summary(states)
    battery = build_battery_summary(states)
    recorder_volume = build_recorder_volume_summary(states, noise)
    recommendations = generate_recommendations(summary, noise, battery, recorder_volume)
    recorder_advice = build_recorder_advice(noise)
    domain_health = build_domain_health(states, noise)
    privacy = build_privacy_status(build_privacy_coverage(states), mask_key, key_source, key_metadata)
    return {
        "summary": summary,
        "noise": noise,
        "battery": battery,
        "recommendations": recommendations,
        "recorder_advice": recorder_advice,
        "recorder_volume": recorder_volume,
        "domain_health": domain_health,
        "privacy": privacy,
    }


def build_ai_export_payload(
    states: list[Any],
    level: str = "deep",
    mask_key: str | None = None,
    key_source: str | None = None,
    key_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    level = level if level in EXPORT_LEVELS else "deep"
    if not has_custom_mask_key(mask_key):
        raise ValueError("Privacy mask key must be available for export")
    snapshot = mask_payload(build_snapshot_payload(states, mask_key, key_source, key_metadata), mask_key)

    bundle = build_ai_context_bundle(
        snapshot["summary"],
        snapshot["noise"],
        snapshot["battery"],
        snapshot["recommendations"],
        snapshot["recorder_advice"],
        snapshot["recorder_volume"],
    )
    bundle["domain_health"] = snapshot["domain_health"]
    bundle["recorder_volume"] = snapshot["recorder_volume"]
    bundle["privacy"] = snapshot["privacy"]
    bundle["export_level"] = level

    if level == "short":
        return {
            "schema_version": bundle["schema_version"],
            "generated_at": bundle["generated_at"],
            "product": bundle["product"],
            "export_level": "short",
            "meta": bundle["meta"],
            "privacy": bundle["privacy"],
            "summary": bundle["summary"],
            "battery": bundle["battery"],
            "recorder_volume": bundle["recorder_volume"],
            "action_queue": bundle["action_queue"],
            "llm_context_short": bundle["llm_context_short"],
        }

    return bundle


def build_diagnostics_payload(
    states: list[Any],
    mask_key: str | None = None,
    key_source: str | None = None,
    key_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = build_snapshot_payload(states, mask_key, key_source, key_metadata)
    privacy = snapshot["privacy"]
    exports_enabled = bool(privacy.get("exports_enabled"))
    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "product": "ha_context_explorer_next",
        "integration": {
            "domain": DOMAIN,
            "panel_url": PANEL_URL,
            "panel_module_url": PANEL_MODULE_URL,
        },
        "capabilities": [
            "summary",
            "domain_health",
            "battery_health",
            "recorder_advice",
            "recommendations",
            "privacy_masking",
            "managed_privacy_key",
            "privacy_key_backup",
            "privacy_key_rotation",
            "recorder_volume",
            "ai_export_short",
            "ai_export_deep",
        ],
        "privacy": privacy,
        "export": {
            "enabled": exports_enabled,
            "levels": sorted(EXPORT_LEVELS),
            "blocked_reason": None if exports_enabled else "Privacy mask key missing",
        },
        "counts": {
            "entities_total": snapshot["summary"].get("entities_total", 0),
            "entities_unavailable_or_unknown": snapshot["summary"].get("entities_unavailable_or_unknown", 0),
            "battery_entities_low": snapshot["battery"].get("battery_entities_low", 0),
            "battery_entities_critical": snapshot["battery"].get("battery_entities_critical", 0),
            "battery_entities_unknown": snapshot["battery"].get("battery_entities_unknown", 0),
            "recommendations": len(snapshot["recommendations"]),
            "domain_health_rows": len(snapshot["domain_health"]),
            "recorder_volume_hotspots": snapshot["recorder_volume"].get("totals", {}).get("high_impact_entities", 0),
        },
        "top_domains": snapshot["summary"].get("top_domains", []),
        "developer_notes": [
            "Diagnostics is admin-only and intended for support, UI debugging, and Codex handover context.",
            "AI exports use the managed privacy key unless HCX_MASK_KEY overrides it for development.",
            "Masking is deterministic so repeated sensitive values keep stable pseudonyms.",
        ],
    }


def build_ideas_payload() -> dict[str, list[str]]:
    return {
        "ideas": [
            "Automation drift detector: identify automations with no recent state impact.",
            "Recorder budget advisor: suggest include/exclude patterns by measured noise score.",
            "Battery risk forecast: estimate risk windows from low battery + activity patterns.",
            "Entity naming auditor: detect inconsistent naming and suggest normalized patterns.",
            "Blueprint opportunity miner: detect repeated automation patterns for blueprint extraction.",
            "Dev diagnostics export: capture analyzer, privacy, and UI state for support handovers.",
            "Privacy preview: show which fields will be masked before an export is generated.",
        ]
    }
