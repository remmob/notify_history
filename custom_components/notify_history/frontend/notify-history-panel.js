/* Notification History panel.
   Self-contained web component: no external imports, no build step.
   All record fields are rendered via textContent (never innerHTML) to stay
   XSS-safe; a minimal markdown subset (bold/italic/links) is built from
   DOM nodes per segment. */

const TRANSLATIONS = {
  en: {
    title: "Notification History",
    search: "Search...",
    allRecipients: "All recipients",
    allDates: "Any time",
    today: "Today",
    last7: "Last 7 days",
    clear: "Clear history",
    clearConfirm: "Delete the entire notification history?",
    empty: "No notifications recorded yet.",
    noMatches: "No notifications match the current filters.",
    loadError: "Could not load notification history:",
    details: "Details",
    sentBy: "sent by",
  },
  nl: {
    title: "Notificatiehistorie",
    search: "Zoeken...",
    allRecipients: "Alle ontvangers",
    allDates: "Alle datums",
    today: "Vandaag",
    last7: "Afgelopen 7 dagen",
    clear: "Historie wissen",
    clearConfirm: "De volledige notificatiehistorie verwijderen?",
    empty: "Nog geen notificaties vastgelegd.",
    noMatches: "Geen notificaties voldoen aan de huidige filters.",
    loadError: "Kan notificatiehistorie niet laden:",
    details: "Details",
    sentBy: "verzonden door",
  },
};

/* Pick the string table matching the user's profile language. */
function getStrings(hass) {
  const lang =
    (hass && hass.locale && hass.locale.language) ||
    (hass && hass.language) ||
    "en";
  return lang.startsWith("nl") ? TRANSLATIONS.nl : TRANSLATIONS.en;
}

const LINK_RE = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/;
const BOLD_RE = /\*\*([^*]+)\*\*/;
const ITALIC_RE = /\*([^*]+)\*/;

class NotifyHistoryPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._records = [];
    this._query = "";
    this._recipient = "";
    this._dateFilter = "";
    this._unsub = null;
    this._initialized = false;
    this._narrow = false;
    this._strings = TRANSLATIONS.en;
  }

  /* Called by Home Assistant on every state change. */
  set hass(hass) {
    this._hass = hass;
    this._strings = getStrings(hass);
    if (!this._initialized) {
      this._initialized = true;
      this._init();
    }
    this._updateMenuButton();
  }

  /* Set by Home Assistant when the viewport is narrow (mobile). */
  set narrow(value) {
    this._narrow = value;
    this._updateMenuButton();
  }

  get narrow() {
    return this._narrow;
  }

  /* Show the sidebar toggle only on narrow (mobile) screens,
     matching regular dashboard behaviour. */
  _updateMenuButton() {
    const btn = this.shadowRoot && this.shadowRoot.getElementById("menu");
    if (!btn) {
      return;
    }
    btn.hidden = !this._narrow;
  }

  disconnectedCallback() {
    if (this._unsub) {
      this._unsub();
      this._unsub = null;
    }
  }

  async _init() {
    this._renderShell();
    try {
      const resp = await this._hass.connection.sendMessagePromise({
        type: "notify_history/list",
      });
      this._records = (resp.records || []).slice().reverse(); // newest first
      this._unsub = await this._hass.connection.subscribeMessage(
        (record) => {
          this._records.unshift(record);
          this._renderRecipientOptions();
          this._renderList();
        },
        { type: "notify_history/subscribe" }
      );
    } catch (err) {
      this._renderError(err);
      return;
    }
    this._renderRecipientOptions();
    this._renderList();
  }

  _renderShell() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          height: 100%;
          overflow-y: auto;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        header {
          position: sticky;
          top: 0;
          z-index: 2;
          display: flex;
          align-items: center;
          justify-content: space-between;
          /* Keep the title clear of the phone camera / status bar area. */
          height: calc(56px + env(safe-area-inset-top, 0px));
          box-sizing: border-box;
          padding: env(safe-area-inset-top, 0px) 16px 0;
          background: var(--app-header-background-color, var(--primary-background-color));
          color: var(--app-header-text-color, var(--primary-text-color));
          border-bottom: 1px solid var(--app-header-border-bottom, transparent);
          font-size: 20px;
          font-weight: 400;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 4px;
          min-width: 0;
        }
        #menu {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: inherit;
          padding: 8px;
          margin-left: -8px;
          border-radius: 50%;
          cursor: pointer;
        }
        /* Explicit display would otherwise override the hidden attribute. */
        #menu[hidden] { display: none; }
        #menu:hover { background: rgba(127, 127, 127, 0.2); }
        #menu svg { width: 24px; height: 24px; fill: currentColor; }
        header button {
          background: var(--ha-card-background, var(--card-background-color));
          color: var(--primary-text-color);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color));
          border-radius: 8px;
          padding: 6px 12px;
          font-size: 13px;
          cursor: pointer;
        }
        header button:hover { opacity: 0.8; }
        .toolbar {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          padding: 12px 16px;
          position: sticky;
          top: calc(56px + env(safe-area-inset-top, 0px));
          z-index: 1;
          background: var(--primary-background-color);
        }
        input, select {
          background: var(--ha-card-background, var(--card-background-color));
          color: inherit;
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color));
          border-radius: 8px;
          padding: 8px;
          font-size: 14px;
        }
        input[type="search"] { flex: 1; min-width: 180px; }
        .day {
          padding: 12px 16px 0;
          font-weight: 600;
          color: var(--secondary-text-color);
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: var(--ha-card-border-width, 1px) solid
            var(--ha-card-border-color, var(--divider-color));
          margin: 8px 16px;
          padding: 12px;
        }
        .card .title { font-weight: 600; margin-bottom: 4px; }
        .card .message { white-space: pre-wrap; word-break: break-word; }
        .card .message a { color: var(--primary-color); }
        .card img.attachment {
          display: block;
          max-width: min(320px, 100%);
          border-radius: 8px;
          margin-top: 8px;
        }
        .card details {
          margin-top: 8px;
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        .card details pre {
          white-space: pre-wrap;
          word-break: break-word;
          margin: 4px 0 0;
        }
        .meta {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          flex-wrap: wrap;
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 8px;
        }
        .empty {
          padding: 32px;
          text-align: center;
          color: var(--secondary-text-color);
        }
        .error { color: var(--error-color, #db4437); padding: 16px; }
      </style>
      <header>
        <div class="header-left">
          <button id="menu" aria-label="Menu" hidden>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/>
            </svg>
          </button>
          <span class="header-title"></span>
        </div>
        <button id="clear" hidden></button>
      </header>
      <div class="toolbar">
        <input type="search" id="search">
        <select id="recipient"></select>
        <select id="date">
          <option value=""></option>
          <option value="today"></option>
          <option value="7d"></option>
        </select>
      </div>
      <div id="list"></div>`;

    const root = this.shadowRoot;
    root.querySelector(".header-title").textContent = this._strings.title;
    root.getElementById("menu").addEventListener("click", () => {
      this.dispatchEvent(
        new Event("hass-toggle-menu", { bubbles: true, composed: true })
      );
    });
    this._updateMenuButton();
    const search = root.getElementById("search");
    search.placeholder = this._strings.search;
    search.addEventListener("input", (e) => {
      this._query = e.target.value;
      this._renderList();
    });
    root.getElementById("recipient").addEventListener("change", (e) => {
      this._recipient = e.target.value;
      this._renderList();
    });
    const dateSelect = root.getElementById("date");
    const dateLabels = [
      this._strings.allDates,
      this._strings.today,
      this._strings.last7,
    ];
    [...dateSelect.options].forEach((opt, i) => (opt.textContent = dateLabels[i]));
    dateSelect.addEventListener("change", (e) => {
      this._dateFilter = e.target.value;
      this._renderList();
    });

    const clearBtn = root.getElementById("clear");
    clearBtn.textContent = this._strings.clear;
    if (this._hass.user && this._hass.user.is_admin) {
      clearBtn.hidden = false;
      clearBtn.addEventListener("click", () => this._clear());
    }
  }

  async _clear() {
    if (!window.confirm(this._strings.clearConfirm)) {
      return;
    }
    try {
      await this._hass.connection.sendMessagePromise({
        type: "notify_history/clear",
      });
      this._records = [];
      this._renderRecipientOptions();
      this._renderList();
    } catch (err) {
      this._renderError(err);
    }
  }

  _renderError(err) {
    const list = this.shadowRoot.getElementById("list");
    list.textContent = "";
    const div = document.createElement("div");
    div.className = "error";
    div.textContent = `${this._strings.loadError} ${err && err.message ? err.message : err}`;
    list.appendChild(div);
  }

  _renderRecipientOptions() {
    const select = this.shadowRoot.getElementById("recipient");
    const current = this._recipient;
    const recipients = [...new Set(this._records.map((r) => r.recipient))].sort();
    select.textContent = "";
    const all = document.createElement("option");
    all.value = "";
    all.textContent = this._strings.allRecipients;
    select.appendChild(all);
    for (const recipient of recipients) {
      const opt = document.createElement("option");
      opt.value = recipient;
      opt.textContent = recipient;
      select.appendChild(opt);
    }
    if (recipients.includes(current)) {
      select.value = current;
    } else {
      this._recipient = "";
    }
  }

  _filtered() {
    const q = this._query.toLowerCase();
    const now = new Date();
    return this._records.filter((r) => {
      if (
        q &&
        !`${r.title || ""} ${r.message} ${r.recipient}`.toLowerCase().includes(q)
      ) {
        return false;
      }
      if (this._recipient && r.recipient !== this._recipient) {
        return false;
      }
      if (this._dateFilter) {
        const d = new Date(r.when);
        if (
          this._dateFilter === "today" &&
          d.toDateString() !== now.toDateString()
        ) {
          return false;
        }
        if (this._dateFilter === "7d" && now - d > 7 * 864e5) {
          return false;
        }
      }
      return true;
    });
  }

  _renderList() {
    const list = this.shadowRoot.getElementById("list");
    list.textContent = "";
    const records = this._filtered();

    if (!records.length) {
      const div = document.createElement("div");
      div.className = "empty";
      div.textContent = this._records.length
        ? this._strings.noMatches
        : this._strings.empty;
      list.appendChild(div);
      return;
    }

    const locale =
      (this._hass && this._hass.locale && this._hass.locale.language) ||
      navigator.language;
    const dayFormat = new Intl.DateTimeFormat(locale, {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    const timeFormat = new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
    });

    let currentDay = "";
    for (const record of records) {
      const when = new Date(record.when);
      const day = dayFormat.format(when);
      if (day !== currentDay) {
        currentDay = day;
        const header = document.createElement("div");
        header.className = "day";
        header.textContent = day;
        list.appendChild(header);
      }
      list.appendChild(this._renderCard(record, timeFormat.format(when)));
    }
  }

  _renderCard(record, time) {
    const card = document.createElement("div");
    card.className = "card";

    if (record.title) {
      const title = document.createElement("div");
      title.className = "title";
      title.textContent = record.title;
      card.appendChild(title);
    }

    const message = document.createElement("div");
    message.className = "message";
    renderInlineMarkdown(record.message || "", message);
    card.appendChild(message);

    const imageUrl = record.data && record.data.image;
    if (typeof imageUrl === "string" && isSafeImageUrl(imageUrl)) {
      const img = document.createElement("img");
      img.className = "attachment";
      img.src = imageUrl;
      img.loading = "lazy";
      img.alt = record.title || "notification attachment";
      card.appendChild(img);
    }

    if (record.data && Object.keys(record.data).length) {
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = this._strings.details;
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(record.data, null, 2);
      details.appendChild(summary);
      details.appendChild(pre);
      card.appendChild(details);
    }

    const meta = document.createElement("div");
    meta.className = "meta";
    const recipient = document.createElement("span");
    recipient.textContent = record.recipient;
    const timestamp = document.createElement("span");
    timestamp.textContent = time;
    meta.appendChild(recipient);
    meta.appendChild(timestamp);
    card.appendChild(meta);

    return card;
  }
}

/* Render a minimal, safe markdown subset (links, bold, italic) as DOM nodes.
   Everything else stays plain text; raw HTML in messages is never parsed. */
function renderInlineMarkdown(text, parent) {
  let rest = text;
  while (rest.length) {
    const candidates = [
      { match: LINK_RE.exec(rest), type: "link" },
      { match: BOLD_RE.exec(rest), type: "bold" },
      { match: ITALIC_RE.exec(rest), type: "italic" },
    ]
      .filter((c) => c.match)
      .sort((a, b) => a.match.index - b.match.index);

    if (!candidates.length) {
      parent.appendChild(document.createTextNode(rest));
      return;
    }

    const { match, type } = candidates[0];
    if (match.index > 0) {
      parent.appendChild(document.createTextNode(rest.slice(0, match.index)));
    }
    let node;
    if (type === "link") {
      node = document.createElement("a");
      node.href = match[2];
      node.target = "_blank";
      node.rel = "noreferrer noopener";
      node.textContent = match[1];
    } else {
      node = document.createElement(type === "bold" ? "b" : "i");
      node.textContent = match[1];
    }
    parent.appendChild(node);
    rest = rest.slice(match.index + match[0].length);
  }
}

function isSafeImageUrl(url) {
  return (
    url.startsWith("https://") ||
    url.startsWith("http://") ||
    (url.startsWith("/") && !url.startsWith("//"))
  );
}

if (!customElements.get("notify-history-panel")) {
  customElements.define("notify-history-panel", NotifyHistoryPanel);
}
