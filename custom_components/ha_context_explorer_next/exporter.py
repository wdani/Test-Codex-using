from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def _build_action_queue(recommendations: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    do_first, do_next, later = [], [], []
    for rec in recommendations:
        item = {
            "id": rec["id"],
            "stable_id": _stable_id(rec["id"]),
            "title": rec["title"],
            "reason": rec["detail"],
            "impact": "high" if rec["severity"] == "high" else "medium",
            "estimated_effort": "low" if rec["severity"] == "low" else "high" if rec["severity"] == "high" else "medium",
            "category": rec.get("category", "general"),
            "confidence": rec.get("confidence", 0.5),
            "next_action": rec.get("next_action", ""),
        }
        if rec["severity"] == "high":
            do_first.append(item)
        elif rec["severity"] == "medium":
            do_next.append(item)
        else:
            later.append(item)
    return {"do_first": do_first, "do_next": do_next, "later": later}


def build_ai_context_bundle(
    summary: dict[str, Any],
    noise_summary: dict[str, Any],
    battery_summary: dict[str, Any],
    recommendations: list[dict[str, str]],
    recorder_advice: dict[str, Any],
    recorder_volume: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action_queue = _build_action_queue(recommendations)

    return {
        "schema_version": "2.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "product": "ha_context_explorer_next",
        "meta": {
            "instance_profile": {
                "entities_total": summary.get("entities_total", 0),
                "entities_unavailable_or_unknown": summary.get("entities_unavailable_or_unknown", 0),
                "battery_entities_low": battery_summary.get("battery_entities_low", 0),
            },
            "quality_flags": {
                "masked_export": True,
                "recommendations_count": len(recommendations),
            },
        },
        "summary": summary,
        "noise": noise_summary,
        "battery": battery_summary,
        "recommendations": recommendations,
        "recorder_advice": recorder_advice,
        "recorder_volume": recorder_volume or {},
        "action_queue": action_queue,
        "llm_context_short": {
            "high_priority_count": len(action_queue["do_first"]),
            "top_recommendations": [r["title"] for r in recommendations[:3]],
        },
        "llm_context_deep": {
            "top_noisy_entities": noise_summary.get("top_noisy_entities", [])[:20],
            "top_noisy_domains": noise_summary.get("top_noisy_domains", [])[:10],
            "top_recorder_volume_entities": (recorder_volume or {}).get("top_entities", [])[:10],
            "recorder_yaml_preview": recorder_advice.get("yaml_preview", {}),
        },
        "actionable_recommendations": [
            {
                "id": r["id"],
                "stable_id": _stable_id(r["id"]),
                "severity": r["severity"],
                "next_action": r.get("next_action", ""),
            }
            for r in recommendations
        ],
        "notes": [
            "Read-only best-effort analysis.",
            "Sensitive values are masked in export payloads.",
            "Noise scoring is heuristic and intended for prioritization, not absolute judgment.",
        ],
    }
