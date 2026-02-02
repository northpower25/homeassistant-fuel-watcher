from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_TANKERKOENIG_API,
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_RADIUS,
    CONF_FUEL,
    CONF_SOURCE,
    SUPPORTED_SOURCES,
    CONF_TANK_HISTORY_RETENTION_MONTHS,
    DEFAULT_TANK_HISTORY_RETENTION_MONTHS,
)
from .tank_history import append_tank_event
from .notify import send_test_notification


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Fuel Watcher."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Fuel Watcher", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_TANKERKOENIG_API): str,
                vol.Required(CONF_TELEGRAM_TOKEN): str,
                vol.Required(CONF_TELEGRAM_CHAT_ID): str,
                vol.Required(CONF_RADIUS, default=5): vol.Coerce(int),
                vol.Required(CONF_FUEL, default="e5"): vol.In(["e5", "e10", "diesel", "superplus", "lpg", "cng"]),
                vol.Required(CONF_SOURCE, default="tankerkoenig"): vol.In(SUPPORTED_SOURCES),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FuelWatcherOptionsFlow(config_entry)


class FuelWatcherOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Fuel Watcher."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Testnachricht
            if user_input.get("test_notification"):
                await send_test_notification(self.hass, self.entry)
                user_input.pop("test_notification", None)

            # Tankvorgang erfassen
            price = user_input.pop("tank_event_price", None)
            liters = user_input.pop("tank_event_liters", None)
            total = user_input.pop("tank_event_total", None)
            odometer = user_input.pop("tank_event_odometer", None)

            if price:
                try:
                    price_f = float(price)
                    liters_f = float(liters) if liters else None
                    total_f = float(total) if total else None
                    odometer_f = float(odometer) if odometer else None
                except ValueError:
                    price_f = None
                    liters_f = None
                    total_f = None
                    odometer_f = None

                if price_f is not None:
                    append_tank_event(
                        self.hass,
                        self.entry,
                        price_per_liter=price_f,
                        liters=liters_f,
                        total_cost=total_f,
                        odometer=odometer_f,
                        source="manual",
                    )

            return self.async_create_entry(title="", data=user_input)

        data = self.entry.data
        options = self.entry.options

        def opt(key, default=None):
            return options.get(key, data.get(key, default))

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TANK_HISTORY_RETENTION_MONTHS,
                    default=opt(CONF_TANK_HISTORY_RETENTION_MONTHS, DEFAULT_TANK_HISTORY_RETENTION_MONTHS),
                ): vol.Coerce(int),
                vol.Optional("test_notification", default=False): bool,
                vol.Optional("tank_event_price", default=""): str,
                vol.Optional("tank_event_liters", default=""): str,
                vol.Optional("tank_event_total", default=""): str,
                vol.Optional("tank_event_odometer", default=""): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
