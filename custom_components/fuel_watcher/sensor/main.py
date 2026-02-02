from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN
from ..tank_history import get_last_tank_event


class FuelWatcherMainSensor(SensorEntity):
    """Main Fuel Watcher sensor (aktueller Preis / Status)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_main"
        self._state = None
        self._attrs: dict = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    async def async_update(self) -> None:
        """Update main sensor state from last tank event (Fallback)."""
        last = get_last_tank_event(self.hass, self.entry)
        self._attrs["last_tank_event"] = last

        if last:
            self._state = last.get("price_per_liter")
            self._attrs["last_station"] = last.get("station_name")
            self._attrs["last_total_cost"] = last.get("total_cost")
        else:
            self._state = None
