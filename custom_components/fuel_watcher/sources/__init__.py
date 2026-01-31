from .tankerkoenig import get_cheapest_tankerkoenig
from ..const import SOURCE_TANKERKOENIG

def get_cheapest(source, api_key, plz, radius, fuel):
    if source == SOURCE_TANKERKOENIG:
        return get_cheapest_tankerkoenig(api_key, plz, radius, fuel)
    # Platz für weitere Quellen:
    # elif source == "fuelprice_io": ...
    return None
