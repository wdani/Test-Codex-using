# HA Context Explorer Next

Experimental Home Assistant custom integration for deep system analysis, privacy-safe exports, and AI-ready context bundles.

## Vision

HA Context Explorer Next helps users understand:
- what is used most often
- which entities/devices create most noise
- where battery-powered devices may need optimization
- how logs and recorder usage grow over time
- what improvements are likely high impact

## MVP (Phase 1)

- Integration scaffold with sidebar panel
- Read-only analytics endpoints
- Deterministic privacy masking
- AI-ready export schema
- Rule-based recommendations engine
- English-first UI with i18n-ready structure
- Admin diagnostics endpoint for support handovers and UI debugging
- Battery health diagnostics for low, critical, watch, and unknown battery signals
- Heuristic recorder/logbook volume analysis from current state metadata

## Status

This repository is an active prototype.

## Privacy key configuration

For production-like usage, set a unique mask key so deterministic masking tokens are not derived from the default fallback key.

- environment variable: `HCX_MASK_KEY`
- effect: used by `stable_mask` keyed HMAC digest

Example:

```bash
export HCX_MASK_KEY="replace-with-a-long-random-secret"
```

Exports stay locked until `HCX_MASK_KEY` is set to a non-default value. The normal summary endpoint still works without the key and reports export readiness in its `privacy` section.

Current deterministic masking covers:

- IPv4, IPv6, MAC addresses, and email addresses in text
- sensitive attribute keys such as `friendly_name`, `latitude`, `longitude`, `host`, `ip_address`, `serial`, `ssid`, `user`, and `unique_id`
- privacy coverage counters for detected sensitive keys and text patterns, without returning raw sensitive values

## Export levels

Two admin-only export levels are available:

- `deep` (default): full payload with deep context
- `short`: compact payload for quick LLM prompts

Endpoints:

- `/api/ha_context_explorer_next/export/ai_context`
- `/api/ha_context_explorer_next/export/ai_context/short`
- `/api/ha_context_explorer_next/export/ai_context/deep`

## Developer diagnostics

Admin-only diagnostics are available at:

- `/api/ha_context_explorer_next/diagnostics`

The diagnostics payload includes analyzer capabilities, export lock state, privacy mask policy metadata, privacy coverage counters, entity counts, top domains, and support notes. It is intended as a compact handover payload for debugging the integration and for future Codex/UI review workflows.

## Recorder/logbook volume analysis

The summary and AI export payloads include `recorder_volume`, a heuristic estimate of recorder/logbook impact built from current entity state, domain type, attribute count, and attribute payload size.

It reports:

- estimated events and state bytes per day
- top entity and domain hotspots
- safe exclusion candidates that avoid critical control/security domains
- a clear note that the estimate should be replaced with recorder statistics when available

## Battery health diagnostics

The summary, diagnostics, and AI export payloads include a richer `battery` section. It detects battery signals from entity ids, names, `device_class: battery`, common battery attributes, and binary low-battery sensors.

It reports:

- critical, low, watch, unknown, and healthy battery signals
- grouped device keys so duplicated battery entities are easier to review together
- top battery risks and a maintenance queue for the next action list
- recommendation items for critical batteries, unreadable battery signals, and watch-list devices
