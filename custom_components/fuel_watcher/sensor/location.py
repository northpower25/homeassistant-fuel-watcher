"""
Commit: feat(sensor): add location and distance sensors for best station with navigation context

Fuel Watcher – Location Sensors
-------------------------------
Diese Datei implementiert die Standort-bezogenen Sensoren aus v0.0.27 – jetzt
basierend auf der neuen Storage- und Tankerkoenig-Architektur.

Sensoren:
- sensor.fuel_watcher_station_location
    → Adresse, Koordinaten, Navigation-Links
- sensor.fuel_watcher_distance_km
    → Entfernung zur besten Tankstelle in km

Beide Sensoren lesen die Daten aus:
- storage.best_station (gesetzt durch sources/tankerkoenig.py)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.location import distance as ha_distance

from ..storage import load_data
from ..telegram import build_navigation_links


class FuelWatcherLocationSensor(SensorEntity):
    """Sensor for best station location and navigation links."""

    _attr_icon = "mdi:map-marker"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._attr_name = "Fuel Watcher Station Location"
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_station_location"

        self._state: Optional[str] = None
        self._attrs: Dict[str, Any] = {}

    @property
    def native_value(self) -> Optional[str]:
        """Return a human-readable location string."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extended attributes."""
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
        """Update location and navigation attributes."""
        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        if not station:
            self._state = None
            self._attrs = {}
            return

        street = station.get("street") or ""
        house_number = station.get("house_number") or ""
        city = station.get("city") or ""
        post_code = station.get("post_code") or ""

        address = f"{street} {house_number}, {post_code} {city}".strip()
        self._state = address

        links = build_navigation_links(
            {
                "lat": station.get("lat"),
                "lon": station.get("lon"),
            }
        )

        self._attrs = {
            "name": station.get("name"),
            "brand": station.get("brand"),
            "street": street,
            "house_number": house_number,
            "post_code": post_code,
            "city": city,
            "lat": station.get("lat"),
            "lon": station.get("lon"),
            "price": station.get("price"),
            "distance_km": station.get("distance_km"),
            "navigation_google": links.get("google"),
            "navigation_apple": links.get("apple"),
            "navigation_waze": links.get("waze"),
        }


class FuelWatcherDistanceSensor(SensorEntity):
    """Sensor for distance to best station in km."""

    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "km"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._attr_name = "Fuel Watcher Distance (km)"
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_distance_km"

        self._state: Optional[float] = None
        self._attrs: Dict[str, Any] = {}

    @property
    def native_value(self) -> Optional[float]:
        """Return distance in km."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extended attributes."""
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
        """Compute distance between HA home location and best station."""
        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        if not station:
            self._state = None
            self._attrs = {}
            return

        lat = station.get("lat")
        lon = station.get("lon")

        if lat is None or lon is None:
            self._state = None
            self._attrs = {"reason": "missing_coordinates"}
            return

        # Home Assistant home location
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude

        if home_lat is None or home_lon is None:
            self._state = None
            self._attrs = {"reason": "missing_home_coordinates"}
            return

        # Distance in meters
        dist_m = ha_distance(home_lat, home_lon, lat, lon)
        if dist_m is None:
            self._state = None
            self._attrs = {"reason": "distance_calculation_failed"}
            return

        dist_km = round(dist_m / 1000.0, 2)
        self._state = dist_km
        self._attrs = {
            "station_lat": lat,
            "station_lon": lon,
            "home_lat": home_lat,
            "home_lon": home_lon,
        }
