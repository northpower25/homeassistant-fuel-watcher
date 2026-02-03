"""
Commit: refactor(const): remove deprecated config keys and align constants with new storage-based architecture

Fuel Watcher – Constants
------------------------
Bereinigte und modernisierte Konstanten für die neue Storage-Architektur.
"""

from __future__ import annotations

DOMAIN = "fuel_watcher"

# Supported sources
SOURCE_TANKERKOENIG = "tankerkoenig"
SUPPORTED_SOURCES = [SOURCE_TANKERKOENIG]

# Config keys (active)
CONF_TANKERKOENIG_API = "tankerkoenig_api"
CONF_TELEGRAM_TOKEN = "telegram_token"
CONF_TELEGRAM_CHAT_ID = "telegram_chat_id"

CONF_RADIUS = "radius"
CONF_FUEL = "fuel"
CONF_SOURCE = "source"

# Range entity (only remaining vehicle-related config)
CONF_ENTITY_RANGE = "entity_range"

# Platforms
PLATFORMS = ["sensor"]
