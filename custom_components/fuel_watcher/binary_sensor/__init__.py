"""Binary sensor platform for Fuel Watcher integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .on_trip import OnTripBinarySensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fuel Watcher binary sensors."""
    
    # Add on trip binary sensor
    binary_sensor = OnTripBinarySensor(hass, entry)
    async_add_entities([binary_sensor], True)
    
    _LOGGER.info("Fuel Watcher binary sensors set up for %s", entry.title)
