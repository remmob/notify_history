[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![nl](https://img.shields.io/badge/lang-nl-orange.svg)](README.nl.md)

# Notification History for Home Assistant

A Home Assistant custom integration that records all `notify.*` service calls and persistent notifications in a local store and shows them in a searchable sidebar panel. Never wonder again which notification was sent, when, and to whom.

> **Disclaimer**: This is an independent, community-built integration. It is not affiliated with, endorsed by, or supported by Nabu Casa or the Home Assistant project. The software is provided as-is (see [LICENSE](LICENSE)).

## Features

- Records every `notify.*` service call (mobile app push, `notify.send_message` entities, and any other notify platform) including title, message, recipient and timestamp.
- Records persistent notifications, including ones created programmatically by other integrations.
- Sidebar panel **Notifications** with:
  - Free-text search across title, message, recipient and service.
  - Filter by recipient and by date (today / last 7 days).
  - Live updates: new notifications appear in the panel instantly, no refresh needed.
  - Expandable details per record (service called, extra data payload, triggering user).
  - Admin-only "Clear history" action.
- Friendly recipient names: `notify.mobile_app_*` services and `notify.send_message` entity targets are resolved to their device or entity names.
- Configurable retention: maximum age in days (default 7, up to 365) and maximum number of entries (default 200, up to 5000).
- Ignore list: exclude specific notify services from being recorded.
- Fully local: history is stored in Home Assistant's own storage (`.storage`), nothing leaves your machine.
- Set up and reconfigured entirely through the Home Assistant UI - no YAML.

## Installation

### HACS Custom Repository

1. Open HACS in Home Assistant.
2. Click the three dots menu (⋮) in the top right corner.
3. Select 'Custom repositories'.
4. Add this repository URL: `https://github.com/remmob/notify_history`.
5. Set the category to **Integration**.
6. Click 'Add' to save.

See the [official HACS documentation](https://hacs.xyz/docs/faq/custom_repositories/) for more details.

### Manual

1. Download or copy the `notify_history` folder from this repository:
	[`custom_components/notify_history`](custom_components/notify_history)
2. Place this folder in your Home Assistant installation under:
	`config/custom_components/notify_history`
3. Restart Home Assistant.
4. Add the integration via the Integrations screen in the Home Assistant UI.

More info and updates:
- [GitHub: remmob/notify_history](https://github.com/remmob/notify_history)

## Adding the Integration

Go to the Integrations page in Home Assistant and click on "Add Integration". Search for "Notification History" and select it. There is nothing to configure during setup - confirm, and the **Notifications** panel appears in the sidebar. Only one instance of the integration can be added.

## Using the Panel

Open **Notifications** in the sidebar. The newest notifications are shown at the top; new ones appear in real time.

- Use the search box to filter on any text in the title, message, recipient or service name.
- Use the recipient dropdown to show only notifications sent to a specific device or entity.
- Use the date dropdown to limit the list to today or the last 7 days.
- Click a record to expand it and see the service that was called, the extra `data` payload (capped at 1 kB) and, when available, the user that triggered it.
- Administrators can wipe the entire history with the "Clear history" button (with confirmation).

## Configuring the Integration

All settings can be changed after setup, without removing the integration. Open the integration's entry and click the gear icon.

- **Maximum age (days)**: records older than this are pruned automatically (1-365, default 7).
- **Maximum entries**: when the history grows beyond this, the oldest records are dropped (10-5000, default 200).
- **Ignored services**: pick (or type) notify services whose calls should not be recorded, e.g. a noisy TTS target.

## How It Works

- `notify.*` service calls are captured from the Home Assistant event bus; calls without a `message` are ignored.
- Persistent notifications are captured through the persistent notification component itself, so notifications created by other integrations (not via a service call) are recorded too. Duplicates within a 5-second window are suppressed.
- History is persisted to `.storage/notify_history.history` with a debounced write, and pruned on every new record according to your retention settings.
- The panel is a self-contained web component served by the integration; it communicates over the Home Assistant websocket API and renders all content XSS-safe. A minimal markdown subset (bold, italic, links) in messages is supported.

## Privacy

Notification content can be sensitive. Everything this integration stores stays on your Home Assistant instance, in a private storage file readable only by Home Assistant. Clearing the history removes the stored records permanently.
