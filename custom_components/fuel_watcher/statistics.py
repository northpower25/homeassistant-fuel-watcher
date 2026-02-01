from __future__ import annotations

from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import WEEKDAY_OPTIONS


def get_expected_consumption_tomorrow(entry: ConfigEntry) -> int:
    """
    Returns the expected consumption (km) for tomorrow.
    Uses user-defined weekday defaults until real statistics are available.
    """

    # Options > Data (Options override initial config)
    options = entry.options or entry.data

    # Today (0 = Monday, 6 = Sunday)
    weekday = datetime.now().weekday()

    # Tomorrow
    tomorrow = (weekday + 1) % 7

    # Key for tomorrow
    key = WEEKDAY_OPTIONS[tomorrow]

    # Return configured value (fallback 50 km)
    return options.get(key, 50)


# ---------------------------------------------------------------------------
# OPTIONAL FUTURE STATISTICS ENGINE
# ---------------------------------------------------------------------------

def compute_real_consumption_statistics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    history_days: int = 14,
) -> dict:
    """
    Placeholder for future real consumption statistics.
    This function is intentionally simple for now.

    The idea:
    - Pull odometer history
    - Compute daily km driven
    - Build weekday averages
    - Replace manual values once enough data exists
    """

    # This is a placeholder for future expansion.
    # You can later implement:
    # - hass.history.get_significant_states()
    # - odometer deltas
    # - weekday grouping
    # - smoothing / outlier removal

    return {}  # Not yet implemented


def merge_statistics_with_defaults(
    entry: ConfigEntry,
    real_stats: dict,
) -> dict:
    """
    Merges real statistics with user defaults.
    Real stats override defaults only if enough data exists.
    """

    options = entry.options or entry.data

    merged = {}

    for idx, key in enumerate(WEEKDAY_OPTIONS):
        if key in real_stats:
            merged[key] = real_stats[key]
        else:
            merged[key] = options.get(key, 50)

    return merged
