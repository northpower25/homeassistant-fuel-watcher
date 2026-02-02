from __future__ import annotations

DOMAIN = "fuel_watcher"

# Sources
SOURCE_TANKERKOENIG = "tankerkoenig"
SUPPORTED_SOURCES = [SOURCE_TANKERKOENIG]

# Config keys
CONF_TANKERKOENIG_API = "tankerkoenig_api"
CONF_TELEGRAM_TOKEN = "telegram_token"
CONF_TELEGRAM_CHAT_ID = "telegram_chat_id"

CONF_RADIUS = "radius"
CONF_FUEL = "fuel"
CONF_SOURCE = "source"

CONF_PRICE_THRESHOLD = "price_threshold"
CONF_DISTANCE_THRESHOLD = "distance_threshold"

CONF_ENTITY_FUEL_LEVEL = "entity_fuel_level"
CONF_ENTITY_RANGE = "entity_range"
CONF_ENTITY_CONSUMPTION = "entity_consumption"
CONF_ENTITY_ODOMETER = "entity_odometer"
CONF_ENTITY_LOCATION = "entity_location"

# Weekday consumption
CONF_CONSUMPTION_MONDAY = "consumption_monday_km"
CONF_CONSUMPTION_TUESDAY = "consumption_tuesday_km"
CONF_CONSUMPTION_WEDNESDAY = "consumption_wednesday_km"
CONF_CONSUMPTION_THURSDAY = "consumption_thursday_km"
CONF_CONSUMPTION_FRIDAY = "consumption_friday_km"
CONF_CONSUMPTION_SATURDAY = "consumption_saturday_km"
CONF_CONSUMPTION_SUNDAY = "consumption_sunday_km"

WEEKDAY_OPTIONS = [
    CONF_CONSUMPTION_MONDAY,
    CONF_CONSUMPTION_TUESDAY,
    CONF_CONSUMPTION_WEDNESDAY,
    CONF_CONSUMPTION_THURSDAY,
    CONF_CONSUMPTION_FRIDAY,
    CONF_CONSUMPTION_SATURDAY,
    CONF_CONSUMPTION_SUNDAY,
]

# Notify options
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_NOTIFY_ON_DECISION_TANKEN = "notify_on_decision_tanken"
CONF_NOTIFY_ON_PRICE_THRESHOLD = "notify_on_price_threshold"
CONF_NOTIFY_ON_PRICE_DELTA = "notify_on_price_delta"
CONF_NOTIFY_ON_PRICE_SPIKE = "notify_on_price_spike"
CONF_NOTIFY_ON_RANGE_KM = "notify_on_range_km"
CONF_NOTIFY_ON_RANGE_DAYS = "notify_on_range_days"
CONF_NOTIFY_ON_STATION_CHANGE = "notify_on_station_change"
CONF_NOTIFY_ON_API_ERROR = "notify_on_api_error"

CONF_NOTIFY_RANGE_KM_THRESHOLD = "notify_range_km_threshold"
CONF_NOTIFY_RANGE_DAYS_THRESHOLD = "notify_range_days_threshold"
CONF_NOTIFY_PRICE_SPIKE_PERCENT = "notify_price_spike_percent"

CONF_PRICE_MODE = "price_mode"  # fixed | percent | absolute
CONF_PRICE_DELTA_PERCENT = "price_delta_percent"
CONF_PRICE_DELTA_ABSOLUTE = "price_delta_absolute"

CONF_NOTIFY_MSG_TANKEN = "notify_msg_tanken"
CONF_NOTIFY_MSG_PRICE = "notify_msg_price"
CONF_NOTIFY_MSG_PRICE_DELTA = "notify_msg_price_delta"
CONF_NOTIFY_MSG_PRICE_SPIKE = "notify_msg_price_spike"
CONF_NOTIFY_MSG_RANGE_KM = "notify_msg_range_km"
CONF_NOTIFY_MSG_RANGE_DAYS = "notify_msg_range_days"
CONF_NOTIFY_MSG_STATION_CHANGE = "notify_msg_station_change"
CONF_NOTIFY_MSG_API_ERROR = "notify_msg_api_error"

# Tank history (manuelle Erfassung)
CONF_TANK_EVENT_PRICE = "tank_event_price"
CONF_TANK_EVENT_LITERS = "tank_event_liters"
CONF_TANK_EVENT_TOTAL = "tank_event_total"
CONF_TANK_EVENT_ODOMETER = "tank_event_odometer"

# Default messages (humorvoll, Markdown + Emojis)
DEFAULT_NOTIFY_MSG_TANKEN = (
    "⛽ *Dein Auto flüstert: „Bitte tank mich…“*\n"
    "Grund: _{reason}_\n"
    "Preis: `{price} €/l`\n"
    "Reichweite: `{range_km} km`\n"
    "📍 [Navigation](https://www.google.com/maps/search/?api=1&query={lat},{lng})"
)

DEFAULT_NOTIFY_MSG_PRICE = (
    "💰 *Schnäppchen‑Alarm!*\n"
    "Der Preis ist jetzt bei `{price} €/l` — gönn dir!"
)

DEFAULT_NOTIFY_MSG_PRICE_DELTA = (
    "📉 *Preisbewegung entdeckt!*\n"
    "Der Preis hat sich um `{delta} €/l` ({delta_percent} %) verändert.\n"
    "Aktueller Preis: `{price} €/l`"
)

DEFAULT_NOTIFY_MSG_RANGE_KM = (
    "⚠️ *Oh oh…*\n"
    "Dein Auto hat Durst: nur noch `{range_km} km` Restreichweite."
)

DEFAULT_NOTIFY_MSG_RANGE_DAYS = (
    "📅 *Wie lange hält der Saft?*\n"
    "Noch `{days_left}` Tage — dann wird’s eng."
)

DEFAULT_NOTIFY_MSG_PRICE_SPIKE = (
    "📈 *Autsch! Preisexplosion…*\n"
    "Der Preis ist um `{spike_percent}%` gestiegen (jetzt `{price} €/l`)."
)

DEFAULT_NOTIFY_MSG_STATION_CHANGE = (
    "⛽ *Neue Tankstelle im Spiel!*\n"
    "Jetzt: _{station}_ (`{price} €/l`, Entfernung `{distance_km} km`).\n"
    "📍 [Navigation](https://www.google.com/maps/search/?api=1&query={lat},{lng})"
)

DEFAULT_NOTIFY_MSG_API_ERROR = (
    "❌ *Fuel Watcher hat ein Problem…*\n"
    "Die Tankdaten konnten nicht aktualisiert werden: _{error}_"
)
