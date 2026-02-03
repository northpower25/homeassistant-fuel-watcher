"""
Commit: feat(strategy): add percent and absolute price drop thresholds to decision logic

Fuel Watcher – Strategy Engine
------------------------------
Entscheidet, ob eine Tankempfehlung ausgesprochen wird.

Nutzt:
- last_price aus Storage
- konfigurierbare Schwellwerte:
  - price_drop_percent_threshold
  - price_drop_absolute_threshold
- schreibt:
  - last_price
  - last_decision
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

    Rückgabe:
    {
        "should_tank": bool,
        "reason": str,
        "delta": float,
        "delta_percent": float,
    }
    """

    options = entry.options or entry.data

    percent_threshold = float(options.get(CONF_PRICE_DROP_PERCENT_THRESHOLD, 0))
    absolute_threshold = float(options.get(CONF_PRICE_DROP_ABSOLUTE_THRESHOLD, 0))

    last_price = await get_last_price(hass, entry)

    if last_price is None:
        # Erstes Mal: kein Vergleich möglich
        await set_last_price(hass, entry, current_price)
        decision = {"should_tank": False, "reason": "initial"}
        await set_last_decision(hass, entry, decision)
        return {
            "should_tank": False,
            "reason": "initial",
            "delta": 0,
            "delta_percent": 0,
        }

    delta = current_price - last_price
    delta_percent = (delta / last_price) * 100 if last_price > 0 else 0

    _LOGGER.debug(
        "Strategy: last_price=%.3f current_price=%.3f delta=%.3f delta_percent=%.2f%%",
        last_price,
        current_price,
        delta,
        delta_percent,
    )

    # 1) Absoluter Schwellwert
    if absolute_threshold > 0 and delta <= -absolute_threshold:
        reason = f"Preis um {abs(delta):.2f} € gefallen"
        decision = {"should_tank": True, "reason": reason}
        await set_last_price(hass, entry, current_price)
        await set_last_decision(hass, entry, decision)
        return {
            "should_tank": True,
            "reason": reason,
            "delta": delta,
            "delta_percent": delta_percent,
        }

    # 2) Prozentualer Schwellwert
    if percent_threshold > 0 and delta_percent <= -percent_threshold:
        reason = f"Preis um {abs(delta_percent):.1f}% gefallen"
        decision = {"should_tank": True, "reason": reason}
        await set_last_price(hass, entry, current_price)
        await set_last_decision(hass, entry, decision)
        return {
            "should_tank": True,
            "reason": reason,
            "delta": delta,
            "delta_percent": delta_percent,
        }

    # 3) Keine Empfehlung
    decision = {"should_tank": False, "reason": "no_threshold_hit"}
    await set_last_decision(hass, entry, decision)
    return {
        "should_tank": False,
        "reason": "no_threshold_hit",
        "delta": delta,
        "delta_percent": delta_percent,
    }
