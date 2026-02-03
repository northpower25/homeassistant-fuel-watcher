"""
Commit: feat(statistics): add self-learning consumption and range statistics engine

Fuel Watcher – Statistics Engine
--------------------------------
Diese Datei implementiert die selbstlernende Verbrauchs- und Reichweitenlogik,
wie sie in v0.0.27 beschrieben war – jetzt basierend auf der neuen Storage-Architektur.

Funktionen:
- Odometer-Verlauf auswerten
- Tageskilometer berechnen
- Wochentags-Durchschnittswerte pflegen
- Durchschnittliche Tageskilometer berechnen
- Reichweite in Tagen schätzen

Die Rohdaten (odometer_history, weekday_consumption) werden in storage.py gehalten.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import load_data, update_weekday_consumption


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


async def get_odometer_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> List[Dict[str, Any]]:
    """Return full odometer history."""
    data = await load_data(hass, entry)
    return data.get("odometer_history", [])


async def get_weekday_stats(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Dict[int, Dict[str, Any]]:
    """Return weekday consumption statistics."""
    data = await load_data(hass, entry)
    return data.get("weekday_consumption", {})


async def recompute_weekday_stats(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """
    Recompute weekday statistics from odometer history.

    Diese Funktion kann genutzt werden, falls sich die Logik ändert oder
    historische Daten neu berechnet werden sollen.
    """
    data = await load_data(hass, entry)
    odo = data.get("odometer_history", [])

    # Reset stats
    data["weekday_consumption"] = {}
    stats = data["weekday_consumption"]

    if len(odo) < 2:
        # Not enough data
        await update_weekday_consumption(hass, entry, 0, 0.0)
        return

    # Sort by timestamp
    odo_sorted = sorted(
        odo,
        key=lambda x: _parse_ts(x.get("ts") or "") or datetime.min,
    )

    last = odo_sorted[0]
    last_ts = _parse_ts(last.get("ts") or "")
    last_val = last.get("value")

    for entry_ in odo_sorted[1:]:
        ts = _parse_ts(entry_.get("ts") or "")
        val = entry_.get("value")

        if ts is None or last_ts is None:
            last_ts = ts
            last_val = val
            continue

        try:
            km = float(val) - float(last_val)
        except Exception:
            last_ts = ts
            last_val = val
            continue

        if km <= 0:
            last_ts = ts
            last_val = val
            continue

        weekday = ts.weekday()
        if weekday not in stats:
            stats[weekday] = {"km": 0.0, "count": 0}

        stats[weekday]["km"] += km
        stats[weekday]["count"] += 1

        last_ts = ts
        last_val = val

    data["weekday_consumption"] = stats
    from .storage import save_data  # lazy import to avoid cycles
    await save_data(hass, entry, data)


async def get_avg_daily_km(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    fallback: float = 40.0,
) -> float:
    """
    Compute average daily kilometers based on weekday statistics.

    Wenn keine oder zu wenige Daten vorhanden sind, wird der Fallback-Wert genutzt.
    """
    stats = await get_weekday_stats(hass, entry)

    if not stats:
        return fallback

    total_km = 0.0
    total_days = 0

    for wd, s in stats.items():
        km = float(s.get("km", 0.0))
        count = int(s.get("count", 0))
        if count <= 0:
            continue
        total_km += km
        total_days += count

    if total_days <= 0:
        return fallback

    avg = total_km / total_days
    # Begrenzen auf sinnvolle Werte
    if avg <= 0:
        return fallback

    return round(avg, 1)


async def estimate_days_left(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    km_left: Optional[float],
    fallback_daily_km: float = 40.0,
) -> Optional[float]:
    """
    Estimate remaining days based on km_left and learned daily km.

    Wird von Strategy-Sensoren genutzt, um sensor.fuel_watcher_days_left zu berechnen.
    """
    if km_left is None:
        return None

    avg_daily_km = await get_avg_daily_km(hass, entry, fallback=fallback_daily_km)
    if avg_daily_km <= 0:
        return None

    days = km_left / avg_daily_km
    return round(days, 1)
