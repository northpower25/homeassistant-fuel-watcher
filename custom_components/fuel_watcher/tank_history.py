"""
Commit: refactor(tank_history): migrate tank history to unified HA storage backend

Fuel Watcher – Tank History Wrapper
-----------------------------------
Diese Datei ersetzt die alte JSON-basierte Tankhistorie vollständig.

Sie dient als API-Schicht zwischen:
- storage.py (persistente Datenhaltung)
- Sensoren
- Services
- Telegram-Parser
- Strategy-Engine

Alle Tankvorgänge werden über storage.py verwaltet.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import (
    load_data,
    append_tank_event,
    update_tank_event,
    delete_tank_event,
    clear_tank_history,
)


# ---------------------------------------------------------------------------
# High-level API for Tank History
# ---------------------------------------------------------------------------

async def get_tank_events(hass: HomeAssistant, entry: ConfigEntry) -> List[Dict[str, Any]]:
    """Return full tank history."""
    data = await load_data(hass, entry)
    return data.get("tank_history", [])


async def get_last_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Optional[Dict[str, Any]]:
    """Return the most recent tank event."""
    events = await get_tank_events(hass, entry)
    if not events:
        return None

    # Events are stored in chronological order → last = newest
    return events[-1]


async def add_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    price_per_liter: float,
    liters: Optional[float] = None,
    total_cost: Optional[float] = None,
    station_name: Optional[str] = None,
    odometer: Optional[float] = None,
    source: str = "manual",
) -> Dict[str, Any]:
    """Add a tank event (wrapper for storage)."""
    return await append_tank_event(
        hass,
        entry,
        price_per_liter=price_per_liter,
        liters=liters,
        total_cost=total_cost,
        station_name=station_name,
        odometer=odometer,
        source=source,
    )


async def modify_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    event_id: int,
    **updates,
) -> bool:
    """Update an existing tank event."""
    return await update_tank_event(hass, entry, event_id=event_id, **updates)


async def remove_tank_event(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    event_id: int,
) -> bool:
    """Delete a tank event."""
    return await delete_tank_event(hass, entry, event_id=event_id)


async def wipe_tank_history(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete all tank events."""
    await clear_tank_history(hass, entry)
