from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .main import FuelWatcherSensor
from .diagnostics import FuelWatcherDiagnosticsSensor
from .location import FuelWatcherLocationSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Fuel Watcher sensors."""
    main_sensor = FuelWatcherSensor(hass, entry)
    diag_sensor = FuelWatcherDiagnosticsSensor(hass, entry, main_sensor)
    location_sensor = FuelWatcherLocationSensor(hass, entry)

    async_add_entities([
        main_sensor,
        diag_sensor,
        location_sensor,
    ])
