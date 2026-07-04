"""Capture, store and fan out notification history records."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any, Callable

from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util, slugify
from homeassistant.util.ulid import ulid_now

from .const import (
    CONF_IGNORED_SERVICES,
    CONF_MAX_AGE_DAYS,
    CONF_MAX_ENTRIES,
    DEFAULT_MAX_AGE_DAYS,
    DEFAULT_MAX_ENTRIES,
    SAVE_DELAY,
    SOURCE_NOTIFY,
    SOURCE_PERSISTENT,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

DEDUP_WINDOW = timedelta(seconds=5)
DATA_EXCERPT_LIMIT = 1000  # max serialized size of the stored data excerpt


class NotifyHistoryStore(Store[dict[str, Any]]):
    """Store subclass with a migration hook for future schema changes."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict
    ) -> dict:
        """Migrate stored data to the current schema version."""
        return old_data


class NotifyHistoryManager:
    """Listen for notifications, keep a pruned history and notify subscribers."""

    def __init__(self, hass: HomeAssistant, options: dict[str, Any]) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.options = options
        self._store = NotifyHistoryStore(hass, STORAGE_VERSION, STORAGE_KEY, private=True)
        self._records: list[dict[str, Any]] = []
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._unsubs: list[Callable[[], None]] = []

    async def async_setup(self) -> None:
        """Load stored history and register event listeners."""
        data = await self._store.async_load()
        self._records = (data or {}).get("records", [])
        self._prune()

        self._unsubs.append(
            self.hass.bus.async_listen(EVENT_CALL_SERVICE, self._handle_call_service)
        )

        # The persistent_notification dispatcher signal is not a formally public
        # API, so import defensively and degrade gracefully if it moves.
        try:
            from homeassistant.components.persistent_notification import (
                SIGNAL_PERSISTENT_NOTIFICATIONS_UPDATED,
            )
        except ImportError:
            _LOGGER.warning(
                "Persistent notification signal unavailable; only notify.* "
                "service calls will be recorded"
            )
        else:
            self._unsubs.append(
                async_dispatcher_connect(
                    self.hass,
                    SIGNAL_PERSISTENT_NOTIFICATIONS_UPDATED,
                    self._handle_persistent_notification_update,
                )
            )

    async def async_shutdown(self) -> None:
        """Detach listeners and flush pending records to disk."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._subscribers.clear()
        await self._store.async_save({"records": self._records})

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return the current history records, oldest first."""
        return self._records

    @callback
    def async_subscribe(
        self, target: Callable[[dict[str, Any]], None]
    ) -> Callable[[], None]:
        """Subscribe to new records; returns an unsubscribe callable."""
        self._subscribers.append(target)

        @callback
        def _unsubscribe() -> None:
            if target in self._subscribers:
                self._subscribers.remove(target)

        return _unsubscribe

    async def async_clear(self) -> None:
        """Remove all history records."""
        self._records = []
        await self._store.async_save({"records": []})

    @callback
    def _handle_call_service(self, event: Event) -> None:
        """Record notify.* service calls from the event bus."""
        if event.data.get("domain") != "notify":
            return
        service = event.data.get("service") or ""
        # persistent_notification is captured via the dispatcher signal instead,
        # which also covers notifications created programmatically.
        if service == "persistent_notification":
            return
        if service in self.options.get(CONF_IGNORED_SERVICES, []):
            return

        service_data = event.data.get("service_data")
        if not isinstance(service_data, dict):
            service_data = {}
        message = service_data.get("message")
        if message is None:
            return

        self._add_record(
            {
                "id": ulid_now(),
                "when": dt_util.utcnow().isoformat(),
                "source": SOURCE_NOTIFY,
                "service": f"notify.{service}",
                "recipient": ", ".join(self._resolve_recipients(service, service_data)),
                "title": _as_str(service_data.get("title")),
                "message": _as_str(message) or "",
                "data": _sanitize(service_data.get("data")),
                "user_id": event.context.user_id,
            }
        )

    @callback
    def _handle_persistent_notification_update(
        self, update_type: Any, notifications: dict[str, Any]
    ) -> None:
        """Record newly added persistent notifications."""
        # Compare by value to avoid importing the UpdateType enum.
        if str(getattr(update_type, "value", update_type)).lower() != "added":
            return
        for notification in notifications.values():
            message = _as_str(notification.get("message")) or ""
            if self._is_duplicate(message):
                continue
            created = notification.get("created_at")
            self._add_record(
                {
                    "id": ulid_now(),
                    "when": created.isoformat()
                    if created is not None
                    else dt_util.utcnow().isoformat(),
                    "source": SOURCE_PERSISTENT,
                    "service": "persistent_notification",
                    "recipient": "Persistent notification",
                    "title": _as_str(notification.get("title")),
                    "message": message,
                    "data": {"notification_id": notification.get("notification_id")},
                    "user_id": None,
                }
            )

    def _is_duplicate(self, message: str) -> bool:
        """Return True if this persistent notification was just recorded."""
        now = dt_util.utcnow()
        for record in reversed(self._records[-5:]):
            if record["source"] != SOURCE_PERSISTENT or record["message"] != message:
                continue
            recorded_at = dt_util.parse_datetime(record["when"])
            if recorded_at is not None and now - recorded_at < DEDUP_WINDOW:
                return True
        return False

    def _resolve_recipients(self, service: str, service_data: dict) -> list[str]:
        """Map a notify service call to friendly recipient names."""
        if service == "send_message":
            entity_ids = service_data.get("entity_id") or []
            if isinstance(entity_ids, str):
                entity_ids = [entity_ids]
            recipients = []
            for entity_id in entity_ids:
                state = self.hass.states.get(entity_id)
                recipients.append(
                    state.attributes.get("friendly_name", entity_id)
                    if state
                    else entity_id
                )
            return recipients or ["notify.send_message"]

        if service.startswith("mobile_app_"):
            device_slug = service.removeprefix("mobile_app_")
            for entry in self.hass.config_entries.async_entries("mobile_app"):
                name = entry.data.get("device_name") or entry.title
                if name and slugify(name) == device_slug:
                    return [name]

        return [service.replace("_", " ")]

    @callback
    def _add_record(self, record: dict[str, Any]) -> None:
        """Append a record, prune, schedule a save and notify subscribers."""
        self._records.append(record)
        self._prune()
        self._store.async_delay_save(lambda: {"records": self._records}, SAVE_DELAY)
        for send in list(self._subscribers):
            send(record)

    def _prune(self) -> None:
        """Drop records older than max_age_days and beyond max_entries."""
        max_entries = int(self.options.get(CONF_MAX_ENTRIES, DEFAULT_MAX_ENTRIES))
        max_age_days = int(self.options.get(CONF_MAX_AGE_DAYS, DEFAULT_MAX_AGE_DAYS))
        # All timestamps are UTC ISO 8601, so string comparison is chronological.
        cutoff = (dt_util.utcnow() - timedelta(days=max_age_days)).isoformat()
        self._records = [r for r in self._records if r["when"] >= cutoff]
        if len(self._records) > max_entries:
            self._records = self._records[-max_entries:]


def _as_str(value: Any) -> str | None:
    """Return the value as a string, preserving None."""
    return None if value is None else str(value)


def _sanitize(data: Any, limit: int = DATA_EXCERPT_LIMIT) -> dict | None:
    """Return a JSON-safe, size-capped copy of the notify data block."""
    if not isinstance(data, dict):
        return None
    try:
        text = json.dumps(data, default=str)
    except (TypeError, ValueError):
        return None
    if len(text) > limit:
        return {"_truncated": True}
    return json.loads(text)
