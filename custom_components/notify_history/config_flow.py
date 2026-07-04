"""Config and options flow for the Notification History integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_IGNORED_SERVICES,
    CONF_MAX_AGE_DAYS,
    CONF_MAX_ENTRIES,
    DEFAULT_MAX_AGE_DAYS,
    DEFAULT_MAX_ENTRIES,
    DOMAIN,
)


class NotifyHistoryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of the integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user confirmation step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Notification History", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> NotifyHistoryOptionsFlow:
        """Return the options flow handler."""
        return NotifyHistoryOptionsFlow()


class NotifyHistoryOptionsFlow(OptionsFlow):
    """Handle retention and filtering options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and process the options form."""
        if user_input is not None:
            # NumberSelector returns floats; store clean ints.
            user_input[CONF_MAX_AGE_DAYS] = int(user_input[CONF_MAX_AGE_DAYS])
            user_input[CONF_MAX_ENTRIES] = int(user_input[CONF_MAX_ENTRIES])
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        notify_services = sorted(
            self.hass.services.async_services().get("notify", {})
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAX_AGE_DAYS,
                    default=options.get(CONF_MAX_AGE_DAYS, DEFAULT_MAX_AGE_DAYS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=365,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),
                vol.Required(
                    CONF_MAX_ENTRIES,
                    default=options.get(CONF_MAX_ENTRIES, DEFAULT_MAX_ENTRIES),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10,
                        max=5000,
                        step=10,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_IGNORED_SERVICES,
                    default=options.get(CONF_IGNORED_SERVICES, []),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=notify_services,
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
