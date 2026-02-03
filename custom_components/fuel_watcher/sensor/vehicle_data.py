"""
Commit: feat(sensor): add vehicle data sensor reading from configured entities

Fuel Watcher – Vehicle Data Sensor
----------------------------------
Liest Fahrzeugdaten direkt aus konfigurierten Entitäten:

- entity_range
- entity_odometer
- entity_fuel_level
- entity_location (lat/lon)
- entity_consumption

Keine eigenen Entitäten, nur Aggregation & Diagnose.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import (
    DOMAIN,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_CONSUMPTION,
)


class FuelWatcherVehicleDataSensor(SensorEntity):
    """Aggregierter Fahrzeugdaten-Sensor."""

    _attr_icon = "mdi:car-connected"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vehicle_data"
        self._attr_name = f"Fuel Watcher {entry.title} Vehicle Data"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Read all configured vehicle entities and expose as attributes."""
        opts = self.entry.options or self.entry.data

        range_entity = opts.get(CONF_ENTITY_RANGE)
        odo_entity = opts.get(CONF_ENTITY_ODOMETER)
        fuel_entity = opts.get(CONF_ENTITY_FUEL_LEVEL)
        loc_entity = opts.get(CONF_ENTITY_LOCATION)
        cons_entity = opts.get(CONF_ENTITY_CONSUMPTION)

        attrs = {}

        def safe_get(entity_id):
            if not entity_id:
                return None
            state_obj = self.hass.states.get(entity_id)
            if not state_obj:
                return None
            return state_obj.state, state_obj.attributes

        # Range
        if range_entity:
            val, _ = safe_get(range_entity) or (None, {})
            attrs["range_entity"] = range_entity
            attrs["range_value"] = val

        # Odometer
        if odo_entity:
            val, _ = safe_get(odo_entity) or (None, {})
            attrs["odometer_entity"] = odo_entity
            attrs["odometer_value"] = val

        # Fuel level
        if fuel_entity:
            val, _ = safe_get(fuel_entity) or (None, {})
            attrs["fuel_level_entity"] = fuel_entity
            attrs["fuel_level_value"] = val

        # Consumption
        if cons_entity:
            val, _ = safe_get(cons_entity) or (None, {})
            attrs["consumption_entity"] = cons_entity
            attrs["consumption_value"] = val

        # Location
        if loc_entity:
            state_obj = self.hass.states.get(loc_entity)
            lat = None
            lon = None
            if state_obj:
                # Try attributes first
                lat = state_obj.attributes.get("latitude")
                lon = state_obj.attributes.get("longitude")
                # Fallback: state as "lat,lon"
                if (lat is None or lon is None) and isinstance(state_obj.state, str) and "," in state_obj.state:
                    try:
                        lat_str, lon_str = state_obj.state.split(",", 1)
                        lat = float(lat_str)
                        lon = float(lon_str)
                    except Exception:
                        lat = None
                        lon = None

            attrs["location_entity"] = loc_entity
            attrs["location_lat"] = lat
            attrs["location_lon"] = lon

        self._attr_native_value = "ok" if attrs else None
        self._attr_extra_state_attributes = attrs

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
