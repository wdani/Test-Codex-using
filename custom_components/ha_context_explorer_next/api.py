from __future__ import annotations

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .service import build_ai_export_payload, build_ideas_payload, build_snapshot_payload


class SummaryView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/summary"
    name = "api:ha_context_explorer_next:summary"
    requires_auth = True

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        return self.json(build_snapshot_payload(list(hass.states.async_all())))


class ExportView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/export/ai_context"
    name = "api:ha_context_explorer_next:export_ai_context"
    requires_auth = True

    async def get(self, request):
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message("Admin access required", status_code=403)

        hass: HomeAssistant = request.app["hass"]
        return self.json(build_ai_export_payload(list(hass.states.async_all())))


class IdeasView(HomeAssistantView):
    url = "/api/ha_context_explorer_next/ideas"
    name = "api:ha_context_explorer_next:ideas"
    requires_auth = True

    async def get(self, request):
        return self.json(build_ideas_payload())


def async_register_api(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if state.get("api_registered"):
        return
    hass.http.register_view(SummaryView)
    hass.http.register_view(ExportView)
    hass.http.register_view(IdeasView)
    state["api_registered"] = True
