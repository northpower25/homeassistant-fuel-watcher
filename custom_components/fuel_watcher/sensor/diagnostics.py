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
        # Platzhalter: hier kannst du letzte API-Response, Fehler, Telegram-Status etc. eintragen
        self._attrs["last_error"] = None
        self._attrs["last_update"] = self.entry.last_update_success
