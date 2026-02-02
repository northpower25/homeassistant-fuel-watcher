from __future__ import annotations

from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import WEEKDAY_OPTIONS


def get_expected_consumption_tomorrow(entry: ConfigEntry) -> int:
    """
    Returns the expected consumption (km) for tomorrow.
    Uses user-defined weekday defaults until real statistics are available.
    """
    options = entry.options or entry.data
    weekday = datetime.now().weekday()
    tomorrow = (weekday + 1) % 7
    key = WEEKDAY_OPTIONS[tomorrow]
    return options.get(key, 50)


def compute_days_left(entry: ConfigEntry, range_km: float) -> float:
    """
    Estimate how many days the current range will last,
    based on weekday consumption configuration.
    """
    if range_km is None or range_km <= 0:
        return 0.0

    options = entry.options or entry.data
    weekday = datetime.now().weekday()
    remaining = float(range_km)
    days = 0

    # Simuliere maximal 30 Tage, um Endlosschleifen zu vermeiden
    for _ in range(30):
        key = WEEKDAY_OPTIONS[weekday]
        day_consumption = float(options.get(key, 50))
        if day_consumption <= 0:
            # Schutz: wenn jemand 0 km eingibt, nehmen wir 1 km
            day_consumption = 1.0

        remaining -= day_consumption
        days += 1

        if remaining <= 0:
            break

        weekday = (weekday + 1) % 7

    # Grobe Nachkommastelle
    return round(days + max(remaining, 0) / max(day_consumption, 1.0), 1)
