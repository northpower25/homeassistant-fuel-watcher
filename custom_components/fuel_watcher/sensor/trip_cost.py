"""
Trip Cost Sensor

Phase 2: Displays cost statistics and comparisons.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, CONF_VEHICLE_NAME
from ..trip_cost_calculator import TripCostCalculator

_LOGGER = logging.getLogger(__name__)


class TripCostSensor(SensorEntity):
    """Sensor that displays trip cost statistics."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the trip cost sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{entry.data.get(CONF_VEHICLE_NAME, 'Vehicle')} Trip Costs"
        self._attr_unique_id = f"{entry.entry_id}_trip_costs"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "€"
        self._attr_state_class = SensorStateClass.TOTAL
        self._state = 0.0
        self._cost_stats = {}
        self.cost_calculator = TripCostCalculator(hass, entry)
    
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
    def native_value(self) -> float:
        """Return the state of the sensor (total real costs)."""
        return self._state
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            **self._cost_stats,
            "integration": "fuel_watcher",
        }
    
    async def async_update(self) -> None:
        """Update the sensor state."""
        # Calculate cost statistics
        self._cost_stats = await self.cost_calculator.calculate_trip_statistics_with_costs()
        
        # Set state to total combined cost (fuel + additional)
        self._state = self._cost_stats.get("total_combined_cost", 0.0)
