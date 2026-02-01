from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import SOURCE_TANKERKOENIG
from .tankerkoenig import get_price_data as get_tankerkoenig_price


async def get_price_data(hass: HomeAssistant, entry: ConfigEntry):
    """
    Unified price fetcher for all supported sources.
    Routes to the correct backend based on config entry.
    """

    source = entry.data.get("source")

    if source == SOURCE_TANKERKOENIG:
        return await get_tankerkoenig_price(hass, entry)

    # Future sources:
    # if source == SOURCE_EU_API:
    #     return await get_eu_api_price(hass, entry)

    return None
