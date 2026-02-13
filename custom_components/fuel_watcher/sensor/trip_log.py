"""
Trip Log Sensor

Shows trip history and statistics.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, CONF_VEHICLE_NAME
from .. import storage

_LOGGER = logging.getLogger(__name__)


class TripLogSensor(SensorEntity):
    """Sensor that displays trip log and statistics."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the trip log sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{entry.data.get(CONF_VEHICLE_NAME, 'Vehicle')} Trip Log"
        self._attr_unique_id = f"{entry.entry_id}_trip_log"
        self._attr_icon = "mdi:notebook-multiple"
        self._state = 0
        self._trips = []
        self._statistics = {}
    
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
    def native_value(self) -> int:
        """Return the state of the sensor (total trips)."""
        return self._state
    
    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "trips"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        # Return last 10 trips and statistics
        recent_trips = self._trips[-10:] if len(self._trips) > 10 else self._trips
        
        return {
            "recent_trips": recent_trips,
            "statistics": self._statistics,
            "total_trips": self._state,
            "integration": "fuel_watcher",
        }
    
    async def async_update(self) -> None:
        """Update the sensor state."""
        # Load trips
        self._trips = await storage.get_trips(self.hass, self.entry)
        self._state = len(self._trips)
        
        # Load statistics
        self._statistics = await storage.get_trip_statistics(self.hass, self.entry)


class CurrentTripSensor(SensorEntity):
    """Sensor that displays current ongoing trip."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the current trip sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{entry.data.get(CONF_VEHICLE_NAME, 'Vehicle')} Current Trip"
        self._attr_unique_id = f"{entry.entry_id}_current_trip"
        self._attr_icon = "mdi:car-clock"
        self._state = "idle"
        self._current_trip = None
    
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
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._state
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self._current_trip:
            return {"integration": "fuel_watcher"}
        
        return {
            "trip_id": self._current_trip.get("trip_id"),
            "started_at": self._current_trip.get("started_at"),
            "distance_km": self._current_trip.get("distance_km", 0),
            "odometer_start": self._current_trip.get("odometer_start"),
            "fuel_level_start": self._current_trip.get("fuel_level_start"),
            "integration": "fuel_watcher",
        }
    
    async def async_update(self) -> None:
        """Update the sensor state."""
        # Load current trip
        self._current_trip = await storage.get_current_trip(self.hass, self.entry)
        
        if self._current_trip:
            self._state = "in_progress"
            self._attr_icon = "mdi:car"
        else:
            self._state = "idle"
            self._attr_icon = "mdi:car-clock"
