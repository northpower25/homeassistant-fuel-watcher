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
    CONF_CONSUMPTION_MONDAY,
    CONF_CONSUMPTION_TUESDAY,
    CONF_CONSUMPTION_WEDNESDAY,
    CONF_CONSUMPTION_THURSDAY,
    CONF_CONSUMPTION_FRIDAY,
    CONF_CONSUMPTION_SATURDAY,
    CONF_CONSUMPTION_SUNDAY,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_ON_DECISION_TANKEN,
    CONF_NOTIFY_ON_PRICE_THRESHOLD,
    CONF_NOTIFY_ON_PRICE_DELTA,
    CONF_NOTIFY_ON_PRICE_SPIKE,
    CONF_NOTIFY_ON_RANGE_KM,
    CONF_NOTIFY_ON_RANGE_DAYS,
    CONF_NOTIFY_RANGE_KM_THRESHOLD,
    CONF_NOTIFY_RANGE_DAYS_THRESHOLD,
    CONF_PRICE_MODE,
    CONF_PRICE_DELTA_PERCENT,
    CONF_PRICE_DELTA_ABSOLUTE,
    CONF_NOTIFY_MSG_TANKEN,
    CONF_NOTIFY_MSG_PRICE,
    CONF_NOTIFY_MSG_PRICE_DELTA,
    CONF_NOTIFY_MSG_PRICE_SPIKE,
    CONF_NOTIFY_MSG_RANGE_KM,
    CONF_NOTIFY_MSG_RANGE_DAYS,
    CONF_NOTIFY_MSG_STATION_CHANGE,
    CONF_NOTIFY_MSG_API_ERROR,
    DEFAULT_NOTIFY_MSG_TANKEN,
    DEFAULT_NOTIFY_MSG_PRICE_DELTA,
    DEFAULT_NOTIFY_MSG_RANGE_DAYS,
    CONF_TANK_HISTORY_RETENTION_MONTHS,
    DEFAULT_TANK_HISTORY_RETENTION_MONTHS,
)

from .notify import send_test_notification
from .tank_history import append_tank_event


class FuelWatcherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

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

            vol.Optional(CONF_CONSUMPTION_MONDAY, default=50): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_TUESDAY, default=50): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_WEDNESDAY, default=50): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_THURSDAY, default=50): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_FRIDAY, default=60): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_SATURDAY, default=20): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_SUNDAY, default=10): vol.Coerce(int),
        })

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
        """Main options menu."""
        if user_input is not None:

            # Testnachricht senden
            if user_input.get("test_notification", False):
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

        schema = vol.Schema({

            # Basis
            vol.Required(CONF_RADIUS, default=opt(CONF_RADIUS, 5)): vol.Coerce(int),
            vol.Required(CONF_FUEL, default=opt(CONF_FUEL, "e5")): vol.In(["e5", "e10", "diesel", "superplus", "lpg", "cng"]),
            vol.Required(CONF_PRICE_THRESHOLD, default=opt(CONF_PRICE_THRESHOLD, 0.0)): vol.Coerce(float),
            vol.Required(CONF_DISTANCE_THRESHOLD, default=opt(CONF_DISTANCE_THRESHOLD, 10.0)): vol.Coerce(float),

            # Fahrzeug-Entitäten
            vol.Optional(CONF_ENTITY_FUEL_LEVEL, default=opt(CONF_ENTITY_FUEL_LEVEL, "")): str,
            vol.Optional(CONF_ENTITY_RANGE, default=opt(CONF_ENTITY_RANGE, "")): str,
            vol.Optional(CONF_ENTITY_CONSUMPTION, default=opt(CONF_ENTITY_CONSUMPTION, "")): str,
            vol.Optional(CONF_ENTITY_ODOMETER, default=opt(CONF_ENTITY_ODOMETER, "")): str,
            vol.Optional(CONF_ENTITY_LOCATION, default=opt(CONF_ENTITY_LOCATION, "")): str,

            # Verbrauch
            vol.Optional(CONF_CONSUMPTION_MONDAY, default=opt(CONF_CONSUMPTION_MONDAY, 50)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_TUESDAY, default=opt(CONF_CONSUMPTION_TUESDAY, 50)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_WEDNESDAY, default=opt(CONF_CONSUMPTION_WEDNESDAY, 50)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_THURSDAY, default=opt(CONF_CONSUMPTION_THURSDAY, 50)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_FRIDAY, default=opt(CONF_CONSUMPTION_FRIDAY, 60)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_SATURDAY, default=opt(CONF_CONSUMPTION_SATURDAY, 20)): vol.Coerce(int),
            vol.Optional(CONF_CONSUMPTION_SUNDAY, default=opt(CONF_CONSUMPTION_SUNDAY, 10)): vol.Coerce(int),

            # Benachrichtigungen
            vol.Optional(CONF_NOTIFY_ENABLED, default=opt(CONF_NOTIFY_ENABLED, True)): bool,
            vol.Optional(CONF_NOTIFY_ON_DECISION_TANKEN, default=opt(CONF_NOTIFY_ON_DECISION_TANKEN, True)): bool,
            vol.Optional(CONF_NOTIFY_ON_PRICE_THRESHOLD, default=opt(CONF_NOTIFY_ON_PRICE_THRESHOLD, False)): bool,
            vol.Optional(CONF_NOTIFY_ON_PRICE_DELTA, default=opt(CONF_NOTIFY_ON_PRICE_DELTA, False)): bool,
            vol.Optional(CONF_NOTIFY_ON_RANGE_KM, default=opt(CONF_NOTIFY_ON_RANGE_KM, False)): bool,
            vol.Optional(CONF_NOTIFY_ON_RANGE_DAYS, default=opt(CONF_NOTIFY_ON_RANGE_DAYS, True)): bool,

            vol.Optional(CONF_NOTIFY_RANGE_KM_THRESHOLD, default=opt(CONF_NOTIFY_RANGE_KM_THRESHOLD, 100.0)): vol.Coerce(float),
            vol.Optional(CONF_NOTIFY_RANGE_DAYS_THRESHOLD, default=opt(CONF_NOTIFY_RANGE_DAYS_THRESHOLD, 2.0)): vol.Coerce(float),

            # Preis-Delta
            vol.Optional(CONF_PRICE_MODE, default=opt(CONF_PRICE_MODE, "fixed")): vol.In(["fixed", "percent", "absolute"]),
            vol.Optional(CONF_PRICE_DELTA_PERCENT, default=opt(CONF_PRICE_DELTA_PERCENT, 5.0)): vol.Coerce(float),
            vol.Optional(CONF_PRICE_DELTA_ABSOLUTE, default=opt(CONF_PRICE_DELTA_ABSOLUTE, 0.10)): vol.Coerce(float),

            # Nachrichtentexte
            vol.Optional(CONF_NOTIFY_MSG_TANKEN, default=opt(CONF_NOTIFY_MSG_TANKEN, DEFAULT_NOTIFY_MSG_TANKEN)): str,
            vol.Optional(CONF_NOTIFY_MSG_RANGE_DAYS, default=opt(CONF_NOTIFY_MSG_RANGE_DAYS, DEFAULT_NOTIFY_MSG_RANGE_DAYS)): str,
            vol.Optional(CONF_NOTIFY_MSG_PRICE_DELTA, default=opt(CONF_NOTIFY_MSG_PRICE_DELTA, DEFAULT_NOTIFY_MSG_PRICE_DELTA)): str,

            # Tankhistorie – Aufbewahrungszeitraum
            vol.Optional(
                CONF_TANK_HISTORY_RETENTION_MONTHS,
                default=opt(CONF_TANK_HISTORY_RETENTION_MONTHS, DEFAULT_TANK_HISTORY_RETENTION_MONTHS),
            ): vol.Coerce(int),

            # Testnachricht
            vol.Optional("test_notification", default=False): bool,

            # Tankvorgang erfassen
            vol.Optional("tank_event_price", default=""): str,
            vol.Optional("tank_event_liters", default=""): str,
            vol.Optional("tank_event_total", default=""): str,
            vol.Optional("tank_event_odometer", default=""): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
