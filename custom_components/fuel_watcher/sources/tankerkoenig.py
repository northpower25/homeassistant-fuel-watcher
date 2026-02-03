"""
Commit: fix(location) + feat(strategy): robust coordinate extraction & price threshold logic

Fuel Watcher – Tankerkoenig Source
----------------------------------
Diese Version enthält:
- Robuste Extraktion von LAT/LON aus jeder Location-Entität
  (state="lat,lon" ODER attributes.latitude/longitude)
- Fallback auf HA-Home-Location, wenn Fahrzeugposition fehlt
- Integration der Strategy-Engine (Preis-Schwellwerte)
- Multi-Vehicle Support
- Verbesserte Fehlerbehandlung
"""

from __future__ import annotations

import logging
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_TANKERKOENIG_API,
    CONF_FUEL_TYPE,
    CONF_RADIUS,
    CONF_ENTITY_LOCATION,
)
from ..strategy_engine import evaluate_strategy
from ..storage import set_last_api, set_last_error

_LOGGER = logging.getLogger(__name__)

TK_URL = "https://creativecommons.tankerkoenig.de/json/list.php"


# ---------------------------------------------------------------------------
# LOCATION HANDLING
# ---------------------------------------------------------------------------

def get_location_from_entity(hass: HomeAssistant, entity_id: str):
    """Extract latitude/longitude from any location entity.

    Unterstützt:
    - state = "lat,lon"
    - attributes.latitude / attributes.longitude
    - device_tracker (state = home/away)
    """

    state_obj = hass.states.get(entity_id)
    if not state_obj:
        _LOGGER.error("Location entity not found: %s", entity_id)
        return None

    # 1) Try parsing state directly
    if isinstance(state_obj.state, str) and "," in state_obj.state:
        try:
            lat_str, lon_str = state_obj.state.split(",", 1)
            return float(lat_str), float(lon_str)
        except Exception:
            pass  # fallback to attributes

    # 2) Try attributes (device_tracker, mobile_app, car integrations)
    attrs = state_obj.attributes
    lat = attrs.get("latitude")
    lon = attrs.get("longitude")

    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except Exception:
            _LOGGER.error("Invalid lat/lon attributes in %s", entity_id)
            return None

    # 3) No valid coordinates found
    _LOGGER.error(
        "Invalid location entity: %s (no coordinates in state or attributes)",
        entity_id,
    )
    return None


# ---------------------------------------------------------------------------
# MAIN API CALL
# ---------------------------------------------------------------------------

async def update_tankerkoenig(hass: HomeAssistant, entry: ConfigEntry):
    """Fetch price data from Tankerkoenig and evaluate strategy."""

    api_key = entry.data.get(CONF_TANKERKOENIG_API)
    fuel_type = entry.data.get(CONF_FUEL_TYPE)
    radius = entry.data.get(CONF_RADIUS, 5)

    # ----------------------------------------------------------------------
    # LOCATION RESOLUTION
    # ----------------------------------------------------------------------
    location_entity = entry.options.get(CONF_ENTITY_LOCATION)
    coords = None

    if location_entity:
        coords = get_location_from_entity(hass, location_entity)

    if coords is None:
        # fallback: HA home location
        lat = hass.config.latitude
        lon = hass.config.longitude
        _LOGGER.debug("Using HA home location: %s, %s", lat, lon)
    else:
        lat, lon = coords
        _LOGGER.debug("Using vehicle location: %s, %s", lat, lon)

    # ----------------------------------------------------------------------
    # API CALL
    # ----------------------------------------------------------------------
    params = {
        "lat": lat,
        "lng": lon,
        "rad": radius,
        "sort": "price",
        "type": fuel_type,
        "apikey": api_key,
    }

    try:
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(TK_URL, params=params) as resp:
                    if resp.status != 200:
                        msg = f"HTTP {resp.status} from Tankerkoenig"
                        _LOGGER.error(msg)
                        await set_last_error(hass, entry, msg)
                        return None

                    data = await resp.json()
                    await set_last_api(hass, entry, data)

    except Exception as e:
        msg = f"Tankerkoenig request failed: {e}"
        _LOGGER.error(msg)
        await set_last_error(hass, entry, msg)
        return None

    if "stations" not in data or not data["stations"]:
        msg = "No stations returned by Tankerkoenig"
        _LOGGER.error(msg)
        await set_last_error(hass, entry, msg)
        return None

    # Best station
    station = data["stations"][0]
    price = station.get("price")

    if price is None:
        msg = "Station has no price data"
        _LOGGER.error(msg)
        await set_last_error(hass, entry, msg)
        return None

    # ----------------------------------------------------------------------
    # STRATEGY EVALUATION
    # ----------------------------------------------------------------------
    strategy = await evaluate_strategy(
        hass=hass,
        entry=entry,
        current_price=price,
        station_name=station.get("name", "Unknown"),
    )

    return {
        "station": station,
        "price": price,
        "strategy": strategy,
        "lat": lat,
        "lon": lon,
    }
