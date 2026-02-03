"""
Commit: fix(config_flow): remove deprecated storage import and modernize options flow

Fuel Watcher – Config Flow
--------------------------
- Einrichtung der Integration
- Options-Flow für Fahrzeug-Entitäten, Thresholds und Templates
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_TANKERKOENIG_API,
    CONF_FUEL_TYPE,
    CONF_RADIUS,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_CONSUMPTION,
    CONF_PRICE_DROP_PERCENT_THRESHOLD,
    CONF_PRICE_DROP_ABSOLUTE_THRESHOLD,
    CONF_NOTIFY_MSG_TANKEN,
    CONF_NOTIFY_MSG_RANGE_DAYS,
    DEFAULT_NOTIFY_MSG_TANKEN,
    DEFAULT_NOTIFY_MSG_RANGE_DAYS,
)


FUEL_TYPES = ["e5", "e10", "diesel"]


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fuel Watcher."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial setup."""
        if user_input is not None:
            return self.async_create_entry(
                title="Fuel Watcher",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_TANKERKOENIG_API): str,
                vol.Required(CONF_FUEL_TYPE, default="e5"): vol.In(FUEL_TYPES),
                vol.Required(CONF_RADIUS, default=5): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, user_input=None):
        """Import from YAML (deprecated)."""
        return await self.async_step_user(user_input)


# ---------------------------------------------------------------------------
# OPTIONS FLOW
# ---------------------------------------------------------------------------

class FuelWatcherOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Fuel Watcher."""

    def __init__(self, config_entry):
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        """Main options menu."""
        hass: HomeAssistant = self.hass

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Alle Sensor-Entitäten laden
        entities = [
            e.entity_id
            for e in hass.states.async_all()
            if e.entity_id.startswith("sensor.")
            or e.entity_id.startswith("device_tracker.")
            or e.entity_id.startswith("number.")
            or e.entity_id.startswith("input_number.")
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENTITY_RANGE,
                    default=self.entry.options.get(CONF_ENTITY_RANGE)
                    or self.entry.data.get(CONF_ENTITY_RANGE),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_ODOMETER,
                    default=self.entry.options.get(CONF_ENTITY_ODOMETER)
                    or self.entry.data.get(CONF_ENTITY_ODOMETER),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_FUEL_LEVEL,
                    default=self.entry.options.get(CONF_ENTITY_FUEL_LEVEL)
                    or self.entry.data.get(CONF_ENTITY_FUEL_LEVEL),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_LOCATION,
                    default=self.entry.options.get(CONF_ENTITY_LOCATION)
                    or self.entry.data.get(CONF_ENTITY_LOCATION),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_CONSUMPTION,
                    default=self.entry.options.get(CONF_ENTITY_CONSUMPTION)
                    or self.entry.data.get(CONF_ENTITY_CONSUMPTION),
                ): vol.In(entities),

                # Strategy thresholds
                vol.Optional(
                    CONF_PRICE_DROP_PERCENT_THRESHOLD,
                    default=self.entry.options.get(CONF_PRICE_DROP_PERCENT_THRESHOLD, 5),
                ): float,

                vol.Optional(
                    CONF_PRICE_DROP_ABSOLUTE_THRESHOLD,
                    default=self.entry.options.get(CONF_PRICE_DROP_ABSOLUTE_THRESHOLD, 0.10),
                ): float,

                # Telegram templates
                vol.Optional(
                    CONF_NOTIFY_MSG_TANKEN,
                    default=self.entry.options.get(CONF_NOTIFY_MSG_TANKEN)
                    or DEFAULT_NOTIFY_MSG_TANKEN,
                ): str,

                vol.Optional(
                    CONF_NOTIFY_MSG_RANGE_DAYS,
                    default=self.entry.options.get(CONF_NOTIFY_MSG_RANGE_DAYS)
                    or DEFAULT_NOTIFY_MSG_RANGE_DAYS,
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
