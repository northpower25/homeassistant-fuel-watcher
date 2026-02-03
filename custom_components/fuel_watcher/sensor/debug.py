"""
Commit: feat(sensor): add debug sensor exposing full storage state

Fuel Watcher – Debug Sensor
---------------------------
Zeigt den kompletten Storage-Inhalt für dieses Fahrzeug:

- last_price
- last_decision
- last_api (gekürzt)
- last_telegram
- last_error
- version
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import _load_data
from ..const import DOMAIN


class FuelWatcherDebugSensor(SensorEntity):
    """Debug sensor exposing full storage state."""

    _attr_icon = "mdi:database-eye"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_debug"
        self._attr_name = f"Fuel Watcher {entry.title} Debug"
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        """Load full storage content."""
        data = await _load_data(self.hass, self.entry)

        # API-Daten kürzen, damit der Sensor nicht explodiert
        api_preview = None
        if data.get("last_api"):
            api_preview = {
                "stations_count": len(data["last_api"].get("stations", [])),
                "ok": data["last_api"].get("ok"),
            }

        self._attr_native_value = "ok"
        self._attr_extra_state_attributes = {
            "version": data.get("version"),
            "last_price": data.get("last_price"),
            "last_decision": data.get("last_decision"),
            "last_telegram": data.get("last_telegram"),
            "last_error": data.get("last_error"),
            "api_preview": api_preview,
        }

    @property
    def should_poll(self):
        return True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"Fuel Watcher {self.entry.title}",
            "manufacturer": "Fuel Watcher",
        }
