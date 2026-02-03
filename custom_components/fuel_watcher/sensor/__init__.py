# Commit: fix: correct tank history sensor import path
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
        FuelWatcherMainSensor(hass, entry),

        FuelWatcherDecisionSensor(hass, entry),
        FuelWatcherRangeKmSensor(hass, entry),
        FuelWatcherDaysLeftSensor(hass, entry),
        FuelWatcherPriceDeltaSensor(hass, entry),
        FuelWatcherPriceSpikeSensor(hass, entry),

        FuelWatcherDiagnosticsSensor(hass, entry),

        FuelWatcherLocationSensor(hass, entry),
        FuelWatcherDistanceSensor(hass, entry),

        FuelWatcherTankHistorySensor(hass, entry),
    ]

    async_add_entities(entities)
