"""Websocket API for the Notification History panel."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DATA_WS_REGISTERED, DOMAIN, WS_CLEAR, WS_LIST, WS_SUBSCRIBE

if TYPE_CHECKING:
    from .coordinator import NotifyHistoryManager


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register websocket commands once (they cannot be unregistered)."""
    if hass.data.get(DATA_WS_REGISTERED):
        return
    hass.data[DATA_WS_REGISTERED] = True
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_clear)
    websocket_api.async_register_command(hass, ws_subscribe)


def _manager(hass: HomeAssistant) -> NotifyHistoryManager | None:
    """Return the manager if the integration is currently loaded."""
    manager = hass.data.get(DOMAIN)
    return manager if manager is not None and not isinstance(manager, bool) else None


@websocket_api.websocket_command({vol.Required("type"): WS_LIST})
@callback
def ws_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return all stored notification records."""
    manager = _manager(hass)
    connection.send_result(
        msg["id"], {"records": manager.records if manager else []}
    )


@websocket_api.websocket_command({vol.Required("type"): WS_CLEAR})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_clear(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Clear the notification history."""
    manager = _manager(hass)
    if manager is not None:
        await manager.async_clear()
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): WS_SUBSCRIBE})
@callback
def ws_subscribe(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Push new notification records to the subscribed client."""
    manager = _manager(hass)
    if manager is None:
        connection.send_error(msg["id"], "not_loaded", "Integration not loaded")
        return

    @callback
    def forward(record: dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], record))

    connection.subscriptions[msg["id"]] = manager.async_subscribe(forward)
    connection.send_result(msg["id"])
