"""
Commit: feat(sensor): add best price sensor using Tankerkoenig result and storage

Fuel Watcher – Best Price Sensor
--------------------------------
Zeigt:
- beste gefundene Tankstelle
- aktuellen Preis
- Distanz
- Koordinaten
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import get_last_api
from ..const import DOMAIN


class FuelWatcherBestPriceSensor(SensorEntity):
    """Sensor für den besten Preis."""

    _attr_icon = "mdi:gas-station"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_best_price"
        self._attr_name = f"Fuel Watcher {entry.title} Best Price"
        self._attr_native_unit_of_measurement = "€/L"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Update sensor state from last API data."""
        data = await get_last_api(self.hass, self.entry)
        if not data:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        stations = data.get("stations") or []
        if not stations:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        station = stations[0]
        price = station.get("price")

        self._attr_native_value = price
        self._attr_extra_state_attributes = {
            "station_name": station.get("name"),
            "brand": station.get("brand"),
            "street": station.get("street"),
            "house_number": station.get("houseNumber"),
            "post_code": station.get("postCode"),
            "place": station.get("place"),
            "lat": station.get("lat"),
            "lng": station.get("lng"),
            "is_open": station.get("isOpen"),
            "dist": station.get("dist"),
        }

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"Fuel Watcher {self.entry.title}",
            "manufacturer": "Fuel Watcher",
        }
