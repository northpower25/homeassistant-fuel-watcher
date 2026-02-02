from __future__ import annotations

from datetime import datetime
from homeassistant.config_entries import ConfigEntry

from .const import WEEKDAY_OPTIONS


def get_expected_consumption_tomorrow(entry: ConfigEntry, weekday_consumption: dict | None = None) -> int:
    options = entry.options or entry.data
    weekday = datetime.now().weekday()
    tomorrow = (weekday + 1) % 7
    key = WEEKDAY_OPTIONS[tomorrow]

    if weekday_consumption and key in weekday_consumption:
        return int(round(weekday_consumption[key]))

    return int(options.get(key, 50))
