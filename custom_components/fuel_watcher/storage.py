"""
Commit: feat(storage): introduce unified HA storage backend for tank, odometer, price and statistics data

Fuel Watcher – Unified Storage Backend
--------------------------------------
Diese Datei ersetzt die alte JSON-Datenhaltung vollständig.

Gespeichert werden:
- Tankhistorie
- Odometer-Historie
- Preis-Historie
- Wochentags-Verbrauch
- Letzte API-Antwort
- Letzte Telegram-Nachricht
- Letzter Fehler
- Beste Tankstelle (Tankerkoenig)

Alle Daten liegen in:
  .storage/fuel_watcher_<entry_id>.json

und werden über Home Assistants Storage-API verwaltet.
"""

from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = "fuel_watcher_{}"


def _store(hass: HomeAssistant, entry: ConfigEntry) -> Store:
    """Return HA storage instance for this config entry."""
    key = STORAGE_KEY_TEMPLATE.format(entry.entry_id)
    return Store(hass, STORAGE_VERSION, key)


async def load_data(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Load all stored data for this entry."""
    store = _store(hass, entry)
    data = await store.async_load()

    if not data:
        data = {
            "tank_history": [],
            "odometer_history": [],
            "price_history": [],
            "weekday_consumption": {},
            "best_station": None,
            "last_api": None,
            "last_telegram": None,
            "last_error": None,
        }

    return data


async def save_data(hass: HomeAssistant, entry: ConfigEntry, data: dict) -> None:
    """Persist all data."""
    store = _store(hass, entry)
    await store.async_save(data)


# ---------------------------------------------------------------------------
# Tankhistorie
# ---------------------------------------------------------------------------

async def append_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    price_per_liter: float,
    liters: float | None = None,
    total_cost: float | None = None,
    station_name: str | None = None,
    odometer: float | None = None,
    source: str = "manual",
) -> dict:
    """Add a tank event to the history."""
    data = await load_data(hass, entry)
    events = data["tank_history"]

    if liters is not None and total_cost is None:
        total_cost = round(liters * price_per_liter, 2)

    event_id = max((e.get("id", 0) for e in events), default=0) + 1

    event = {
        "id": event_id,
        "ts": datetime.utcnow().isoformat(),
        "price_per_liter": price_per_liter,
        "liters": liters,
        "total_cost": total_cost,
        "station_name": station_name,
        "odometer": odometer,
        "source": source,
    }

    events.append(event)
    data["tank_history"] = events

    await save_data(hass, entry, data)
    return event


async def update_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    event_id: int,
    **updates,
) -> bool:
    """Update an existing tank event."""
    data = await load_data(hass, entry)
    events = data["tank_history"]

    updated = False
    for ev in events:
        if ev.get("id") == event_id:
            ev.update(updates)
            updated = True
            break

    if updated:
        await save_data(hass, entry, data)

    return updated


async def delete_tank_event(hass: HomeAssistant, entry: ConfigEntry, *, event_id: int) -> bool:
    """Delete a tank event."""
    data = await load_data(hass, entry)
    events = data["tank_history"]

    new_events = [e for e in events if e.get("id") != event_id]
    deleted = len(new_events) != len(events)

    if deleted:
        data["tank_history"] = new_events
        await save_data(hass, entry, data)

    return deleted


async def clear_tank_history(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear all tank events."""
    data = await load_data(hass, entry)
    data["tank_history"] = []
    await save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# Odometer / Verbrauch
# ---------------------------------------------------------------------------

async def append_odometer(hass: HomeAssistant, entry: ConfigEntry, value: float) -> None:
    """Append odometer reading."""
    data = await load_data(hass, entry)
    data["odometer_history"].append(
        {"value": value, "ts": datetime.utcnow().isoformat()}
    )
    await save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# Preis-Historie
# ---------------------------------------------------------------------------

async def append_price(hass: HomeAssistant, entry: ConfigEntry, price: float) -> None:
    """Append price reading."""
    data = await load_data(hass, entry)
    data["price_history"].append(
        {"price": price, "ts": datetime.utcnow().isoformat()}
    )
    await save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# Weekday Consumption
# ---------------------------------------------------------------------------

async def update_weekday_consumption(
    hass: HomeAssistant,
    entry: ConfigEntry,
    weekday: int,
    km: float,
) -> None:
    """Update weekday consumption statistics."""
    data = await load_data(hass, entry)
    stats = data["weekday_consumption"]

    if weekday not in stats:
        stats[weekday] = {"km": 0.0, "count": 0}

    stats[weekday]["km"] += km
    stats[weekday]["count"] += 1

    data["weekday_consumption"] = stats
    await save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# Best Station (Tankerkoenig)
# ---------------------------------------------------------------------------

async def set_best_station(hass: HomeAssistant, entry: ConfigEntry, station: dict) -> None:
    """Store best station from Tankerkoenig."""
    data = await load_data(hass, entry)
    data["best_station"] = station
    await save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

async def set_last_api(hass: HomeAssistant, entry: ConfigEntry, payload: dict | str) -> None:
    data = await load_data(hass, entry)
    data["last_api"] = payload
    await save_data(hass, entry, data)


async def set_last_telegram(hass: HomeAssistant, entry: ConfigEntry, payload: dict | str) -> None:
    data = await load_data(hass, entry)
    data["last_telegram"] = payload
    await save_data(hass, entry, data)


async def set_last_error(hass: HomeAssistant, entry: ConfigEntry, error: str | dict | None) -> None:
    data = await load_data(hass, entry)
    data["last_error"] = error
    await save_data(hass, entry, data)
