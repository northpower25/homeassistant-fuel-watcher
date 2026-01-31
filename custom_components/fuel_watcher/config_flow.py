import voluptuous as vol
from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_TANKERKOENIG_API,
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_PLZ,
    CONF_RADIUS,
    CONF_FUEL,
    CONF_SOURCE,
    CONF_PRICE_THRESHOLD,
    CONF_DISTANCE_THRESHOLD,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_ODOMETER,
    SUPPORTED_SOURCES,
)


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Fuel Watcher."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Fuel Watcher", data=user_input)

        # Alle Entity-Felder als Freitext (kein Entity-Registry-Zugriff) test
        schema = vol.Schema({
            vol.Required(CONF_TANKERKOENIG_API): str,
            vol.Required(CONF_TELEGRAM_TOKEN): str,
            vol.Required(CONF_TELEGRAM_CHAT_ID): str,
            vol.Required(CONF_PLZ): str,

            vol.Optional(CONF_RADIUS, default=5): vol.Coerce(int),
            vol.Optional(CONF_FUEL, default="e5"): vol.In(
                ["e5", "e10", "diesel", "superplus", "lpg", "cng"]
            ),

            vol.Optional(CONF_SOURCE, default="tankerkoenig"): vol.In(SUPPORTED_SOURCES),

            vol.Optional(CONF_PRICE_THRESHOLD, default=0.0): vol.Coerce(float),
            vol.Optional(CONF_DISTANCE_THRESHOLD, default=10.0): vol.Coerce(float),

            vol.Optional(CONF_ENTITY_FUEL_LEVEL): str,
            vol.Optional(CONF_ENTITY_RANGE): str,
            vol.Optional(CONF_ENTITY_CONSUMPTION): str,
            vol.Optional(CONF_ENTITY_ODOMETER): str,
            vol.Optional(CONF_ENTITY_LOCATION): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)
