"""
Commit: feat(const): add vehicle_name and vehicle entity keys
(odometer, fuel level, location, consumption), Trasholds for decition, Notify messages
"""

DOMAIN = "fuel_watcher"

# Config keys
CONF_TANKERKOENIG_API = "tankerkoenig_api"
CONF_TELEGRAM_TOKEN = "telegram_token"
CONF_TELEGRAM_CHAT_ID = "telegram_chat_id"

CONF_RADIUS = "radius"
CONF_FUEL_TYPE = "fuel_type"

# Vehicle identity
CONF_VEHICLE_NAME = "vehicle_name"

# Vehicle entity references
CONF_ENTITY_RANGE = "entity_range"
CONF_ENTITY_ODOMETER = "entity_odometer"
CONF_ENTITY_FUEL_LEVEL = "entity_fuel_level"
CONF_ENTITY_LOCATION = "entity_location"
CONF_ENTITY_CONSUMPTION = "entity_consumption"

# Trasholds for decition
CONF_PRICE_DROP_PERCENT_THRESHOLD = "price_drop_percent_threshold"
CONF_PRICE_DROP_ABSOLUTE_THRESHOLD = "price_drop_absolute_threshold"

# Notify messages
CONF_NOTIFY_MSG_TANKEN = "notify_msg_tanken"
CONF_NOTIFY_MSG_RANGE_DAYS = "notify_msg_range_days"

DEFAULT_NOTIFY_MSG_TANKEN = (
    "⛽ *Tankempfehlung für {vehicle}*\n"
    "Grund: _{reason}_\n"
    "Preis: `{price} €/l`\n"
    "Δ: `{delta} €/l` ({delta_percent} %)\n"
    "Reichweite: `{range_km} km`\n"
    "📍 {station} ({distance_km} km)\n"
    "[Navigation](https://www.google.com/maps/search/?api=1&query={lat},{lng})"
)

DEFAULT_NOTIFY_MSG_RANGE_DAYS = (
    "⚠️ *Reichweitenwarnung für {vehicle}*\n"
    "Noch `{days_left}` Tage verbleibend.\n"
    "Aktuelle Reichweite: `{range_km} km`"
)

PLATFORMS = ["sensor"]
