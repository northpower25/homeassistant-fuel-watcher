import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry
from .const import *

class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Fuel Watcher", data=user_input)

        er = entity_registry.async_get(self.hass)
        entities = sorted(er.entities.keys())

        schema = vol.Schema({
            vol.Required(CONF_TANKERKOENIG_API): str,
            vol.Required(CONF_TELEGRAM_TOKEN): str,
            vol.Required(CONF_TELEGRAM_CHAT_ID): str,
            vol.Required(CONF_PLZ): str,
            vol.Optional(CONF_RADIUS, default=5): int,
            vol.Optional(CONF_FUEL, default="e5"): vol.In(
                ["e5", "e10", "diesel", "superplus", "lpg", "cng"]
            ),

            vol.Optional(CONF_PRICE_THRESHOLD, default=0.0): float,
            vol.Optional(CONF_DISTANCE_THRESHOLD, default=10.0): float,

            vol.Optional(CONF_ENTITY_FUEL_LEVEL): vol.In(entities),
            vol.Optional(CONF_ENTITY_RANGE): vol.In(entities),
            vol.Optional(CONF_ENTITY_CONSUMPTION): vol.In(entities),
            vol.Optional(CONF_ENTITY_LOCATION): vol.In(entities),
        })

        return self.async_show_form(step_id="user", data_schema=schema)
