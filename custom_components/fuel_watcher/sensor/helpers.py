import logging
from homeassistant.core import HomeAssistant
from ..const import (
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_LOCATION,
)

_LOGGER = logging.getLogger(__name__)


def validate_entities(hass: HomeAssistant, entry):
    """Check if all configured entities exist in Home Assistant."""
    missing = []

    def check(key):
        entity_id = entry.options.get(key) or entry.data.get(key)
        if entity_id and hass.states.get(entity_id) is None:
            missing.append(entity_id)

    check(CONF_ENTITY_FUEL_LEVEL)
    check(CONF_ENTITY_RANGE)
    check(CONF_ENTITY_CONSUMPTION)
    check(CONF_ENTITY_ODOMETER)
    check(CONF_ENTITY_LOCATION)

    return missing
