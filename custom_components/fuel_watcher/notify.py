from __future__ import annotations

import logging
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
)

_LOGGER = logging.getLogger(__name__)


async def _send_telegram_message(token: str, chat_id: str, text: str, parse_mode: str = "Markdown"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    async with aiohttp.ClientSession() as session:
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
    token = entry.data.get(CONF_TELEGRAM_TOKEN)
    chat_id = entry.data.get(CONF_TELEGRAM_CHAT_ID)

    if not token or not chat_id:
        _LOGGER.warning("Telegram not configured (token/chat_id missing)")
        return

    ok = await _send_telegram_message(token, chat_id, text)
    if ok:
        _LOGGER.debug("Telegram notification sent successfully")
    else:
        _LOGGER.error("Telegram notification failed")


async def send_test_notification(hass: HomeAssistant, entry: ConfigEntry):
    text = (
        "🤖 *Fuel Watcher Testnachricht*\n\n"
        "Dein Auto sagt: „Ich bin bereit für intelligente Tankentscheidungen!“\n"
        "Wenn du das hier lesen kannst, funktioniert dein Telegram‑Bot einwandfrei 🚀"
    )
    await send_notification(hass, entry, text)
