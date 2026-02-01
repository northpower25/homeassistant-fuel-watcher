from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Sensor-Instanz speichern, damit der Test-Service darauf zugreifen kann
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Wird später vom Sensor gesetzt
    hass.data[DOMAIN]["sensor"] = None

    async def handle_test(call: ServiceCall):
        sensor = hass.data[DOMAIN].get("sensor")
        if sensor:
            await sensor.run_test()

    hass.services.async_register(DOMAIN, "test", handle_test)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
