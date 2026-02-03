"""
Commit: refactor(notify): integrate with new telegram engine, diagnostics storage and markdown messaging

Fuel Watcher – Notification Wrapper
-----------------------------------
Diese Datei kapselt den Versand von Telegram-Nachrichten und integriert:

- neue Telegram-Engine
- Storage-Diagnostics (last_telegram, last_error)
- Markdown-Unterstützung
- Fehlerlogging

Sie dient als zentrale Stelle für ausgehende Benachrichtigungen.
"""

from __future__ import annotations

import logging
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
)
from .storage import set_last_telegram, set_last_error

_LOGGER = logging.getLogger(__name__)


async def _send_telegram_message(
    hass: HomeAssistant,
    token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> bool:
    """Send raw Telegram message."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }

    session = async_get_clientsession(hass)

    try:
        with async_timeout.timeout(10):
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    _LOGGER.error("Telegram sendMessage failed: %s - %s", resp.status, body)
                    return False
    except Exception as e:
        _LOGGER.error("Error sending Telegram message: %s", e)
        return False

    return True


async def send_notification(hass: HomeAssistant, entry: ConfigEntry, text: str):
    """Send a Telegram notification and update diagnostics."""
    token = entry.data.get(CONF_TELEGRAM_TOKEN)
    chat_id = entry.data.get(CONF_TELEGRAM_CHAT_ID)

    if not token or not chat_id:
        _LOGGER.warning("Telegram not configured (token/chat_id missing)")
        await set_last_error(hass, entry, "Telegram not configured")
        return

    ok = await _send_telegram_message(hass, token, chat_id, text)

    if ok:
        _LOGGER.debug("Telegram notification sent successfully")
        await set_last_telegram(hass, entry, {"text": text})
    else:
        _LOGGER.error("Telegram notification failed")
        await set_last_error(hass, entry, "Telegram send failed")


async def send_test_notification(hass: HomeAssistant, entry: ConfigEntry):
    """Send a test message."""
    text = (
        "🤖 *Fuel Watcher Testnachricht*\n\n"
        "Dein Auto sagt: „Ich bin bereit für intelligente Tankentscheidungen!“\n"
        "Wenn du das hier lesen kannst, funktioniert dein Telegram‑Bot einwandfrei 🚀"
    )
    await send_notification(hass, entry, text)
