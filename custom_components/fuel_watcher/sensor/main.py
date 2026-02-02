from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..tank_history import (
    append_tank_event,
    get_last_tank_event,
)
from ..const import DOMAIN


class FuelWatcherMainSensor(SensorEntity):
    """Main Fuel Watcher status sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_main"
        self._state = None
        self._attrs = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    async def async_update(self):
        """Update sensor state."""
        last_event = get_last_tank_event(self.hass, self.entry)

        self._attrs["last_tank_event"] = last_event

        if last_event:
            self._state = last_event.get("price_per_liter")
        else:
            self._state = None
