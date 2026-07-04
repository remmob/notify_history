"""Sidebar panel and static file registration for Notification History."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_STATIC_REGISTERED,
    PANEL_ICON,
    PANEL_JS,
    PANEL_TITLE,
    PANEL_URL_PATH,
    STATIC_URL,
    VERSION,
)


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve the frontend files and add the sidebar panel."""
    # Static paths cannot be unregistered, so register them only once.
    if not hass.data.get(DATA_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    STATIC_URL,
                    str(Path(__file__).parent / "frontend"),
                    cache_headers=False,
                )
            ]
        )
        hass.data[DATA_STATIC_REGISTERED] = True

    if PANEL_URL_PATH not in hass.data.get("frontend_panels", {}):
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_URL_PATH,
            config={
                "_panel_custom": {
                    "name": "notify-history-panel",
                    "embed_iframe": False,
                    "trust_external": False,
                    "module_url": f"{PANEL_JS}?v={VERSION}",
                }
            },
            require_admin=False,
        )


@callback
def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel."""
    if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
