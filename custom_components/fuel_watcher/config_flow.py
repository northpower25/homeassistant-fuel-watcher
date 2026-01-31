import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

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

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Fuel Watcher", data=user_input)

        # --- Entity Registry sicher laden ---
        er = async_get_entity_registry(self.hass)
        entities = []

        if er is not None and hasattr(er, "entities"):
            try:
                entities = sorted(er.entities.keys())
            except Exception:
                entities = []

        # --- Dropdown + Freitext ---
        def entity_field():
            if entities:
                return vol.Any(vol.In(entities), str)
            return str

        # --- Formularschema ---
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

            # --- numerische Felder robust ---
            vol.Optional(CONF_PRICE_THRESHOLD, default=0.0): vol.Coerce(float),
            vol.Optional(CONF_DISTANCE_THRESHOLD, default=10.0): vol.Coerce(float),

            # --- Fahrzeugdaten ---
            vol.Optional(CONF_ENTITY_FUEL_LEVEL): entity_field(),
            vol.Optional(CONF_ENTITY_RANGE): entity_field(),
            vol.Optional(CONF_ENTITY_CONSUMPTION): entity_field(),
            vol.Optional(CONF_ENTITY_ODOMETER): entity_field(),
            vol.Optional(CONF_ENTITY_LOCATION): entity_field(),
        })

        return self.async_show_form(step_id="user", data_schema=schema)
