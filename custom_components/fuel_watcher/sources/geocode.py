import logging
import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


async def reverse_geocode_postcode(hass, lat, lon):
    """Reverse-geocode lat/lon to a German PLZ using Nominatim."""
    url = (
        "https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lon}&format=json&addressdetails=1"
    )

    session = async_get_clientsession(hass)

    try:
        async with async_timeout.timeout(10):
            async with session.get(url, headers={"User-Agent": "FuelWatcher/1.0"}) as resp:
                data = await resp.json()
    except Exception as e:
        _LOGGER.error(f"[FuelWatcher] Reverse-Geocoding Fehler: {e}")
        return None

    address = data.get("address", {})
    plz = address.get("postcode")

    if plz:
        _LOGGER.warning(f"[FuelWatcher] Reverse-Geocoding PLZ: {plz}")
        return plz

    _LOGGER.error("[FuelWatcher] Reverse-Geocoding: Keine PLZ gefunden")
    return None


async def get_dynamic_postcode(hass, entity_id):
    """Extract lat/lon from a device_tracker and return dynamic PLZ."""
    state = hass.states.get(entity_id)

    if not state:
        _LOGGER.error(f"[FuelWatcher] Standort-Entity nicht gefunden: {entity_id}")
        return None

    lat = state.attributes.get("latitude")
    lon = state.attributes.get("longitude")

    if lat is None or lon is None:
        _LOGGER.error(f"[FuelWatcher] Standort-Entity hat keine Koordinaten: {entity_id}")
        return None

    return await reverse_geocode_postcode(hass, lat, lon)
