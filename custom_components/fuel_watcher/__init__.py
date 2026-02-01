from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import async_load_platform

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Fuel Watcher from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Sensor-Plattform laden
    await async_load_platform(hass, "sensor", DOMAIN, {}, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Fuel Watcher."""
    return True
