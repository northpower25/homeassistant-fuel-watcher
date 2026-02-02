from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _get_data_path(hass: HomeAssistant, entry: ConfigEntry) -> str:
    base = hass.config.path(f"custom_components/{DOMAIN}/data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{entry.entry_id}.json")


def _load_data(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    path = _get_data_path(hass, entry)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading tank history file %s: %s", path, e)
        return {}


def _save_data(hass: HomeAssistant, entry: ConfigEntry, data: dict[str, Any]) -> None:
    path = _get_data_path(hass, entry)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _LOGGER.error("Error saving tank history file %s: %s", path, e)


def append_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    price_per_liter: float,
    liters: float | None = None,
    total_cost: float | None = None,
    station_id: str | None = None,
    station_name: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    odometer: float | None = None,
) -> None:
    data = _load_data(hass, entry)
    events = data.get("tank_events", [])

    if liters is not None and total_cost is None:
        total_cost = round(liters * price_per_liter, 2)

    event = {
        "ts": datetime.utcnow().isoformat(),
        "price_per_liter": price_per_liter,
        "liters": liters,
        "total_cost": total_cost,
        "station_id": station_id,
        "station_name": station_name,
        "lat": lat,
        "lng": lng,
        "odometer": odometer,
    }
    events.append(event)
    data["tank_events"] = events
    _save_data(hass, entry, data)


def get_last_tank_event(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    data = _load_data(hass, entry)
    events = data.get("tank_events", [])
    if not events:
        return None
    return events[-1]
