from .tankerkoenig import get_cheapest_tankerkoenig
from ..const import SOURCE_TANKERKOENIG

async def get_cheapest(hass, source, api_key, lat, lon, radius, fuel):
    if source == SOURCE_TANKERKOENIG:
        return await get_cheapest_tankerkoenig(hass, api_key, lat, lon, radius, fuel)

    return None
