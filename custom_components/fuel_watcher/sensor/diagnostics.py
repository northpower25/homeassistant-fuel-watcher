from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN


class FuelWatcherDiagnosticsSensor(SensorEntity):
    """Diagnostics sensor for Fuel Watcher."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher Diagnostics"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_diagnostics"
        self._state = "ok"
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
        data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})

        last_api = data.get("last_api")
        last_telegram = data.get("last_telegram")
        last_error = data.get("last_error")

        self._attrs = {
            "last_api": last_api,
            "last_telegram": last_telegram,
            "last_error": last_error,
        }

        self._state = "error" if last_error else "ok"
