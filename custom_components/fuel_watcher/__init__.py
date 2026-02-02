from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .notify import send_test_notification

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    async def handle_test_service(call: ServiceCall):
        config_entry_id = call.data.get("config_entry_id", entry.entry_id)
        cfg_entry = hass.data[DOMAIN].get(config_entry_id)
        if cfg_entry:
            await send_test_notification(hass, cfg_entry)

    hass.services.async_register(DOMAIN, "send_test_notification", handle_test_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
