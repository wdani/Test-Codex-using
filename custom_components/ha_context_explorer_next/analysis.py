from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any


def _entity_domain(entity_id: str) -> str:
    return entity_id.split('.', 1)[0] if '.' in entity_id else 'unknown'


def build_entity_activity_summary(states: list[Any]) -> dict[str, Any]:
    domain_counts = Counter()
    unavailable = 0

    for state in states:
        entity_id = getattr(state, "entity_id", "unknown.unknown")
        domain = _entity_domain(entity_id)
        domain_counts[domain] += 1
        if getattr(state, "state", None) in {"unavailable", "unknown"}:
            unavailable += 1

    top_domains = [{"domain": d, "count": c} for d, c in domain_counts.most_common(10)]

    return {
        "entities_total": len(states),
        "entities_unavailable_or_unknown": unavailable,
        "top_domains": top_domains,
    }


def build_noise_summary(states: list[Any]) -> dict[str, Any]:
    top_by_attr_size: list[dict[str, Any]] = []

    for state in states:
        attrs = getattr(state, "attributes", {}) or {}
        attr_keys = len(attrs.keys())
        attr_chars = sum(len(str(k)) + len(str(v)) for k, v in attrs.items())
        score = (attr_keys * 2) + attr_chars
        top_by_attr_size.append(
            {
                "entity_id": getattr(state, "entity_id", "unknown.unknown"),
                "domain": _entity_domain(getattr(state, "entity_id", "unknown.unknown")),
                "attributes_count": attr_keys,
                "attributes_chars": attr_chars,
                "noise_score": score,
            }
        )

    top_by_attr_size.sort(key=lambda i: i["noise_score"], reverse=True)
    top_noisy = top_by_attr_size[:20]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "top_noisy_entities": top_noisy,
    }


def build_battery_summary(states: list[Any]) -> dict[str, Any]:
    battery_entities = []
    for state in states:
        entity_id = getattr(state, "entity_id", "")
        if entity_id.startswith("sensor.") and ("battery" in entity_id.lower() or "battery" in getattr(state, "name", "").lower()):
            value = getattr(state, "state", None)
            battery_entities.append({"entity_id": entity_id, "state": value})

    low = []
    for item in battery_entities:
        try:
            if float(item["state"]) <= 20:
                low.append(item)
        except (TypeError, ValueError):
            continue

    return {
        "battery_entities_total": len(battery_entities),
        "battery_entities_low": len(low),
        "low_battery_entities": low[:50],
    }


def generate_recommendations(
    summary: dict[str, Any],
    noise_summary: dict[str, Any],
    battery_summary: dict[str, Any],
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []

    if summary.get("entities_unavailable_or_unknown", 0) > 0:
        recs.append({
            "id": "availability-review",
            "severity": "medium",
            "title": "Review unavailable entities",
            "detail": "Some entities are unavailable/unknown; check connectivity, power, and integration health.",
        })

    if summary.get("entities_total", 0) > 500:
        recs.append({
            "id": "scale-recorder-review",
            "severity": "high",
            "title": "Recorder optimization suggested",
            "detail": "Large installations benefit from include/exclude tuning and purge strategy.",
        })

    if battery_summary.get("battery_entities_low", 0) > 0:
        recs.append({
            "id": "battery-attention",
            "severity": "high",
            "title": "Low battery devices detected",
            "detail": "Low battery entities were detected; replace/recharge soon to avoid automation instability.",
        })

    if noise_summary.get("top_noisy_entities"):
        recs.append({
            "id": "noise-hotspots",
            "severity": "medium",
            "title": "High-noise entities identified",
            "detail": "Review top noisy entities to reduce recorder churn and excess log verbosity.",
        })

    if not recs:
        recs.append({
            "id": "healthy-baseline",
            "severity": "low",
            "title": "No immediate issues detected",
            "detail": "Current baseline looks healthy for this quick pass.",
        })

    return recs
