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

## Privacy model

- Export payloads require a non-default `HCX_MASK_KEY`.
- Masking is deterministic, so the same sensitive value keeps the same pseudonym inside an export.
- Text masking covers IP addresses, MAC addresses, and email addresses.
- Sensitive Home Assistant attribute values are masked by key hints, including friendly names, exact location, host/network identifiers, serial-like identifiers, and user/person fields.

## Near-term roadmap

- Add recorder/logbook-backed volume analytics
- Add battery-focused diagnostics
- Add i18n translation bundles
- Add richer graph/relationship model
