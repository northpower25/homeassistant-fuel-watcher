"""
Commit: feat(sensor): add tank history sensor with full storage integration

Fuel Watcher – Tank History Sensor
----------------------------------
Dieser Sensor zeigt die gesamte Tankhistorie an:
- letzte Tankvorgänge
- Liter, Preis, Gesamtkosten
- Odometer
- Quelle (manual/telegram)

Er dient als Übersicht und Debug-Hilfe.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..tank_history import get_tank_events


class FuelWatcherTankHistorySensor(SensorEntity):
    """Tank history sensor."""

    _attr_icon = "mdi:gas-station"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._attr_name = "Fuel Watcher Tank History"
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_tank_history"

        self._state: Optional[int] = None
        self._attrs: Dict[str, Any] = {}

    @property
    def native_value(self) -> Optional[int]:
        """Return number of tank events."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self._attrs

    @property
    def device_info(self):
        return {
            "identifiers": {("fuel_watcher", self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    async def async_update(self) -> None:
        events = await get_tank_events(self.hass, self.entry)

        self._state = len(events)
        self._attrs = {
            "events": events,
        }
