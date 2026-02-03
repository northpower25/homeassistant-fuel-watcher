"""
Commit: feat(strategy): add percent and absolute price drop thresholds to decision logic

Fuel Watcher – Strategy Engine
------------------------------
Erweitert um:
- price_drop_percent_threshold
- price_drop_absolute_threshold

Die Strategy-Engine entscheidet:
- Soll getankt werden?
- Ist der Preis signifikant gefallen?
- Ist der Preis im Vergleich zum letzten Preis attraktiv?

Die Engine nutzt:
- Storage (last_price, last_station, history)
- Options (Schwellwerte)
- Fahrzeugdaten (range_entity)
"""

from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import (
    get_last_price,
    set_last_price,
    set_last_decision,
)
from .const import (
    CONF_ENTITY_RANGE,
    CONF_PRICE_DROP_PERCENT_THRESHOLD,
    CONF_PRICE_DROP_ABSOLUTE_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


async def evaluate_strategy(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_price: float,
    station_name: str,
) -> dict:
    """
    Hauptlogik der Tankstrategie.
    Gibt ein dict zurück:
    {
        "should_tank": bool,
        "reason": str,
        "delta": float,
        "delta_percent": float,
    }
    """

    options = entry.options or entry.data

    # Schwellwerte aus Options
    percent_threshold = float(options.get(CONF_PRICE_DROP_PERCENT_THRESHOLD, 0))
    absolute_threshold = float(options.get(CONF_PRICE_DROP_ABSOLUTE_THRESHOLD, 0))

    # Letzten Preis laden
    last_price = await get_last_price(hass, entry)

    if last_price is None:
        # Beim ersten Start gibt es keinen Vergleich
        await set_last_price(hass, entry, current_price)
        await set_last_decision(hass, entry, {"should_tank": False, "reason": "initial"})
        return {
            "should_tank": False,
            "reason": "initial",
            "delta": 0,
            "delta_percent": 0,
        }

    # Preisänderungen berechnen
    delta = current_price - last_price
    delta_percent = (delta / last_price) * 100 if last_price > 0 else 0

    _LOGGER.debug(
        "Strategy: last_price=%.3f current_price=%.3f delta=%.3f delta_percent=%.2f%%",
        last_price,
        current_price,
        delta,
        delta_percent,
    )

    # Entscheidung: Preis ist absolut gefallen
    if absolute_threshold > 0 and delta <= -absolute_threshold:
        reason = f"Preis um {abs(delta):.2f} € gefallen"
        await set_last_price(hass, entry, current_price)
        await set_last_decision(hass, entry, {"should_tank": True, "reason": reason})
        return {
            "should_tank": True,
            "reason": reason,
            "delta": delta,
            "delta_percent": delta_percent,
        }

    # Entscheidung: Preis ist prozentual gefallen
    if percent_threshold > 0 and delta_percent <= -percent_threshold:
        reason = f"Preis um {abs(delta_percent):.1f}% gefallen"
        await set_last_price(hass, entry, current_price)
        await set_last_decision(hass, entry, {"should_tank": True, "reason": reason})
        return {
            "should_tank": True,
            "reason": reason,
            "delta": delta,
            "delta_percent": delta_percent,
        }

    # Keine Tankempfehlung
    await set_last_decision(hass, entry, {"should_tank": False, "reason": "no_threshold_hit"})
    return {
        "should_tank": False,
        "reason": "no_threshold_hit",
        "delta": delta,
        "delta_percent": delta_percent,
    }
