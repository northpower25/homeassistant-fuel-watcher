"""
Commit: feat(sensor): add diagnostics sensor for API, telegram and error tracking

Fuel Watcher – Diagnostics Sensor
---------------------------------
Dieser Sensor zeigt:
- letzte API-Antwort
- letzte Telegram-Nachricht
- letzten Fehler
- Timestamp der letzten Ereignisse

Er dient zur Fehlersuche und Transparenz.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import load_data


class FuelWatcherDiagnosticsSensor(SensorEntity):
    """Diagnostics sensor for Fuel Watcher."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._attr_name = "Fuel Watcher Diagnostics"
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_diagnostics"

        self._state: Optional[str] = None
        self._attrs: Dict[str, Any] = {}

    @property
    def native_value(self) -> Optional[str]:
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
        data = await load_data(self.hass, self.entry)

        last_api = data.get("last_api")
        last_telegram = data.get("last_telegram")
        last_error = data.get("last_error")

        self._state = "OK" if last_error is None else "ERROR"

        self._attrs = {
            "last_api": last_api,
            "last_telegram": last_telegram,
            "last_error": last_error,
        }
