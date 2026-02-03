"""
Commit: feat(price_engine): add delta, percent, spike and trend price analytics

Fuel Watcher – Price Engine
---------------------------
Diese Datei implementiert die Preislogik aus v0.0.27 – jetzt basierend auf der
neuen Storage-Architektur.

Funktionen:
- Preis-Delta (absolut)
- Preis-Delta-Prozent
- Preis-Spike-Erkennung
- Preis-Trend (steigend/fallend)
- Letzten Preis aus Tankhistorie oder Preis-Historie bestimmen

Die Rohdaten (tank_history, price_history) werden in storage.py gehalten.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import load_data


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_price_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> List[Dict[str, Any]]:
    data = await load_data(hass, entry)
    return data.get("price_history", [])


async def _get_last_price_from_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Optional[float]:
    """Return last price from price_history."""
    prices = await _get_price_history(hass, entry)
    if not prices:
        return None

    # Sort by timestamp
    sorted_prices = sorted(
        prices,
        key=lambda x: _parse_ts(x.get("ts") or "") or datetime.min,
    )

    return sorted_prices[-1].get("price")


async def _get_last_price_from_tank_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Optional[float]:
    """Return last price_per_liter from tank_history."""
    data = await load_data(hass, entry)
    events = data.get("tank_history", [])
    if not events:
        return None

    return events[-1].get("price_per_liter")


async def get_last_known_price(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Optional[float]:
    """
    Return the most reliable last known price.

    Priorität:
    1. Letzter Preis aus Tankhistorie
    2. Letzter Preis aus Preis-Historie
    """
    tank_price = await _get_last_price_from_tank_history(hass, entry)
    if tank_price is not None:
        return tank_price

    return await _get_last_price_from_history(hass, entry)


# ---------------------------------------------------------------------------
# Price Delta (absolute)
# ---------------------------------------------------------------------------

async def compute_price_delta(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_price: Optional[float],
) -> Optional[float]:
    """Compute absolute price delta."""
    if current_price is None:
        return None

    last_price = await get_last_known_price(hass, entry)
    if last_price is None:
        return None

    delta = current_price - float(last_price)
    return round(delta, 3)


# ---------------------------------------------------------------------------
# Price Delta Percent
# ---------------------------------------------------------------------------

async def compute_price_delta_percent(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_price: Optional[float],
) -> Optional[float]:
    """Compute percent price delta."""
    if current_price is None:
        return None

    last_price = await get_last_known_price(hass, entry)
    if last_price is None or last_price == 0:
        return None

    percent = ((current_price - last_price) / last_price) * 100
    return round(percent, 2)


# ---------------------------------------------------------------------------
# Price Spike Detection
# ---------------------------------------------------------------------------

async def detect_price_spike(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_price: Optional[float],
    threshold: float = 0.08,
) -> Optional[bool]:
    """
    Detect price spike.

    threshold = absolute difference in €/L
    """
    delta = await compute_price_delta(hass, entry, current_price=current_price)
    if delta is None:
        return None

    return delta >= threshold


# ---------------------------------------------------------------------------
# Price Trend
# ---------------------------------------------------------------------------

async def compute_price_trend(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    window: int = 5,
) -> Optional[str]:
    """
    Compute price trend based on last N price entries.

    Returns:
    - "rising"
    - "falling"
    - "stable"
    - None (not enough data)
    """
    prices = await _get_price_history(hass, entry)
    if len(prices) < 2:
        return None

    # Sort chronologically
    sorted_prices = sorted(
        prices,
        key=lambda x: _parse_ts(x.get("ts") or "") or datetime.min,
    )

    # Take last N entries
    window_prices = sorted_prices[-window:]
    values = [p.get("price") for p in window_prices if p.get("price") is not None]

    if len(values) < 2:
        return None

    if values[-1] > values[0]:
        return "rising"
    if values[-1] < values[0]:
        return "falling"
    return "stable"
