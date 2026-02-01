from __future__ import annotations

import logging
from math import radians, sin, cos, sqrt, atan2

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .base import fetch_json
from ..const import CONF_TANKERKOENIG_API, CONF_FUEL, CONF_RADIUS, CONF_ENTITY_LOCATION

_LOGGER = logging.getLogger(__name__)


def _distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


async def get_price_data(hass: HomeAssistant, entry: ConfigEntry):
    api_key = entry.data.get(CONF_TANKERKOENIG_API)
    fuel = entry.data.get(CONF_FUEL, "e5")
    radius = entry.data.get(CONF_RADIUS, 5)

    # Standort des Fahrzeugs
    location_entity = entry.data.get(CONF_ENTITY_LOCATION)
    location = hass.states.get(location_entity)

    if not location:
        _LOGGER.warning("No location entity available: %s", location_entity)
        return None

    try:
        lat = float(location.attributes.get("latitude"))
        lng = float(location.attributes.get("longitude"))
    except Exception:
        _LOGGER.error("Invalid location entity: %s", location_entity)
        return None

    url = (
        f"https://creativecommons.tankerkoenig.de/json/list.php?"
        f"lat={lat}&lng={lng}&rad={radius}&sort=price&type={fuel}&apikey={api_key}"
    )

    async with hass.helpers.aiohttp_client.async_get_clientsession() as session:
        data = await fetch_json(session, url)

    if not data or "stations" not in data:
        _LOGGER.error("Invalid response from Tankerkoenig API")
        return None

    stations = data["stations"]
    if not stations:
        return None

    # Günstigste Tankstelle auswählen
    station = min(stations, key=lambda s: s.get("price", 999))

    distance = _distance_km(lat, lng, station["lat"], station["lng"])

    return {
        "price": station.get("price"),
        "station": station.get("name"),
        "lat": station.get("lat"),
        "lng": station.get("lng"),
        "distance_km": round(distance, 2),
        "fuel": fuel,
    }
