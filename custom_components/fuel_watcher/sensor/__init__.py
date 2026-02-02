from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .main import FuelWatcherMainSensor
from .diagnostics import FuelWatcherDiagnosticsSensor
from .location import FuelWatcherLocationSensor
from .tank_history import FuelWatcherTankHistorySensor

from ..const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up Fuel Watcher sensors."""

    main_sensor = FuelWatcherMainSensor(hass, entry)
    diag_sensor = FuelWatcherDiagnosticsSensor(hass, entry)
    location_sensor = FuelWatcherLocationSensor(hass, entry)
    tank_history_sensor = FuelWatcherTankHistorySensor(hass, entry)

    entities = [
        main_sensor,
        diag_sensor,
        location_sensor,
        tank_history_sensor,
    ]

    async_add_entities(entities)
