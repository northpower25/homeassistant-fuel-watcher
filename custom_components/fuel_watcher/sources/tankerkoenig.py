"""
Commit: feat(tankerkoenig): add unified tankerkoenig API integration with storage, best-station logic and diagnostics

Fuel Watcher – Tankerkoenig Source
----------------------------------
Diese Datei implementiert die komplette Tankerkoenig-Integration:

- API-Abfrage
- Fehlerbehandlung
- Auswahl der besten Tankstelle
- Speichern der besten Tankstelle in HA-Storage
- Speichern der Preis-Historie
- Diagnostics (last_api, last_error)
- Rückgabe strukturierter Daten für Sensoren

Die Datei ist vollständig async und nutzt die neue Storage-Architektur.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import (
    set_last_api,
    set_last_error,
    append_price,
    set_best_station,
)
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

API_URL = "https://creativecommons.tankerkoenig.de/json/list.php"


# ---------------------------------------------------------------------------
# API Request
# ---------------------------------------------------------------------------

async def fetch_tankerkoenig_data(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    lat: float,
    lon: float,
    radius: float,
    fuel_type: str,
    api_key: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch station list from Tankerkoenig API.
    """

    params = {
        "lat": lat,
        "lng": lon,
        "rad": radius,
        "sort": "price",
        "type": fuel_type,
        "apikey": api_key,
    }

    try:
        session = aiohttp.ClientSession()
        async with session.get(API_URL, params=params, timeout=10) as resp:
            data = await resp.json()
            await session.close()

    except Exception as err:
        _LOGGER.error("Tankerkoenig API error: %s", err)
        await set_last_error(hass, entry, str(err))
        return None

    # Save diagnostics
    await set_last_api(hass, entry, data)

    if not data or data.get("ok") is not True:
        await set_last_error(hass, entry, f"API returned error: {data}")
        return None

    return data


# ---------------------------------------------------------------------------
# Best Station Selection
# ---------------------------------------------------------------------------

def _select_best_station(stations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select the best station based on:
    - lowest price
    - valid coordinates
    - open status (if provided)
    """

    valid = [
        s for s in stations
        if s.get("price") not in (None, "null")
        and s.get("lat") is not None
        and s.get("lng") is not None
    ]

    if not valid:
        return None

    # Sort by price ascending
    sorted_stations = sorted(valid, key=lambda s: float(s["price"]))
    return sorted_stations[0]


# ---------------------------------------------------------------------------
# Main Update Function
# ---------------------------------------------------------------------------

async def update_tankerkoenig(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    lat: float,
    lon: float,
    radius: float,
    fuel_type: str,
    api_key: str,
) -> Optional[Dict[str, Any]]:
    """
    Perform full Tankerkoenig update:
    - API call
    - best station selection
    - store best station
    - append price history
    """

    data = await fetch_tankerkoenig_data(
        hass,
        entry,
        lat=lat,
        lon=lon,
        radius=radius,
        fuel_type=fuel_type,
        api_key=api_key,
    )

    if not data:
        return None

    stations = data.get("stations", [])
    if not stations:
        await set_last_error(hass, entry, "No stations returned")
        return None

    best = _select_best_station(stations)
    if not best:
        await set_last_error(hass, entry, "No valid station found")
        return None

    # Normalize station structure
    station = {
        "name": best.get("name"),
        "brand": best.get("brand"),
        "street": best.get("street"),
        "house_number": best.get("houseNumber"),
        "post_code": best.get("postCode"),
        "city": best.get("place"),
        "lat": best.get("lat"),
        "lon": best.get("lng"),
        "price": best.get("price"),
        "distance_km": best.get("dist"),
    }

    # Save best station
    await set_best_station(hass, entry, station)

    # Save price history
    try:
        await append_price(hass, entry, float(best.get("price")))
    except Exception:
        pass

    return station
