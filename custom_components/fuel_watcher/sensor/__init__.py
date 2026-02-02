from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .main import FuelWatcherSensor
from .diagnostics import FuelWatcherDiagnosticsSensor
from .location import FuelWatcherLocationSensor
from .derived import (
    FuelWatcherPriceSensor,
    FuelWatcherStationNameSensor,
    FuelWatcherDistanceSensor,
    FuelWatcherRangeSensor,
    FuelWatcherFuelLevelSensor,
    FuelWatcherConsumptionSensor,
    FuelWatcherOdometerSensor,
    FuelWatcherStrategyDecisionSensor,
    FuelWatcherStrategyReasonSensor,
    FuelWatcherHealthScoreSensor,
    FuelWatcherLastErrorSensor,
    FuelWatcherExpectedConsumptionTomorrowSensor,
    FuelWatcherDaysLeftSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    main_sensor = FuelWatcherSensor(hass, entry)
    diag_sensor = FuelWatcherDiagnosticsSensor(hass, entry, main_sensor)
    location_sensor = FuelWatcherLocationSensor(hass, entry)

    derived_sensors = [
        FuelWatcherPriceSensor(main_sensor),
        FuelWatcherStationNameSensor(main_sensor),
        FuelWatcherDistanceSensor(main_sensor),
        FuelWatcherRangeSensor(main_sensor),
        FuelWatcherFuelLevelSensor(main_sensor),
        FuelWatcherConsumptionSensor(main_sensor),
        FuelWatcherOdometerSensor(main_sensor),
        FuelWatcherStrategyDecisionSensor(main_sensor),
        FuelWatcherStrategyReasonSensor(main_sensor),
        FuelWatcherHealthScoreSensor(main_sensor),
        FuelWatcherLastErrorSensor(main_sensor),
        FuelWatcherExpectedConsumptionTomorrowSensor(main_sensor),
        FuelWatcherDaysLeftSensor(main_sensor),
    ]

    async_add_entities([main_sensor, diag_sensor, location_sensor] + derived_sensors)
