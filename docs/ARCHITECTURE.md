# Architecture (v0.1)

## Layers

1. Collection: pull current Home Assistant in-memory state.
2. Analysis: produce quick health and activity summaries.
3. Recommendation engine: map findings to actionable suggestions.
4. Privacy: deterministic masking utilities.
5. Export: AI-friendly context bundle.
6. Diagnostics: admin-only support payload for analyzer/export/UI state.
7. UI: in-panel summary visualization.

## API surfaces

- `/api/ha_context_explorer_next/summary`: read-only analyzer snapshot, including privacy/export status.
- `/api/ha_context_explorer_next/export/ai_context/{level}`: masked AI export, blocked until `HCX_MASK_KEY` is set.
- `/api/ha_context_explorer_next/diagnostics`: compact support and Codex handover payload.
- `/api/ha_context_explorer_next/ideas`: current product backlog ideas.

## Recorder/logbook model

- `recorder_volume` is a current-state heuristic, not a database measurement.
- Entity volume score combines estimated domain churn, state size, attribute count, attribute payload size, and noise score.
- Domain rows aggregate entity estimates so broad recorder/logbook candidates are visible.
- Critical control/security domains are excluded from safe exclusion candidates.
- Future recorder integration should replace estimated event counts with observed database/event statistics.

## Privacy model

- Export payloads require a non-default `HCX_MASK_KEY`.
- Masking is deterministic, so the same sensitive value keeps the same pseudonym inside an export.
- Text masking covers IP addresses, MAC addresses, and email addresses.
- Sensitive Home Assistant attribute values are masked by key hints, including friendly names, exact location, host/network identifiers, serial-like identifiers, and user/person fields.
- Privacy coverage scans state and attribute metadata for maskable keys and text patterns, then returns counters only.

## UI workbenches

- Summary cards show entity, availability, battery, noise, recorder, and domain-health signals.
- Recorder/logbook volume shows likely database/logbook hotspots and estimated daily state volume.
- Privacy/export status shows whether export endpoints are unlocked and how many sensitive signals were detected.
- Export workbench loads short/deep AI payloads and supports copying targeted slices.
- Diagnostics workbench loads and copies the admin diagnostics payload for support handovers.

## Near-term roadmap

- Add recorder/logbook-backed volume analytics
- Add battery-focused diagnostics
- Add i18n translation bundles
- Add richer graph/relationship model
