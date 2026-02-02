from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN


class FuelWatcherLocationSensor(SensorEntity):
    """Empfohlene Tankstelle (Location)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher Tankstelle"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_station_location"
        self._state = None
        self._attrs: dict = {}

    @property
    def native_value(self):
        return self._state  # z.B. Name der Tankstelle

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
        # Platzhalter: hier später API-Daten eintragen
        self._state = None
        self._attrs["lat"] = None
        self._attrs["lon"] = None
        self._attrs["google_maps"] = None
        self._attrs["apple_maps"] = None
        self._attrs["waze"] = None


class FuelWatcherDistanceSensor(SensorEntity):
    """Entfernung zur empfohlenen Tankstelle."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher Entfernung"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_distance"
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return "km"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    async def async_update(self) -> None:
        # Platzhalter: hier später Entfernung berechnen
        self._state = None
