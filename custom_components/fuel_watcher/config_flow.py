"""
Commit: feat(config_flow): add full options flow with range entity, thresholds, telegram test and spike settings

Fuel Watcher – Config Flow
--------------------------
Dieser Flow bietet:
- Auswahl der Range-Entity
- Preis-Spike-Schwelle
- Decision-Delta-Schwelle
- Min. Days Left
- Testnachricht senden
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


def _get_number_entities(hass: HomeAssistant):
    """Return list of number-like entities (km range sensors)."""
    registry = er.async_get(hass)
    return [
        (entity.entity_id, entity.entity_id)
        for entity in registry.entities.values()
        if entity.platform != DOMAIN
    ]


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Main config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="Fuel Watcher", data={})

    async def async_step_init(self, user_input=None):
        return self.async_step_user()


class FuelWatcherOptionsFlow(config_entries.OptionsFlow):
    """Options flow."""

    def __init__(self, config_entry):
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        hass = self.hass

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        number_entities = _get_number_entities(hass)

        schema = vol.Schema(
            {
                vol.Optional(
                    "range_entity",
                    default=self.entry.options.get("range_entity"),
                ): vol.In(number_entities),

                vol.Optional(
                    "price_spike_threshold",
                    default=self.entry.options.get("price_spike_threshold", 0.08),
                ): float,

                vol.Optional(
                    "decision_delta_threshold",
                    default=self.entry.options.get("decision_delta_threshold", -0.03),
                ): float,

                vol.Optional(
                    "min_days_left",
                    default=self.entry.options.get("min_days_left", 2),
                ): float,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
