from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

HIGH_CHURN_DOMAIN_FACTORS = {
    "sensor": 10,
    "binary_sensor": 6,
    "device_tracker": 8,
    "person": 5,
    "weather": 4,
    "camera": 4,
    "media_player": 4,
    "automation": 3,
    "script": 3,
    "light": 2,
    "switch": 2,
}
CRITICAL_CONTROL_DOMAINS = {"alarm_control_panel", "cover", "fan", "lock", "siren"}


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
    domain_noise = Counter()

    for state in states:
        entity_id = getattr(state, "entity_id", "unknown.unknown")
        domain = _entity_domain(entity_id)
        attrs = getattr(state, "attributes", {}) or {}
        attr_keys = len(attrs.keys())
        attr_chars = sum(len(str(k)) + len(str(v)) for k, v in attrs.items())
        score = (attr_keys * 2) + attr_chars
        domain_noise[domain] += score
        top_by_attr_size.append(
            {
                "entity_id": entity_id,
                "domain": domain,
                "attributes_count": attr_keys,
                "attributes_chars": attr_chars,
                "noise_score": score,
            }
        )

    top_by_attr_size.sort(key=lambda i: i["noise_score"], reverse=True)
    top_noisy = top_by_attr_size[:20]
    top_domains = [{"domain": d, "noise_score": s} for d, s in domain_noise.most_common(10)]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "top_noisy_entities": top_noisy,
        "top_noisy_domains": top_domains,
        "domain_noise_all": dict(domain_noise),
    }


def build_battery_summary(states: list[Any]) -> dict[str, Any]:
    battery_entities = []
    for state in states:
        entity_id = getattr(state, "entity_id", "")
        state_name = getattr(state, "name", "")
        if entity_id.startswith("sensor.") and (
            "battery" in entity_id.lower() or "battery" in state_name.lower()
        ):
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


def _rec(
    id_: str,
    severity: str,
    title: str,
    detail: str,
    next_action: str,
    category: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "id": id_,
        "severity": severity,
        "category": category,
        "confidence": confidence,
        "title": title,
        "detail": detail,
        "next_action": next_action,
    }


def generate_recommendations(
    summary: dict[str, Any],
    noise_summary: dict[str, Any],
    battery_summary: dict[str, Any],
    recorder_volume: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []

    if summary.get("entities_unavailable_or_unknown", 0) > 0:
        recs.append(
            _rec(
                "availability-review",
                "medium",
                "Review unavailable entities",
                "Some entities are unavailable/unknown; check connectivity, power, and integration health.",
                "Open entities view and inspect unavailable devices/integrations first.",
                "availability",
                0.75,
            )
        )

    if summary.get("entities_total", 0) > 500:
        recs.append(
            _rec(
                "scale-recorder-review",
                "high",
                "Recorder optimization suggested",
                "Large installations benefit from include/exclude tuning and purge strategy.",
                "Review recorder include/exclude and verify purge retention settings.",
                "recorder",
                0.8,
            )
        )

    if battery_summary.get("battery_entities_low", 0) > 0:
        recs.append(
            _rec(
                "battery-attention",
                "high",
                "Low battery devices detected",
                "Low battery entities were detected; replace/recharge soon to avoid automation instability.",
                "Replace/recharge low battery devices in the next maintenance window.",
                "battery",
                0.9,
            )
        )

    top_noise = noise_summary.get("top_noisy_entities", [])
    max_noise_score = int(top_noise[0].get("noise_score", 0)) if top_noise else 0
    if max_noise_score >= 1500:
        recs.append(
            _rec(
                "noise-hotspots",
                "medium",
                "High-noise entities identified",
                "Review top noisy entities to reduce recorder churn and excess log verbosity.",
                "Exclude non-essential high-noise entities from recorder/logbook.",
                "noise",
                0.7,
            )
        )

    if recorder_volume:
        totals = recorder_volume.get("totals", {})
        if int(totals.get("high_impact_entities", 0)) > 0 or int(totals.get("domains_review", 0)) > 0:
            recs.append(
                _rec(
                    "recorder-volume-hotspots",
                    "medium",
                    "Recorder volume hotspots detected",
                    "Some entities or domains are likely to create disproportionate recorder/logbook volume.",
                    "Review recorder volume hotspots before adding broad include/exclude rules.",
                    "recorder",
                    0.72,
                )
            )

    severity_order = {"high": 0, "medium": 1, "low": 2}

    if not recs:
        recs.append(
            _rec(
                "healthy-baseline",
                "low",
                "No immediate issues detected",
                "Current baseline looks healthy for this quick pass.",
                "Keep monitoring weekly and revisit after major integration changes.",
                "baseline",
                0.6,
            )
        )

    recs.sort(key=lambda r: severity_order.get(r["severity"], 99))
    return recs


def build_recorder_advice(noise_summary: dict[str, Any]) -> dict[str, Any]:
    top_entities = noise_summary.get("top_noisy_entities", [])[:12]
    top_domains = noise_summary.get("top_noisy_domains", [])[:6]

    def risk_for_entity(score: int) -> str:
        if score >= 6000:
            return "aggressive"
        if score >= 3500:
            return "review"
        return "safe"

    entity_suggestions = []
    for e in top_entities:
        score = int(e.get("noise_score", 0))
        domain = e.get("domain")
        if domain in {"alarm_control_panel", "lock"}:
            continue
        if score < 2500:
            continue
        entity_suggestions.append(
            {
                "entity_id": e.get("entity_id"),
                "domain": domain,
                "noise_score": score,
                "risk_level": risk_for_entity(score),
                "reason": "High attribute churn can inflate recorder/logbook volume.",
            }
        )

    domain_suggestions = []
    for d in top_domains:
        score = int(d.get("noise_score", 0))
        domain = d.get("domain")
        if domain in {"binary_sensor", "sensor"}:
            continue
        if score < 10000:
            continue
        domain_suggestions.append(
            {
                "domain": domain,
                "noise_score": score,
                "risk_level": "review" if score < 25000 else "aggressive",
                "reason": "Domain-level recorder churn appears elevated.",
            }
        )

    yaml_preview = {
        "recorder": {
            "exclude": {
                "entities": [e["entity_id"] for e in entity_suggestions],
                "domains": [d["domain"] for d in domain_suggestions],
            }
        }
    }

    return {
        "entity_suggestions": entity_suggestions,
        "domain_suggestions": domain_suggestions,
        "yaml_preview": yaml_preview,
        "note": "Review manually before applying; avoid excluding critical control/security entities.",
    }


def _estimated_daily_events(domain: str, attr_keys: int, attr_chars: int) -> int:
    factor = HIGH_CHURN_DOMAIN_FACTORS.get(domain, 2)
    attr_weight = min(20, attr_keys // 4)
    size_weight = min(25, attr_chars // 800)
    return max(1, factor + attr_weight + size_weight)


def _volume_risk(score: int) -> str:
    if score >= 75000:
        return "aggressive"
    if score >= 25000:
        return "review"
    return "safe"


def _volume_reason(domain: str, attr_keys: int, attr_chars: int, estimated_events: int) -> str:
    reasons = []
    if domain in HIGH_CHURN_DOMAIN_FACTORS:
        reasons.append("domain commonly changes often")
    if attr_keys >= 20:
        reasons.append("many attributes")
    if attr_chars >= 5000:
        reasons.append("large attribute payload")
    if estimated_events >= 20:
        reasons.append("high estimated event rate")
    return ", ".join(reasons) if reasons else "low estimated recorder/logbook impact"


def build_recorder_volume_summary(states: list[Any], noise_summary: dict[str, Any]) -> dict[str, Any]:
    noise_by_entity = {
        item.get("entity_id"): int(item.get("noise_score", 0))
        for item in noise_summary.get("top_noisy_entities", [])
    }
    entity_rows = []
    domain_rows: dict[str, dict[str, Any]] = {}

    for state in states:
        entity_id = getattr(state, "entity_id", "unknown.unknown")
        domain = _entity_domain(entity_id)
        attrs = getattr(state, "attributes", {}) or {}
        attr_keys = len(attrs)
        attr_chars = sum(len(str(k)) + len(str(v)) for k, v in attrs.items())
        state_chars = len(str(getattr(state, "state", "")))
        estimated_events = _estimated_daily_events(domain, attr_keys, attr_chars)
        estimated_bytes = estimated_events * max(64, len(entity_id) + state_chars + attr_chars)
        volume_score = estimated_bytes + noise_by_entity.get(entity_id, 0)
        risk = _volume_risk(volume_score)
        row = {
            "entity_id": entity_id,
            "domain": domain,
            "attributes_count": attr_keys,
            "attributes_chars": attr_chars,
            "estimated_daily_events": estimated_events,
            "estimated_daily_state_bytes": estimated_bytes,
            "volume_score": volume_score,
            "risk_level": risk,
            "reason": _volume_reason(domain, attr_keys, attr_chars, estimated_events),
            "recommended_action": "review recorder/logbook exclusion" if risk != "safe" else "keep observed",
        }
        entity_rows.append(row)

        domain_row = domain_rows.setdefault(
            domain,
            {
                "domain": domain,
                "entities": 0,
                "estimated_daily_events": 0,
                "estimated_daily_state_bytes": 0,
                "volume_score": 0,
                "risk_level": "safe",
            },
        )
        domain_row["entities"] += 1
        domain_row["estimated_daily_events"] += estimated_events
        domain_row["estimated_daily_state_bytes"] += estimated_bytes
        domain_row["volume_score"] += volume_score
        domain_row["risk_level"] = _volume_risk(int(domain_row["volume_score"]))

    entity_rows.sort(key=lambda item: int(item["volume_score"]), reverse=True)
    domain_list = sorted(domain_rows.values(), key=lambda item: int(item["volume_score"]), reverse=True)
    exclusion_candidates = [
        row["entity_id"]
        for row in entity_rows
        if row["risk_level"] in {"review", "aggressive"} and row["domain"] not in CRITICAL_CONTROL_DOMAINS
    ][:20]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "method": "heuristic_current_state_snapshot",
        "totals": {
            "entities_scanned": len(states),
            "estimated_daily_events": sum(int(row["estimated_daily_events"]) for row in entity_rows),
            "estimated_daily_state_bytes": sum(int(row["estimated_daily_state_bytes"]) for row in entity_rows),
            "high_impact_entities": sum(1 for row in entity_rows if row["risk_level"] != "safe"),
            "domains_review": sum(1 for row in domain_list if row["risk_level"] != "safe"),
        },
        "top_entities": entity_rows[:20],
        "top_domains": domain_list[:12],
        "safe_exclusion_candidates": exclusion_candidates,
        "notes": [
            "Heuristic estimate from current states; future versions should use recorder statistics when available.",
            "Review manually before excluding entities from recorder or logbook.",
        ],
    }


def build_domain_health(states: list[Any], noise_summary: dict[str, Any]) -> list[dict[str, Any]]:
    domain_counts: dict[str, int] = {}
    domain_noise: dict[str, int] = {
        str(domain): int(score)
        for domain, score in (noise_summary.get("domain_noise_all", {}) or {}).items()
    }

    for state in states:
        entity_id = getattr(state, "entity_id", "unknown.unknown")
        domain = _entity_domain(entity_id)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    rows = []
    for domain in sorted(set(domain_counts) | set(domain_noise)):
        count = domain_counts.get(domain, 0)
        noise = domain_noise.get(domain, 0)
        density = round(noise / count, 2) if count else 0
        risk = "aggressive" if density >= 2000 else "review" if density >= 500 else "safe"
        rows.append({"domain": domain, "entities": count, "noise_score": noise, "noise_density": density, "risk": risk})

    rows.sort(key=lambda r: r["noise_density"], reverse=True)
    return rows[:20]
