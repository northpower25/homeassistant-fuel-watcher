"""
On Trip Binary Sensor

Indicates whether vehicle is currently on a trip.
"""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, CONF_VEHICLE_NAME
from .. import storage

_LOGGER = logging.getLogger(__name__)


class OnTripBinarySensor(BinarySensorEntity):
    """Binary sensor that indicates if vehicle is on a trip."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the on trip binary sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{entry.data.get(CONF_VEHICLE_NAME, 'Vehicle')} On Trip"
        self._attr_unique_id = f"{entry.entry_id}_on_trip"
        self._attr_device_class = BinarySensorDeviceClass.MOVING
        self._attr_icon = "mdi:car"
        self._is_on = False
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.data.get(CONF_VEHICLE_NAME, "Fuel Watcher Vehicle"),
            manufacturer="Fuel Watcher",
            model="Trip Tracking",
        )
    
    @property
    def is_on(self) -> bool:
        """Return true if vehicle is on a trip."""
        return self._is_on
    
    async def async_update(self) -> None:
        """Update the binary sensor state."""
        # Load current trip
        current_trip = await storage.get_current_trip(self.hass, self.entry)
        
        self._is_on = current_trip is not None
