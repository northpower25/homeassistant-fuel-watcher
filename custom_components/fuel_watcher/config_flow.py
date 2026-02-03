"""
Commit: feat(config_flow): add vehicle_name and vehicle entity selection
(odometer, fuel level, location, consumption), Threshold percent and absolut 

Fuel Watcher – Config Flow
--------------------------
Erweitert um:
- vehicle_name (Kennzeichen oder Fahrzeugname)
- entity_odometer
- entity_fuel_level
- entity_location
- entity_consumption
- PRICE_DROP_PERCENT_THRESHOLD
- PRICE_DROP_ABSOLUTE_THRESHOLD
Diese Werte werden NICHT als eigene Entitäten erzeugt,
sondern Fuel Watcher liest die Daten direkt aus den angegebenen Entitäten.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    CONF_TANKERKOENIG_API,
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_RADIUS,
    CONF_FUEL_TYPE,
    CONF_VEHICLE_NAME,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_CONSUMPTION,
)


def _get_all_entities(hass: HomeAssistant):
    """Return list of all entities for dropdown selection."""
    registry = er.async_get(hass)
    return [
        (entity.entity_id, entity.entity_id)
        for entity in registry.entities.values()
    ]


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Main config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        hass = self.hass

        if user_input is not None:
            return self.async_create_entry(title=user_input.get(CONF_VEHICLE_NAME), data=user_input)

        entities = _get_all_entities(hass)

        schema = vol.Schema(
            {
                vol.Required(CONF_VEHICLE_NAME): str,
                vol.Required(CONF_TANKERKOENIG_API): str,
                vol.Required(CONF_TELEGRAM_TOKEN): str,
                vol.Required(CONF_TELEGRAM_CHAT_ID): str,
                vol.Required(CONF_RADIUS, default=5): int,
                vol.Required(CONF_FUEL_TYPE, default="e5"): vol.In(["e5", "e10", "diesel"]),

                # Fahrzeugdaten
                vol.Optional(CONF_ENTITY_RANGE): vol.In(entities),
                vol.Optional(CONF_ENTITY_ODOMETER): vol.In(entities),
                vol.Optional(CONF_ENTITY_FUEL_LEVEL): vol.In(entities),
                vol.Optional(CONF_ENTITY_LOCATION): vol.In(entities),
                vol.Optional(CONF_ENTITY_CONSUMPTION): vol.In(entities),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)


class FuelWatcherOptionsFlow(config_entries.OptionsFlow):
    """Options flow."""

    def __init__(self, config_entry):
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        hass = self.hass

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entities = _get_all_entities(hass)

        schema = vol.Schema(
            {
                # Fahrzeugdaten erneut konfigurierbar
                vol.Optional(
                    CONF_ENTITY_RANGE,
                    default=self.entry.options.get(CONF_ENTITY_RANGE, self.entry.data.get(CONF_ENTITY_RANGE)),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_ODOMETER,
                    default=self.entry.options.get(CONF_ENTITY_ODOMETER, self.entry.data.get(CONF_ENTITY_ODOMETER)),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_FUEL_LEVEL,
                    default=self.entry.options.get(CONF_ENTITY_FUEL_LEVEL, self.entry.data.get(CONF_ENTITY_FUEL_LEVEL)),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_LOCATION,
                    default=self.entry.options.get(CONF_ENTITY_LOCATION, self.entry.data.get(CONF_ENTITY_LOCATION)),
                ): vol.In(entities),

                vol.Optional(
                    CONF_ENTITY_CONSUMPTION,
                    default=self.entry.options.get(CONF_ENTITY_CONSUMPTION, self.entry.data.get(CONF_ENTITY_CONSUMPTION)),
                ): vol.In(entities),
                
                vol.Optional(
                    CONF_PRICE_DROP_PERCENT_THRESHOLD, 
                    default=5): float,
                
                vol.Optional(
                    CONF_PRICE_DROP_ABSOLUTE_THRESHOLD, 
                    default=0.10): float,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
