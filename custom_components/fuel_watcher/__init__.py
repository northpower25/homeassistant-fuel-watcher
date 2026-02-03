"""
Commit: feat(init): add platform setup, service registration and tankerkoenig update orchestration

Fuel Watcher – Integration Init
-------------------------------
- Registriert Sensor-Plattformen
- Registriert Services
- Führt Tankerkoenig-Updates aus
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, PLATFORMS
from .sources.tankerkoenig import update_tankerkoenig
from .storage import load_data
from .telegram import send_price_notification

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Fuel Watcher."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Periodic Tankerkoenig update
    async def _update(now):
        opts = entry.options
        data = await load_data(hass, entry)

        lat = hass.config.latitude
        lon = hass.config.longitude
        radius = opts.get("radius", 5)
        fuel_type = opts.get("fuel_type", "e5")
        api_key = opts.get("api_key")

        if not api_key:
            return

        station = await update_tankerkoenig(
            hass,
            entry,
            lat=lat,
            lon=lon,
            radius=radius,
            fuel_type=fuel_type,
            api_key=api_key,
        )

        if station:
            await send_price_notification(
                hass,
                entry,
                current_price=float(station.get("price")),
            )

    async_track_time_interval(hass, _update, timedelta(minutes=10))

    # Register services
    async def _add_tank(call):
        from .tank_history import add_tank_event
        await add_tank_event(
            hass,
            entry,
            price_per_liter=call.data.get("price_per_liter"),
            liters=call.data.get("liters"),
            station_name=call.data.get("station_name"),
            odometer=call.data.get("odometer"),
        )

    async def _clear(call):
        from .tank_history import clear_tank_history
        await clear_tank_history(hass, entry)

    async def _test(call):
        from .telegram import build_notification
        msg = await build_notification(
            hass,
            entry,
            title="🧪 Testnachricht",
            body="Fuel Watcher Telegram funktioniert.",
        )
        _LOGGER.info("Test message: %s", msg)

    hass.services.async_register(DOMAIN, "add_tank_event", _add_tank)
    hass.services.async_register(DOMAIN, "clear_tank_history", _clear)
    hass.services.async_register(DOMAIN, "send_test_notification", _test)

    return True
