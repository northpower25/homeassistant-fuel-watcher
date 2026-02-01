import json
import async_timeout
import logging
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


async def get_cheapest_tankerkoenig(hass, api_key, lat, lon, radius, fuel):
    """Call Tankerkoenig list API using lat/lng."""
    url = (
        "https://creativecommons.tankerkoenig.de/json/list.php"
        f"?lat={lat}&lng={lon}&rad={radius}&sort=price&type={fuel}&apikey={api_key}"
    )

    _LOGGER.warning(f"[FuelWatcher] Tankerkönig URL: {url}")

    session = async_get_clientsession(hass)

    try:
        async with async_timeout.timeout(10):
            async with session.get(url) as resp:
                status = resp.status
                text = await resp.text()

                _LOGGER.warning(f"[FuelWatcher] Tankerkönig HTTP Status: {status}")
                _LOGGER.warning(f"[FuelWatcher] Tankerkönig Antwort RAW: {text}")

                try:
                    data = json.loads(text)
                except Exception as e:
                    _LOGGER.error(f"[FuelWatcher] JSON Parse Fehler: {e}")
                    return None

                _LOGGER.warning(f"[FuelWatcher] Tankerkönig Parsed JSON: {data}")

    except Exception as e:
        _LOGGER.error(f"[FuelWatcher] Tankerkönig API Fehler: {e}")
        return None

    if data.get("status") != "ok":
        _LOGGER.error(f"[FuelWatcher] Tankerkönig Status != ok: {data.get('message')}")
        return None

    stations = data.get("stations", [])
    if not stations:
        _LOGGER.error("[FuelWatcher] Tankerkönig: Keine Stationen gefunden")
        return None

    stations = [s for s in stations if s.get("price") is not None]
    if not stations:
        _LOGGER.error("[FuelWatcher] Tankerkönig: Keine Preise gefunden")
        return None

    cheapest = min(stations, key=lambda x: x["price"])

    return {
        "price": cheapest["price"],
        "name": cheapest["name"],
        "lat": cheapest.get("lat"),
        "lng": cheapest.get("lng"),
    }
