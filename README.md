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

## Export levels

Two admin-only export levels are available:

- `deep` (default): full payload with deep context
- `short`: compact payload for quick LLM prompts

Endpoints:

- `/api/ha_context_explorer_next/export/ai_context`
- `/api/ha_context_explorer_next/export/ai_context/short`
- `/api/ha_context_explorer_next/export/ai_context/deep`
