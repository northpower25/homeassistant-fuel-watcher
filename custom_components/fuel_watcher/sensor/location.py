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
        station = data.get("best_station")

        if not station:
            self._state = None
            self._attrs = {}
            return

        self._state = station.get("name")
        lat = station.get("lat")
        lon = station.get("lon")

        self._attrs = {
            "brand": station.get("brand"),
            "street": station.get("street"),
            "house_number": station.get("house_number"),
            "post_code": station.get("post_code"),
            "city": station.get("city"),
            "lat": lat,
            "lon": lon,
            "price": station.get("price"),
            "distance_km": station.get("distance_km"),
        }

        if lat and lon:
            self._attrs["google_maps"] = f"https://maps.google.com/?q={lat},{lon}"
            self._attrs["apple_maps"] = f"http://maps.apple.com/?ll={lat},{lon}"
            self._attrs["waze"] = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"


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
        data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        station = data.get("best_station")

        if not station:
            self._state = None
            return

        try:
            self._state = round(float(station.get("distance_km")), 2)
        except:
            self._state = None
