from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_ai_context_bundle(
    summary: dict[str, Any],
    noise_summary: dict[str, Any],
    battery_summary: dict[str, Any],
    recommendations: list[dict[str, str]],
    recorder_advice: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.2.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "product": "ha_context_explorer_next",
        "summary": summary,
        "noise": noise_summary,
        "battery": battery_summary,
        "recommendations": recommendations,
        "recorder_advice": recorder_advice,
        "actionable_recommendations": [
            {"id": r["id"], "severity": r["severity"], "next_action": r.get("next_action", "")}
            for r in recommendations
        ],
        "notes": [
            "Read-only best-effort analysis.",
            "Sensitive values should be masked before sharing externally.",
            "Noise scoring is heuristic and intended for prioritization, not absolute judgment.",
        ],
    }
