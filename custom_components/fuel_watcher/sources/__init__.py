from .const import DOMAIN

async def async_setup_entry(hass, entry):
    """Set up Fuel Watcher from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
