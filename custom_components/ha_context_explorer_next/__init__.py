from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import async_register_api
from .const import DOMAIN, PANEL_ICON, PANEL_MODULE_URL, PANEL_TITLE, PANEL_URL, PLATFORMS
from .privacy_key import async_load_or_create_privacy_key


def _module_path() -> str:
    return str(Path(__file__).parent / "www" / "app.js")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    state = hass.data.setdefault(DOMAIN, {})
    state["enabled"] = True
    await async_load_or_create_privacy_key(hass)

    if not state.get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_MODULE_URL, _module_path(), cache_headers=False)]
        )
        state["static_registered"] = True

    async_register_api(hass)

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        config={
            "_panel_custom": {
                "name": "ha-context-explorer-next-panel",
                "embed_iframe": False,
                "module_url": PANEL_MODULE_URL,
            }
        },
        require_admin=True,
    )

    state["panel_registered"] = True
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    state = hass.data.setdefault(DOMAIN, {})
    if unload_ok and state.get("panel_registered"):
        async_remove_panel(hass, PANEL_URL.strip("/"))
        state["panel_registered"] = False
    if unload_ok:
        state["enabled"] = False
    return unload_ok
