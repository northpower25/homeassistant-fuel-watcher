"""
Commit: fix(sensor): restore valid sensor platform setup and add vehicle data sensor hook

Fuel Watcher – Sensor Platform
------------------------------
Registriert alle Sensoren der Integration:
- BestPriceSensor
- StrategySensor
- RangeDaysSensor
- VehicleDataSensor (optional, wenn Fahrzeug-Entitäten konfiguriert sind)
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    CONF_ENTITY_RANGE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_CONSUMPTION,
)
from .best_price import FuelWatcherBestPriceSensor
from .strategy import FuelWatcherStrategySensor
from .range_days import FuelWatcherRangeDaysSensor
from .vehicle_data import FuelWatcherVehicleDataSensor
from .debug import FuelWatcherDebugSensor
from .trip_log import TripLogSensor, CurrentTripSensor

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Fuel Watcher sensors."""
    sensors = []

    # Basis-Sensoren
    sensors.append(FuelWatcherBestPriceSensor(hass, entry))
    sensors.append(FuelWatcherStrategySensor(hass, entry))
    sensors.append(FuelWatcherRangeDaysSensor(hass, entry))
    sensors.append(FuelWatcherDebugSensor(hass, entry))

    # Fahrzeugdaten-Sensor nur, wenn mindestens eine Fahrzeug-Entität gesetzt ist
    vehicle_entities = [
        entry.options.get(CONF_ENTITY_RANGE) or entry.data.get(CONF_ENTITY_RANGE),
        entry.options.get(CONF_ENTITY_ODOMETER) or entry.data.get(CONF_ENTITY_ODOMETER),
        entry.options.get(CONF_ENTITY_FUEL_LEVEL) or entry.data.get(CONF_ENTITY_FUEL_LEVEL),
        entry.options.get(CONF_ENTITY_LOCATION) or entry.data.get(CONF_ENTITY_LOCATION),
        entry.options.get(CONF_ENTITY_CONSUMPTION) or entry.data.get(CONF_ENTITY_CONSUMPTION),
    ]

    if any(vehicle_entities):
        sensors.append(FuelWatcherVehicleDataSensor(hass, entry))
    
    # Trip tracking sensors
    sensors.append(TripLogSensor(hass, entry))
    sensors.append(CurrentTripSensor(hass, entry))

    async_add_entities(sensors)
