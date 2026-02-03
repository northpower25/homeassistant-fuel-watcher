"""
Commit: feat(diagnostics): add full diagnostics export including storage and config

Fuel Watcher – Diagnostics
--------------------------
Ermöglicht Home Assistant, eine Diagnose-Datei zu exportieren:

- ConfigEntry-Daten
- Options
- Storage-Inhalt
- Letzter API-Call
- Letzte Entscheidung
- Letzte Telegram-Nachricht
- Letzter Fehler
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import _load_data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    """Return diagnostics for a config entry."""

    storage = await _load_data(hass, entry)

    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "data": entry.data,
        "options": entry.options,
        "storage": storage,
    }
