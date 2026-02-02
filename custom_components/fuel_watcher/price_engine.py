from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .tank_history import _load_data as _load_history, _save_data as _save_history
from .const import (
    CONF_PRICE_MODE,
    CONF_PRICE_DELTA_PERCENT,
    CONF_PRICE_DELTA_ABSOLUTE,
)


def update_price_history(
    hass: HomeAssistant,
    entry: ConfigEntry,
    price: float | None,
) -> None:
    if price is None:
        return

    data = _load_history(hass, entry)
    history = data.get("price", [])
    history.append({"value": price})
    history = history[-60:]
    data["price"] = history
    _save_history(hass, entry, data)


def get_last_price(hass: HomeAssistant, entry: ConfigEntry) -> float | None:
    data = _load_history(hass, entry)
    history = data.get("price", [])
    if not history:
        return None
    return float(history[-1]["value"])


def compute_price_delta(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_price: float | None,
) -> dict[str, Any]:
    if current_price is None:
        return {"delta": None, "delta_percent": None, "trigger": False}

    last_price = get_last_price(hass, entry)
    if last_price is None or last_price <= 0:
        return {"delta": None, "delta_percent": None, "trigger": False}

    delta = round(current_price - last_price, 3)
    delta_percent = round((delta / last_price) * 100.0, 1)

    options = entry.options or entry.data
    mode = options.get(CONF_PRICE_MODE, "fixed")
    delta_percent_threshold = float(options.get(CONF_PRICE_DELTA_PERCENT, 5.0))
    delta_abs_threshold = float(options.get(CONF_PRICE_DELTA_ABSOLUTE, 0.10))

    trigger = False
    if mode == "percent":
        if abs(delta_percent) >= delta_percent_threshold:
            trigger = True
    elif mode == "absolute":
        if abs(delta) >= delta_abs_threshold:
            trigger = True
    else:
        trigger = False

    return {
        "delta": delta,
        "delta_percent": delta_percent,
        "trigger": trigger,
    }
