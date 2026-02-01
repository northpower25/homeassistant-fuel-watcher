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
    CONF_PRICE_THRESHOLD,
    CONF_DISTANCE_THRESHOLD,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_LOCATION,
    SUPPORTED_SOURCES,
)


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Fuel Watcher", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_TANKERKOENIG_API): str,
            vol.Required(CONF_TELEGRAM_TOKEN): str,
            vol.Required(CONF_TELEGRAM_CHAT_ID): str,

            vol.Required(CONF_RADIUS, default=5): vol.Coerce(int),
            vol.Required(CONF_FUEL, default="e5"): vol.In(["e5", "e10", "diesel", "superplus", "lpg", "cng"]),
            vol.Required(CONF_SOURCE, default="tankerkoenig"): vol.In(SUPPORTED_SOURCES),

            vol.Optional(CONF_PRICE_THRESHOLD, default=0.0): vol.Coerce(float),
            vol.Optional(CONF_DISTANCE_THRESHOLD, default=10.0): vol.Coerce(float),

            vol.Optional(CONF_ENTITY_FUEL_LEVEL, default=""): str,
            vol.Optional(CONF_ENTITY_RANGE, default=""): str,
            vol.Optional(CONF_ENTITY_CONSUMPTION, default=""): str,
            vol.Optional(CONF_ENTITY_ODOMETER, default=""): str,
            vol.Optional(CONF_ENTITY_LOCATION, default=""): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FuelWatcherOptionsFlow(config_entry)


class FuelWatcherOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.entry.data
        options = self.entry.options

        def opt(key, default=None):
            return options.get(key, data.get(key, default))

        schema = vol.Schema({
            vol.Required(CONF_RADIUS, default=opt(CONF_RADIUS, 5)): vol.Coerce(int),
            vol.Required(CONF_FUEL, default=opt(CONF_FUEL, "e5")): vol.In(["e5", "e10", "diesel", "superplus", "lpg", "cng"]),
            vol.Required(CONF_PRICE_THRESHOLD, default=opt(CONF_PRICE_THRESHOLD, 0.0)): vol.Coerce(float),
            vol.Required(CONF_DISTANCE_THRESHOLD, default=opt(CONF_DISTANCE_THRESHOLD, 10.0)): vol.Coerce(float),

            vol.Optional(CONF_ENTITY_FUEL_LEVEL, default=opt(CONF_ENTITY_FUEL_LEVEL, "")): str,
            vol.Optional(CONF_ENTITY_RANGE, default=opt(CONF_ENTITY_RANGE, "")): str,
            vol.Optional(CONF_ENTITY_CONSUMPTION, default=opt(CONF_ENTITY_CONSUMPTION, "")): str,
            vol.Optional(CONF_ENTITY_ODOMETER, default=opt(CONF_ENTITY_ODOMETER, "")): str,
            vol.Optional(CONF_ENTITY_LOCATION, default=opt(CONF_ENTITY_LOCATION, "")): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
