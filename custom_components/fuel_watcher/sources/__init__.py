from .tankerkoenig import get_cheapest_tankerkoenig
from ..const import SOURCE_TANKERKOENIG


async def get_cheapest(hass, source, api_key, plz, radius, fuel):
    if source == SOURCE_TANKERKOENIG:
        return await get_cheapest_tankerkoenig(hass, api_key, plz, radius, fuel)

    return None
