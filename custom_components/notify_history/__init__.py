"""Notification History integration.

Records all notify.* service calls and persistent notifications in a local
store and exposes them through a searchable sidebar panel.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import NotifyHistoryManager
from .panel import async_register_panel, async_unregister_panel
from .websocket import async_register_websocket


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notification History from a config entry."""
    options = {**entry.data, **entry.options}
    manager = NotifyHistoryManager(hass, options)
    await manager.async_setup()
    hass.data[DOMAIN] = manager

    async_register_websocket(hass)
    await async_register_panel(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    manager: NotifyHistoryManager | None = hass.data.pop(DOMAIN, None)
    if manager is not None:
        await manager.async_shutdown()
    async_unregister_panel(hass)
    return True
