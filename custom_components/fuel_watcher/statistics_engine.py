from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, WEEKDAY_OPTIONS

_LOGGER = logging.getLogger(__name__)


def _get_stats_path(hass: HomeAssistant, entry: ConfigEntry) -> str:
    base = hass.config.path(f"custom_components/{DOMAIN}/data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{entry.entry_id}_stats.json")


def _load_stats(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    path = _get_stats_path(hass, entry)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading stats file %s: %s", path, e)
        return {}


def _save_stats(hass: HomeAssistant, entry: ConfigEntry, data: dict[str, Any]) -> None:
    path = _get_stats_path(hass, entry)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _LOGGER.error("Error saving stats file %s: %s", path, e)


def update_odometer_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
    odometer: float | None,
) -> None:
    if odometer is None:
        return

    stats = _load_stats(hass, entry)
    history = stats.get("odometer", [])
    now = datetime.utcnow().isoformat()

    history.append({"ts": now, "value": odometer})
    # Begrenzen
    history = history[-60:]
    stats["odometer"] = history
    _save_stats(hass, entry, stats)


def compute_weekday_consumption(
    hass: HomeAssistant,
    entry: ConfigEntry,
    fallback_options: dict,
) -> dict[str, float]:
    """
    Versucht, aus Odometer-Historie Tageskilometer zu berechnen
    und daraus Wochentagsdurchschnitt zu bilden.
    Fällt auf Konfiguration zurück, wenn zu wenig Daten.
    """
    stats = _load_stats(hass, entry)
    history = stats.get("odometer", [])
    if len(history) < 3:
        # Zu wenig Daten -> Fallback
        return {
            key: float(fallback_options.get(key, 50))
            for key in WEEKDAY_OPTIONS
        }

    # Odometer sortieren
    history_sorted = sorted(history, key=lambda x: x["ts"])
    daily_km: dict[int, list[float]] = {i: [] for i in range(7)}

    last = None
    for item in history_sorted:
        try:
            ts = datetime.fromisoformat(item["ts"])
        except Exception:
            continue
        value = float(item["value"])
        if last is not None:
            last_ts, last_val = last
            delta_km = value - last_val
            if delta_km > 0:
                weekday = ts.weekday()
                daily_km[weekday].append(delta_km)
        last = (ts, value)

    result: dict[str, float] = {}
    for idx, key in enumerate(WEEKDAY_OPTIONS):
        values = daily_km.get(idx, [])
        if values:
            avg = sum(values) / len(values)
            result[key] = round(avg, 1)
        else:
            result[key] = float(fallback_options.get(key, 50))

    stats["weekday_consumption"] = result
    _save_stats(hass, entry, stats)
    return result


def compute_days_left_from_weekdays(
    entry: ConfigEntry,
    weekday_consumption: dict[str, float],
    range_km: float | None,
) -> float:
    if range_km is None or range_km <= 0:
        return 0.0

    options = entry.options or entry.data
    weekday = datetime.now().weekday()
    remaining = float(range_km)
    days = 0.0

    for _ in range(30):
        key = WEEKDAY_OPTIONS[weekday]
        day_consumption = float(weekday_consumption.get(key, options.get(key, 50)))
        if day_consumption <= 0:
            day_consumption = 1.0

        remaining -= day_consumption
        days += 1.0

        if remaining <= 0:
            break

        weekday = (weekday + 1) % 7

    if remaining > 0:
        days += remaining / max(day_consumption, 1.0)

    return round(days, 1)
