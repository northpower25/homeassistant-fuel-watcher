"""
Commit: feat(telegram): add template-based messaging with full variable support

Fuel Watcher – Telegram Template Engine
---------------------------------------
Ermöglicht konfigurierbare Nachrichten mit Variablen.

Verfügbare Variablen (empfohlen):
- {vehicle}
- {price}
- {delta}
- {delta_percent}
- {station}
- {distance_km}
- {range_km}
- {days_left}
- {lat}
- {lng}
- {reason}
"""

from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_NOTIFY_MSG_TANKEN,
    CONF_NOTIFY_MSG_RANGE_DAYS,
    DEFAULT_NOTIFY_MSG_TANKEN,
    DEFAULT_NOTIFY_MSG_RANGE_DAYS,
)
from .storage import set_last_telegram

_LOGGER = logging.getLogger(__name__)


def render_template(template: str, data: dict) -> str:
    """Render a template by replacing {vars} with values."""
    try:
        return template.format(**data)
    except Exception as e:
        _LOGGER.error("Template rendering failed: %s", e)
        return template


async def send_tanken_message(
    hass: HomeAssistant,
    entry: ConfigEntry,
    notify_func,
    data: dict,
):
    """Send tank recommendation message."""
    template = (
        entry.options.get(CONF_NOTIFY_MSG_TANKEN)
        or entry.data.get(CONF_NOTIFY_MSG_TANKEN)
        or DEFAULT_NOTIFY_MSG_TANKEN
    )

    text = render_template(template, data)
    await notify_func(hass, entry, text)
    await set_last_telegram(hass, entry, {"text": text})


async def send_range_days_message(
    hass: HomeAssistant,
    entry: ConfigEntry,
    notify_func,
    data: dict,
):
    """Send range-days warning message."""
    template = (
        entry.options.get(CONF_NOTIFY_MSG_RANGE_DAYS)
        or entry.data.get(CONF_NOTIFY_MSG_RANGE_DAYS)
        or DEFAULT_NOTIFY_MSG_RANGE_DAYS
    )

    text = render_template(template, data)
    await notify_func(hass, entry, text)
    await set_last_telegram(hass, entry, {"text": text})
