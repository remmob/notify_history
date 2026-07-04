"""Constants for the Notification History integration."""

from __future__ import annotations

DOMAIN = "notify_history"
VERSION = "1.0.1"  # keep in sync with manifest.json; used for JS cache-busting

STORAGE_KEY = f"{DOMAIN}.history"
STORAGE_VERSION = 1
SAVE_DELAY = 10  # seconds, debounce for Store writes

CONF_MAX_AGE_DAYS = "max_age_days"
CONF_MAX_ENTRIES = "max_entries"
CONF_IGNORED_SERVICES = "ignored_services"
DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_MAX_ENTRIES = 200

PANEL_URL_PATH = "notify-history"
PANEL_TITLE = "Notifications"
PANEL_ICON = "mdi:message-badge-outline"
STATIC_URL = "/notify_history_static"
PANEL_JS = f"{STATIC_URL}/notify-history-panel.js"

WS_LIST = f"{DOMAIN}/list"
WS_CLEAR = f"{DOMAIN}/clear"
WS_SUBSCRIBE = f"{DOMAIN}/subscribe"

SOURCE_NOTIFY = "notify"
SOURCE_PERSISTENT = "persistent_notification"

DATA_STATIC_REGISTERED = f"{DOMAIN}_static_registered"
DATA_WS_REGISTERED = f"{DOMAIN}_ws_registered"
