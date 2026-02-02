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
from .location import (
    FuelWatcherLocationSensor,
    FuelWatcherDistanceSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all Fuel Watcher sensors."""

    entities = [
        # A: Hauptsensor
        FuelWatcherMainSensor(hass, entry),

        # B + F: Strategie / abgeleitete Sensoren
        FuelWatcherDecisionSensor(hass, entry),
        FuelWatcherRangeKmSensor(hass, entry),
        FuelWatcherDaysLeftSensor(hass, entry),
        FuelWatcherPriceDeltaSensor(hass, entry),
        FuelWatcherPriceSpikeSensor(hass, entry),

        # C: Diagnostics
        FuelWatcherDiagnosticsSensor(hass, entry),

        # D: Location
        FuelWatcherLocationSensor(hass, entry),
        FuelWatcherDistanceSensor(hass, entry),
    ]

    async_add_entities(entities)
