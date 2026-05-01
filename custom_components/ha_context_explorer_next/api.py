from __future__ import annotations

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .privacy_key import async_build_privacy_key_backup, async_get_privacy_key_context, async_rotate_privacy_key
from .service import build_ai_export_payload, build_diagnostics_payload, build_ideas_payload, build_snapshot_payload


def _integration_enabled(hass: HomeAssistant) -> bool:
    state = hass.data.get(DOMAIN, {})
    return bool(state.get("enabled", False))


def _require_admin(view: HomeAssistantView, request):
    user = request.get("hass_user")
    if user is None or not user.is_admin:
        return view.json_message("Admin access required", status_code=403)
    return None


class SummaryView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/summary"
    name = "api:ha_context_explorer_next:summary"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        key_context = await async_get_privacy_key_context(hass)
        return self.json(build_snapshot_payload(list(hass.states.async_all()), **key_context))


class ExportView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/export/ai_context"
    name = "api:ha_context_explorer_next:export_ai_context"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        try:
            key_context = await async_get_privacy_key_context(hass)
            return self.json(build_ai_export_payload(list(hass.states.async_all()), level="deep", **key_context))
        except ValueError as exc:
            return self.json_message(str(exc), status_code=412)


class ExportLevelView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/export/ai_context/{level}"
    name = "api:ha_context_explorer_next:export_ai_context_level"
    requires_auth = True

    async def get(self, request, level):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        try:
            key_context = await async_get_privacy_key_context(hass)
            return self.json(build_ai_export_payload(list(hass.states.async_all()), level=level, **key_context))
        except ValueError as exc:
            return self.json_message(str(exc), status_code=412)


class IdeasView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/ideas"
    name = "api:ha_context_explorer_next:ideas"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        return self.json(build_ideas_payload())


class DiagnosticsView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/diagnostics"
    name = "api:ha_context_explorer_next:diagnostics"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        key_context = await async_get_privacy_key_context(hass)
        return self.json(build_diagnostics_payload(list(hass.states.async_all()), **key_context))


class PrivacyKeyBackupView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/privacy/key/backup"
    name = "api:ha_context_explorer_next:privacy_key_backup"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        return self.json(await async_build_privacy_key_backup(hass))


class PrivacyKeyRotateView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/privacy/key/rotate"
    name = "api:ha_context_explorer_next:privacy_key_rotate"
    requires_auth = True

    async def post(self, request):
        hass: HomeAssistant = request.app["hass"]
        if not _integration_enabled(hass):
            return self.json_message("Integration disabled", status_code=503)

        denied = _require_admin(self, request)
        if denied:
            return denied

        try:
            return self.json(await async_rotate_privacy_key(hass))
        except ValueError as exc:
            return self.json_message(str(exc), status_code=409)


def async_register_api(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if state.get("api_registered"):
        return
    hass.http.register_view(SummaryView)
    hass.http.register_view(ExportView)
    hass.http.register_view(ExportLevelView)
    hass.http.register_view(IdeasView)
    hass.http.register_view(DiagnosticsView)
    hass.http.register_view(PrivacyKeyBackupView)
    hass.http.register_view(PrivacyKeyRotateView)
    state["api_registered"] = True
