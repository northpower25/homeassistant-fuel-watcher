from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .main import FuelWatcherMainSensor
from .strategy import (
    FuelWatcherDecisionSensor,
    FuelWatcherRangeKmSensor,
    FuelWatcherDaysLeftSensor,
    FuelWatcherPriceDeltaSensor,
    FuelWatcherPriceSpikeSensor,
)
from .diagnostics import FuelWatcherDiagnosticsSensor
from .location import FuelWatcherLocationSensor, FuelWatcherDistanceSensor
from .tank_history_sensor import FuelWatcherTankHistorySensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all Fuel Watcher sensors."""

    entities = [
        # Hauptsensor
        FuelWatcherMainSensor(hass, entry),

        # Strategie-Sensoren
        FuelWatcherDecisionSensor(hass, entry),
        FuelWatcherRangeKmSensor(hass, entry),
        FuelWatcherDaysLeftSensor(hass, entry),
        FuelWatcherPriceDeltaSensor(hass, entry),
        FuelWatcherPriceSpikeSensor(hass, entry),

        # Diagnose
        FuelWatcherDiagnosticsSensor(hass, entry),

        # Location
        FuelWatcherLocationSensor(hass, entry),
        FuelWatcherDistanceSensor(hass, entry),

        # Tankhistorie
        FuelWatcherTankHistorySensor(hass, entry),
    ]

    async_add_entities(entities)
