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
from .const import DOMAIN, PANEL_FRONTEND_VERSION, PANEL_MODULE_URL, PANEL_URL
from .exporter import build_ai_context_bundle
from .privacy import build_privacy_coverage, build_privacy_status, has_custom_mask_key, mask_payload

EXPORT_LEVELS = {"short", "deep"}
UI_CONTEXT_VERSION = "1.0.0"


def build_panel_metadata() -> dict[str, str]:
    return {
        "url": PANEL_URL,
        "module_url": PANEL_MODULE_URL,
        "frontend_version": PANEL_FRONTEND_VERSION,
    }


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
        "panel": build_panel_metadata(),
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


def _section(
    section_id: str,
    title: str,
    visible_state: dict[str, Any],
    *,
    controls: list[str] | None = None,
    tables: list[dict[str, Any]] | None = None,
    actions: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "visible_state": visible_state,
        "controls": controls or [],
        "tables": tables or [],
        "actions": actions or [],
        "notes": notes or [],
    }


def build_ui_context_payload(
    states: list[Any],
    mask_key: str | None = None,
    key_source: str | None = None,
    key_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not has_custom_mask_key(mask_key):
        raise ValueError("Privacy mask key must be available for UI context export")

    snapshot = mask_payload(build_snapshot_payload(states, mask_key, key_source, key_metadata), mask_key)
    privacy = snapshot["privacy"]
    battery = snapshot["battery"]
    recorder_advice = snapshot["recorder_advice"]
    recorder_volume = snapshot["recorder_volume"]
    recommendations = snapshot["recommendations"]

    sections = [
        _section(
            "overview_kpis",
            "Overview KPI cards",
            {
                "entities": snapshot["summary"].get("entities_total", 0),
                "unavailable_or_unknown": snapshot["summary"].get("entities_unavailable_or_unknown", 0),
                "critical_battery": battery.get("battery_entities_critical", 0),
                "low_battery": battery.get("battery_entities_low", 0),
            },
            notes=["First viewport summary cards prioritize scale, availability, and battery urgency."],
        ),
        _section(
            "battery_health",
            "Battery health",
            {
                "critical": battery.get("battery_entities_critical", 0),
                "low": battery.get("battery_entities_low", 0),
                "watch": battery.get("battery_entities_watch", 0),
                "unknown": battery.get("battery_entities_unknown", 0),
            },
            tables=[
                {
                    "id": "battery_risks",
                    "columns": ["entity_id", "device_key", "percent", "risk_level", "recommended_action"],
                    "visible_rows": battery.get("top_battery_risks", [])[:8],
                }
            ],
            notes=["Rows are ordered by risk first so maintenance work is visible before lower-priority signals."],
        ),
        _section(
            "top_noisy_entities",
            "Top noisy entities",
            {"rows_visible": 5},
            tables=[
                {
                    "id": "top_noisy_entities",
                    "columns": ["entity_id", "domain", "noise_score"],
                    "visible_rows": snapshot["noise"].get("top_noisy_entities", [])[:5],
                }
            ],
        ),
        _section(
            "recorder_advice",
            "Recorder advice",
            {"yaml_preview": recorder_advice.get("yaml_preview", {})},
            controls=["domain_filter", "sort", "copy_yaml"],
            tables=[
                {
                    "id": "recorder_entity_suggestions",
                    "columns": ["entity_id", "domain", "noise_score", "risk_level"],
                    "visible_rows": recorder_advice.get("entity_suggestions", [])[:12],
                }
            ],
            actions=["copy recorder YAML preview"],
        ),
        _section(
            "recorder_logbook_volume",
            "Recorder/logbook volume",
            recorder_volume.get("totals", {}),
            tables=[
                {
                    "id": "recorder_volume_entities",
                    "columns": [
                        "entity_id",
                        "domain",
                        "estimated_daily_events",
                        "estimated_daily_state_bytes",
                        "risk_level",
                    ],
                    "visible_rows": recorder_volume.get("top_entities", [])[:8],
                }
            ],
            notes=recorder_volume.get("notes", []),
        ),
        _section(
            "domain_health_matrix",
            "Domain health matrix",
            {"rows_visible": min(len(snapshot["domain_health"]), 20)},
            tables=[
                {
                    "id": "domain_health",
                    "columns": ["domain", "entities", "noise_score", "noise_density", "risk"],
                    "visible_rows": snapshot["domain_health"][:20],
                }
            ],
        ),
        _section(
            "privacy_export_status",
            "Privacy/export status",
            {
                "exports_enabled": privacy.get("exports_enabled"),
                "key_source": privacy.get("key_source"),
                "key_fingerprint": privacy.get("key_fingerprint"),
                "entities_with_sensitive_signals": privacy.get("coverage", {}).get("entities_with_sensitive_signals", 0),
                "entities_scanned": privacy.get("coverage", {}).get("entities_scanned", 0),
                "sensitive_key_hits": privacy.get("coverage", {}).get("sensitive_key_hits", [])[:6],
                "text_pattern_hits": privacy.get("coverage", {}).get("text_pattern_hits", {}),
            },
            controls=["download_key_backup", "rotate_key"],
            notes=["The raw privacy key is never included in this UI context export."],
        ),
        _section(
            "export_workbench",
            "Export workbench",
            {"default_level": "short", "available_levels": sorted(EXPORT_LEVELS)},
            controls=["export_level", "copy_export_json", "copy_llm_short", "copy_do_first", "copy_ui_context"],
            actions=["copy masked AI export", "copy short LLM context", "copy first action queue", "copy UI context"],
        ),
        _section(
            "diagnostics",
            "Diagnostics",
            {"initial_preview": "empty_until_loaded"},
            controls=["load_diagnostics", "copy_diagnostics_json"],
            actions=["load admin diagnostics payload", "copy diagnostics JSON"],
        ),
        _section(
            "recommendations",
            "Recommendations",
            {"count": len(recommendations)},
            tables=[
                {
                    "id": "recommendations",
                    "columns": ["severity", "title", "detail", "category", "confidence", "next_action"],
                    "visible_rows": recommendations,
                }
            ],
            notes=["Cards are sorted by severity so high-impact work appears first."],
        ),
    ]

    return {
        "schema_version": UI_CONTEXT_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "product": "ha_context_explorer_next",
        "source": "panel_user_visible_context",
        "purpose": "Help an AI understand what the Home Assistant panel shows to a human user.",
        "privacy": {
            "masked": True,
            "key_source": privacy.get("key_source"),
            "key_fingerprint": privacy.get("key_fingerprint"),
            "raw_key_included": False,
        },
        "panel": {
            "title": "HA Context Explorer Next",
            **build_panel_metadata(),
            "initial_export_level": "short",
            "reading_order": [section["id"] for section in sections],
        },
        "sections": sections,
        "user_tasks_supported": [
            "Find unavailable or unknown entities.",
            "Prioritize battery maintenance.",
            "Identify recorder/logbook noise and volume hotspots.",
            "Generate masked AI exports.",
            "Collect diagnostics for support or Codex handover.",
        ],
    }


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
            "panel_frontend_version": PANEL_FRONTEND_VERSION,
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
            "ui_context_export",
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
