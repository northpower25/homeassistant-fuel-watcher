"""
Commit: feat(telegram): add full telegram integration with tank parsing, notifications, navigation links and diagnostics

Fuel Watcher – Telegram Engine
------------------------------
Diese Datei implementiert die komplette Telegram-Integration aus v0.0.27,
jetzt basierend auf der neuen Storage-Architektur.

Funktionen:
- Tankvorgänge per Telegram erfassen (z. B. "42.5L @ 1.72")
- Navigation-Links (Google, Apple, Waze)
- Markdown-Benachrichtigungen
- Preis-Delta / Prozent / Spike
- Reichweite in km / Tagen
- Testnachricht
- Diagnostics-Logging

Abhängigkeiten:
- storage.py
- tank_history.py
- price_engine.py
- statistics_engine.py
- sources/tankerkoenig.py
"""

from __future__ import annotations

import re
import logging
from typing import Optional, Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .storage import (
    set_last_telegram,
    set_last_error,
    load_data,
)
from .tank_history import add_tank_event, get_last_tank_event
from .price_engine import (
    compute_price_delta,
    compute_price_delta_percent,
    detect_price_spike,
)
from .statistics_engine import estimate_days_left
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telegram Parsing
# ---------------------------------------------------------------------------

TANK_REGEX = re.compile(
    r"(?P<liters>\d+(\.\d+)?)\s*[lL]\s*@\s*(?P<price>\d+(\.\d+)?)",
    re.IGNORECASE,
)


def parse_tank_message(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse tank messages like:
      "42.5L @ 1.72"
      "50 l @ 1.65"
    """
    match = TANK_REGEX.search(text)
    if not match:
        return None

    liters = float(match.group("liters"))
    price = float(match.group("price"))

    return {
        "liters": liters,
        "price_per_liter": price,
    }


# ---------------------------------------------------------------------------
# Navigation Links
# ---------------------------------------------------------------------------

def build_navigation_links(station: Dict[str, Any]) -> Dict[str, str]:
    lat = station.get("lat")
    lon = station.get("lon")

    if lat is None or lon is None:
        return {}

    return {
        "google": f"https://maps.google.com/?q={lat},{lon}",
        "apple": f"http://maps.apple.com/?ll={lat},{lon}",
        "waze": f"https://waze.com/ul?ll={lat},{lon}&navigate=yes",
    }


# ---------------------------------------------------------------------------
# Telegram Message Builder
# ---------------------------------------------------------------------------

async def build_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    title: str,
    body: str,
    include_station: bool = True,
) -> str:
    """Build a Markdown Telegram message."""

    data = await load_data(hass, entry)
    station = data.get("best_station")

    msg = f"*{title}*\n{body}"

    if include_station and station:
        links = build_navigation_links(station)
        msg += "\n\n*Tankstelle:*\n"
        msg += f"{station.get('name')} – {station.get('price')} €/L\n"
        msg += f"{station.get('street')} {station.get('house_number')}, {station.get('city')}\n"

        if links:
            msg += "\n*Navigation:*\n"
            if "google" in links:
                msg += f"[Google Maps]({links['google']})\n"
            if "apple" in links:
                msg += f"[Apple Maps]({links['apple']})\n"
            if "waze" in links:
                msg += f"[Waze]({links['waze']})\n"

    return msg


# ---------------------------------------------------------------------------
# Telegram Handler
# ---------------------------------------------------------------------------

async def handle_telegram_message(
    hass: HomeAssistant,
    entry: ConfigEntry,
    text: str,
) -> Optional[str]:
    """
    Process incoming Telegram messages.

    Returns:
        Markdown response text or None.
    """

    # Save diagnostics
    await set_last_telegram(hass, entry, {"text": text})

    # 1) Tankvorgang?
    parsed = parse_tank_message(text)
    if parsed:
        event = await add_tank_event(
            hass,
            entry,
            price_per_liter=parsed["price_per_liter"],
            liters=parsed["liters"],
            source="telegram",
        )

        msg = await build_notification(
            hass,
            entry,
            title="⛽ Tankvorgang gespeichert",
            body=f"{parsed['liters']} L @ {parsed['price_per_liter']} €/L\n"
                 f"Gesamtkosten: {event.get('total_cost')} €",
        )
        return msg

    # 2) Testnachricht?
    if text.strip().lower() == "test":
        msg = await build_notification(
            hass,
            entry,
            title="🧪 Testnachricht",
            body="Telegram ist korrekt eingerichtet.",
        )
        return msg

    # 3) Unbekannte Nachricht
    await set_last_error(hass, entry, f"Unbekannte Telegram-Nachricht: {text}")
    return "Ich konnte deine Nachricht nicht verstehen. Beispiel: `42.5L @ 1.72`"


# ---------------------------------------------------------------------------
# Outgoing Notifications
# ---------------------------------------------------------------------------

async def send_price_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    current_price: float,
) -> str:
    """Build price delta notification."""

    delta = await compute_price_delta(hass, entry, current_price=current_price)
    percent = await compute_price_delta_percent(hass, entry, current_price=current_price)
    spike = await detect_price_spike(hass, entry, current_price=current_price)

    body = f"Aktueller Preis: {current_price} €/L\n"
    if delta is not None:
        body += f"Preis-Delta: {delta} €/L\n"
    if percent is not None:
        body += f"Preis-Delta: {percent}%\n"
    if spike:
        body += "\n⚠️ *Preis-Spike erkannt!*"

    return await build_notification(
        hass,
        entry,
        title="📈 Preisaktualisierung",
        body=body,
    )


async def send_range_notification(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    km_left: float,
) -> str:
    """Build range notification."""

    days = await estimate_days_left(hass, entry, km_left=km_left)

    body = f"Reichweite: {km_left} km\n"
    if days is not None:
        body += f"Reichweite: {days} Tage\n"

    return await build_notification(
        hass,
        entry,
        title="🚗 Reichweiten-Update",
        body=body,
    )
