from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_TANK_HISTORY_RETENTION_MONTHS,
    DEFAULT_TANK_HISTORY_RETENTION_MONTHS,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------
# Datei-Handling
# ---------------------------------------------------------

def _get_data_path(hass: HomeAssistant, entry: ConfigEntry) -> str:
    base = hass.config.path(f"custom_components/{DOMAIN}/data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{entry.entry_id}.json")


def _load_data(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    path = _get_data_path(hass, entry)
    if not os.path.exists(path):
        return {"tank_events": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading tank history file %s: %s", path, e)
        return {"tank_events": []}


def _save_data(hass: HomeAssistant, entry: ConfigEntry, data: dict[str, Any]) -> None:
    path = _get_data_path(hass, entry)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _LOGGER.error("Error saving tank history file %s: %s", path, e)


# ---------------------------------------------------------
# Retention
# ---------------------------------------------------------

def _get_retention_months(entry: ConfigEntry) -> int:
    options = entry.options or entry.data
    return int(options.get(CONF_TANK_HISTORY_RETENTION_MONTHS, DEFAULT_TANK_HISTORY_RETENTION_MONTHS))


def _apply_retention(entry: ConfigEntry, events: list[dict]) -> list[dict]:
    months = _get_retention_months(entry)
    if months <= 0:
        return events

    cutoff = datetime.utcnow() - relativedelta(months=months)
    filtered = []

    for ev in events:
        try:
            ts = datetime.fromisoformat(ev.get("ts"))
            if ts >= cutoff:
                filtered.append(ev)
        except Exception:
            filtered.append(ev)

    return filtered


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

def get_tank_events(hass: HomeAssistant, entry: ConfigEntry) -> list[dict]:
    data = _load_data(hass, entry)
    return data.get("tank_events", [])


def get_last_tank_event(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    events = get_tank_events(hass, entry)
    if not events:
        return None
    return events[-1]


def append_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    price_per_liter: float,
    liters: float | None = None,
    total_cost: float | None = None,
    station_name: str | None = None,
    suggested_price: float | None = None,
    odometer: float | None = None,
    source: str = "manual",
) -> None:

    data = _load_data(hass, entry)
    events = data.get("tank_events", [])

    if liters is not None and total_cost is None:
        total_cost = round(liters * price_per_liter, 2)

    savings = None
    if suggested_price is not None:
        savings = round(suggested_price - price_per_liter, 3)

    event = {
        "id": (max([e.get("id", 0) for e in events]) + 1) if events else 1,
        "ts": datetime.utcnow().isoformat(),
        "price_per_liter": price_per_liter,
        "liters": liters,
        "total_cost": total_cost,
        "station_name": station_name,
        "suggested_price": suggested_price,
        "savings": savings,
        "odometer": odometer,
        "source": source,
    }

    events.append(event)
    events = _apply_retention(entry, events)

    data["tank_events"] = events
    _save_data(hass, entry, data)


def update_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    event_id: int,
    **updates,
) -> None:

    data = _load_data(hass, entry)
    events = data.get("tank_events", [])

    for ev in events:
        if int(ev.get("id")) == int(event_id):
            ev.update(updates)

            price = ev.get("price_per_liter")
            suggested = ev.get("suggested_price")
            if price is not None and suggested is not None:
                ev["savings"] = round(suggested - price, 3)
            break

    data["tank_events"] = _apply_retention(entry, events)
    _save_data(hass, entry, data)


def delete_tank_event(hass: HomeAssistant, entry: ConfigEntry, *, event_id: int) -> None:
    data = _load_data(hass, entry)
    events = data.get("tank_events", [])
    data["tank_events"] = [e for e in events if int(e.get("id")) != int(event_id)]
    _save_data(hass, entry, data)


def clear_tank_history(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _save_data(hass, entry, {"tank_events": []})
