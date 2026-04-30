from __future__ import annotations

from typing import Any

from .analysis import (
    build_battery_summary,
    build_domain_health,
    build_entity_activity_summary,
    build_noise_summary,
    build_recorder_advice,
    generate_recommendations,
)
from .exporter import build_ai_context_bundle
from .privacy import has_custom_mask_key, mask_payload

EXPORT_LEVELS = {"short", "deep"}


def build_snapshot_payload(states: list[Any]) -> dict[str, Any]:
    summary = build_entity_activity_summary(states)
    noise = build_noise_summary(states)
    battery = build_battery_summary(states)
    recommendations = generate_recommendations(summary, noise, battery)
    recorder_advice = build_recorder_advice(noise)
    domain_health = build_domain_health(states, noise)
    return {
        "summary": summary,
        "noise": noise,
        "battery": battery,
        "recommendations": recommendations,
        "recorder_advice": recorder_advice,
        "domain_health": domain_health,
    }


def build_ai_export_payload(states: list[Any], level: str = "deep") -> dict[str, Any]:
    level = level if level in EXPORT_LEVELS else "deep"
    snapshot = mask_payload(build_snapshot_payload(states))
    if not has_custom_mask_key():
        raise ValueError("HCX_MASK_KEY must be set for export")

    bundle = build_ai_context_bundle(
        snapshot["summary"],
        snapshot["noise"],
        snapshot["battery"],
        snapshot["recommendations"],
        snapshot["recorder_advice"],
    )
    bundle["domain_health"] = snapshot["domain_health"]
    bundle["export_level"] = level

    if level == "short":
        return {
            "schema_version": bundle["schema_version"],
            "generated_at": bundle["generated_at"],
            "product": bundle["product"],
            "export_level": "short",
            "meta": bundle["meta"],
            "summary": bundle["summary"],
            "action_queue": bundle["action_queue"],
            "llm_context_short": bundle["llm_context_short"],
        }

    return bundle


def build_ideas_payload() -> dict[str, list[str]]:
    return {
        "ideas": [
            "Automation drift detector: identify automations with no recent state impact.",
            "Recorder budget advisor: suggest include/exclude patterns by measured noise score.",
            "Battery risk forecast: estimate risk windows from low battery + activity patterns.",
            "Entity naming auditor: detect inconsistent naming and suggest normalized patterns.",
            "Blueprint opportunity miner: detect repeated automation patterns for blueprint extraction.",
        ]
    }
