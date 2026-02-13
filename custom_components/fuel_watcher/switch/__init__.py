"""Switch platform for Fuel Watcher integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .trip_tracking_switch import TripTrackingSwitch

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fuel Watcher switches."""
    
    # Add trip tracking switch
    switch = TripTrackingSwitch(hass, entry)
    async_add_entities([switch], True)
    
    _LOGGER.info("Fuel Watcher switches set up for %s", entry.title)
