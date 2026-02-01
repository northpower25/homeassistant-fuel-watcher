DOMAIN = "fuel_watcher"

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

CONF_DYNAMIC_PLZ = "dynamic_plz"   # bleibt für Debug/Anzeige

SOURCE_TANKERKOENIG = "tankerkoenig"

SUPPORTED_SOURCES = [
    SOURCE_TANKERKOENIG,
]

HISTORY_FILE = "fuel_history.json"
