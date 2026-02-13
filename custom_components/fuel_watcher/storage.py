"""
Commit: feat(storage): add per-entry versioned storage for price, decision, api and telegram

Fuel Watcher – Storage Layer
----------------------------
Speichert pro ConfigEntry (pro Fahrzeug) folgende Daten:

- last_price: float
- last_decision: dict
- last_api: dict (Rohdaten von Tankerkoenig)
- last_telegram: dict (zuletzt gesendete Nachricht)

Jeder ConfigEntry bekommt eine eigene Storage-Datei:
- .storage/fuel_watcher_<entry_id>.json

Versionierung:
- version: int
- bei späteren Änderungen kann eine Migration implementiert werden.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = f"{DOMAIN}_{{entry_id}}"


def _get_store(hass: HomeAssistant, entry: ConfigEntry) -> Store:
    """Return a Store instance for this config entry."""
    key = STORAGE_KEY_TEMPLATE.format(entry_id=entry.entry_id)
    return Store(hass, STORAGE_VERSION, key)


async def _load_data(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Load storage data for this entry."""
    store = _get_store(hass, entry)
    data = await store.async_load()
    if not data:
        data = {
            "version": STORAGE_VERSION,
            "last_price": None,
            "last_decision": None,
            "last_api": None,
            "last_telegram": None,
            "last_error": None,
            # Trip tracking data (Phase 1)
            "trips": [],
            "trip_patterns": [],
            "pois": [],
            "trip_tracking_config": {
                "enabled": False,
                "privacy_notice_accepted": False,
                "min_trip_distance_km": 0.5,
                "merge_time_window_minutes": 5,
                "tax_mileage_rate_default": 0.30,
                "tax_mileage_rate_long_distance": 0.38,
                "retention_days": 365,
                "anonymization_schedules": [],
                "geocoding_enabled": True,
                "geocoding_cache_enabled": True,
            },
            "trip_statistics": {
                "total_trips": 0,
                "total_distance_km": 0.0,
                "total_fuel_consumed_liters": 0.0,
                "total_fuel_cost_euros": 0.0,
                "total_additional_costs_euros": 0.0,
                "business_trips": 0,
                "business_distance_km": 0.0,
                "private_trips": 0,
                "private_distance_km": 0.0,
                "commute_trips": 0,
                "commute_distance_km": 0.0,
                "avg_distance_km": 0.0,
                "avg_fuel_consumption_per_100km": 0.0,
                "avg_cost_per_km": 0.0,
                "last_updated": None,
            },
            "current_trip": None,
        }
    return data


async def _save_data(hass: HomeAssistant, entry: ConfigEntry, data: dict) -> None:
    """Save storage data for this entry."""
    store = _get_store(hass, entry)
    await store.async_save(data)


# ---------------------------------------------------------------------------
# BACKWARDS COMPATIBILITY WRAPPER
# ---------------------------------------------------------------------------

async def load_data(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """
    Backwards compatible wrapper for older versions.

    Einige ältere Dateien (oder alte HACS-Caches) importieren noch:
        from .storage import load_data

    Damit diese Version weiterhin funktioniert, ohne dass der Config-Flow crasht,
    leiten wir den Aufruf einfach an _load_data weiter.
    """
    return await _load_data(hass, entry)


# ---------------------------------------------------------------------------
# last_price
# ---------------------------------------------------------------------------

async def get_last_price(hass: HomeAssistant, entry: ConfigEntry) -> float | None:
    """Get last known price for this entry."""
    data = await _load_data(hass, entry)
    return data.get("last_price")


async def set_last_price(hass: HomeAssistant, entry: ConfigEntry, price: float) -> None:
    """Set last known price for this entry."""
    data = await _load_data(hass, entry)
    data["last_price"] = price
    await _save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# last_decision
# ---------------------------------------------------------------------------

async def get_last_decision(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    """Get last strategy decision for this entry."""
    data = await _load_data(hass, entry)
    return data.get("last_decision")


async def set_last_decision(hass: HomeAssistant, entry: ConfigEntry, decision: dict) -> None:
    """Set last strategy decision for this entry."""
    data = await _load_data(hass, entry)
    data["last_decision"] = decision
    await _save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# last_api
# ---------------------------------------------------------------------------

async def get_last_api(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    """Get last Tankerkoenig API response for this entry."""
    data = await _load_data(hass, entry)
    return data.get("last_api")


async def set_last_api(hass: HomeAssistant, entry: ConfigEntry, api_data: dict) -> None:
    """Set last Tankerkoenig API response for this entry."""
    data = await _load_data(hass, entry)
    data["last_api"] = api_data
    await _save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# last_telegram
# ---------------------------------------------------------------------------

async def get_last_telegram(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    """Get last sent telegram message for this entry."""
    data = await _load_data(hass, entry)
    return data.get("last_telegram")


async def set_last_telegram(hass: HomeAssistant, entry: ConfigEntry, telegram_data: dict) -> None:
    """Set last sent telegram message for this entry."""
    data = await _load_data(hass, entry)
    data["last_telegram"] = telegram_data
    await _save_data(hass, entry, data)


# ---------------------------------------------------------------------------
# last_error (für Diagnose)
# ---------------------------------------------------------------------------

async def get_last_error(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Get last error message for this entry."""
    data = await _load_data(hass, entry)
    return data.get("last_error")


async def set_last_error(hass: HomeAssistant, entry: ConfigEntry, error: str) -> None:
    """Set last error message for this entry."""
    data = await _load_data(hass, entry)
    data["last_error"] = error
    await _save_data(hass, entry, data)
    _LOGGER.error("Fuel Watcher [%s]: %s", entry.title, error)


# ---------------------------------------------------------------------------
# Trip Tracking Storage (Phase 1)
# ---------------------------------------------------------------------------

async def get_trip_tracking_config(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Get trip tracking configuration."""
    data = await _load_data(hass, entry)
    return data.get("trip_tracking_config", {})


async def set_trip_tracking_config(hass: HomeAssistant, entry: ConfigEntry, config: dict) -> None:
    """Set trip tracking configuration."""
    data = await _load_data(hass, entry)
    data["trip_tracking_config"] = config
    await _save_data(hass, entry, data)


async def get_trips(hass: HomeAssistant, entry: ConfigEntry) -> list[dict]:
    """Get all trips."""
    data = await _load_data(hass, entry)
    return data.get("trips", [])


async def add_trip(hass: HomeAssistant, entry: ConfigEntry, trip: dict) -> None:
    """Add a new trip."""
    data = await _load_data(hass, entry)
    if "trips" not in data:
        data["trips"] = []
    data["trips"].append(trip)
    await _save_data(hass, entry, data)


async def update_trip(hass: HomeAssistant, entry: ConfigEntry, trip_id: str, trip: dict) -> bool:
    """Update an existing trip. Returns True if found and updated."""
    data = await _load_data(hass, entry)
    trips = data.get("trips", [])
    
    for i, existing_trip in enumerate(trips):
        if existing_trip.get("trip_id") == trip_id:
            trips[i] = trip
            data["trips"] = trips
            await _save_data(hass, entry, data)
            return True
    
    return False


async def delete_trip(hass: HomeAssistant, entry: ConfigEntry, trip_id: str) -> bool:
    """Delete a trip. Returns True if found and deleted."""
    data = await _load_data(hass, entry)
    trips = data.get("trips", [])
    
    new_trips = [t for t in trips if t.get("trip_id") != trip_id]
    
    if len(new_trips) < len(trips):
        data["trips"] = new_trips
        await _save_data(hass, entry, data)
        return True
    
    return False


async def get_current_trip(hass: HomeAssistant, entry: ConfigEntry) -> dict | None:
    """Get current ongoing trip."""
    data = await _load_data(hass, entry)
    return data.get("current_trip")


async def set_current_trip(hass: HomeAssistant, entry: ConfigEntry, trip: dict | None) -> None:
    """Set or clear current ongoing trip."""
    data = await _load_data(hass, entry)
    data["current_trip"] = trip
    await _save_data(hass, entry, data)


async def get_trip_statistics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Get trip statistics."""
    data = await _load_data(hass, entry)
    return data.get("trip_statistics", {})


async def set_trip_statistics(hass: HomeAssistant, entry: ConfigEntry, stats: dict) -> None:
    """Set trip statistics."""
    data = await _load_data(hass, entry)
    data["trip_statistics"] = stats
    await _save_data(hass, entry, data)


async def get_trip_patterns(hass: HomeAssistant, entry: ConfigEntry) -> list[dict]:
    """Get all trip patterns."""
    data = await _load_data(hass, entry)
    return data.get("trip_patterns", [])


async def add_trip_pattern(hass: HomeAssistant, entry: ConfigEntry, pattern: dict) -> None:
    """Add a new trip pattern."""
    data = await _load_data(hass, entry)
    if "trip_patterns" not in data:
        data["trip_patterns"] = []
    data["trip_patterns"].append(pattern)
    await _save_data(hass, entry, data)


async def get_pois(hass: HomeAssistant, entry: ConfigEntry) -> list[dict]:
    """Get all points of interest."""
    data = await _load_data(hass, entry)
    return data.get("pois", [])
