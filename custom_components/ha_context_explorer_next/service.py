from __future__ import annotations

from typing import Any

from .analysis import (
    build_battery_summary,
    build_entity_activity_summary,
    build_noise_summary,
    generate_recommendations,
)
from .exporter import build_ai_context_bundle


def build_snapshot_payload(states: list[Any]) -> dict[str, Any]:
    summary = build_entity_activity_summary(states)
    noise = build_noise_summary(states)
    battery = build_battery_summary(states)
    recommendations = generate_recommendations(summary, noise, battery)
    return {
        "summary": summary,
        "noise": noise,
        "battery": battery,
        "recommendations": recommendations,
    }


def build_ai_export_payload(states: list[Any]) -> dict[str, Any]:
    snapshot = build_snapshot_payload(states)
    return build_ai_context_bundle(
        snapshot["summary"],
        snapshot["noise"],
        snapshot["battery"],
        snapshot["recommendations"],
    )


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
