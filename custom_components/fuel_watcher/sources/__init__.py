from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import SOURCE_TANKERKOENIG
from .tankerkoenig import get_price_data as get_tankerkoenig_price


async def get_price_data(hass: HomeAssistant, entry: ConfigEntry):
    source = entry.data.get("source")
    if source == SOURCE_TANKERKOENIG:
        return await get_tankerkoenig_price(hass, entry)
    return None
