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
