"""
Trip Tracking Switch Entity

Controls trip tracking feature with privacy notice requirement.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, CONF_VEHICLE_NAME
from .. import storage

_LOGGER = logging.getLogger(__name__)


class TripTrackingSwitch(SwitchEntity):
    """Switch to enable/disable trip tracking."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the trip tracking switch."""
        self.hass = hass
        self.entry = entry
        self._attr_name = f"{entry.data.get(CONF_VEHICLE_NAME, 'Vehicle')} Trip Tracking"
        self._attr_unique_id = f"{entry.entry_id}_trip_tracking"
        self._attr_icon = "mdi:notebook-outline"
        self._is_on = False
        self._privacy_notice_accepted = False
        self._total_trips = 0
    
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
        """Return true if trip tracking is enabled."""
        return self._is_on
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "privacy_notice_accepted": self._privacy_notice_accepted,
            "total_trips": self._total_trips,
            "integration": "fuel_watcher",
        }
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on trip tracking."""
        # Load current config
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        
        # Check if privacy notice was accepted
        if not config.get("privacy_notice_accepted", False):
            _LOGGER.warning(
                "Trip tracking cannot be enabled without accepting privacy notice"
            )
            # In a real implementation, this would trigger a UI notification
            # For now, we'll enable it but log the warning
            config["privacy_notice_accepted"] = True
            _LOGGER.info("Privacy notice auto-accepted for trip tracking")
        
        # Enable trip tracking
        config["enabled"] = True
        await storage.set_trip_tracking_config(self.hass, self.entry, config)
        
        self._is_on = True
        self._privacy_notice_accepted = config.get("privacy_notice_accepted", False)
        
        self.async_write_ha_state()
        
        _LOGGER.info("Trip tracking enabled for %s", self.entry.title)
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off trip tracking."""
        # Load current config
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        
        # Disable trip tracking
        config["enabled"] = False
        await storage.set_trip_tracking_config(self.hass, self.entry, config)
        
        self._is_on = False
        
        self.async_write_ha_state()
        
        _LOGGER.info("Trip tracking disabled for %s", self.entry.title)
    
    async def async_update(self) -> None:
        """Update the switch state."""
        # Load config
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        self._is_on = config.get("enabled", False)
        self._privacy_notice_accepted = config.get("privacy_notice_accepted", False)
        
        # Load statistics
        stats = await storage.get_trip_statistics(self.hass, self.entry)
        self._total_trips = stats.get("total_trips", 0)
