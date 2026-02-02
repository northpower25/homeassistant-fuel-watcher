from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .notify import send_test_notification
from .tank_history import (
    append_tank_event,
    update_tank_event,
    delete_tank_event,
    clear_tank_history,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Fuel Watcher from YAML (not used, config flow only)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fuel Watcher from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    # Services registrieren (einmalig pro HA-Instanz)
    if not hass.services.has_service(DOMAIN, "send_test_notification"):

        async def _get_entry(config_entry_id: str | None) -> ConfigEntry | None:
            if config_entry_id and config_entry_id in hass.data.get(DOMAIN, {}):
                return hass.data[DOMAIN][config_entry_id]
            # Fallback: erster Eintrag
            if hass.data.get(DOMAIN):
                return next(iter(hass.data[DOMAIN].values()))
            return None

        async def handle_test_notification(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry found for test notification")
                return
            await send_test_notification(hass, cfg_entry)

        async def handle_add_tank_event(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for add_tank_event")
                return

            append_tank_event(
                hass,
                cfg_entry,
                price_per_liter=call.data.get("price_per_liter"),
                liters=call.data.get("liters"),
                total_cost=call.data.get("total_cost"),
                station_name=call.data.get("station_name"),
                suggested_price=call.data.get("suggested_price"),
                odometer=call.data.get("odometer"),
                source=call.data.get("source", "manual"),
            )

        async def handle_update_tank_event(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for update_tank_event")
                return

            event_id = call.data.get("event_id")
            if not event_id:
                _LOGGER.warning("Fuel Watcher: Missing event_id for update_tank_event")
                return

            updates = {
                k: v
                for k, v in call.data.items()
                if k not in ("config_entry_id", "event_id")
            }
            update_tank_event(hass, cfg_entry, event_id=event_id, **updates)

        async def handle_delete_tank_event(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for delete_tank_event")
                return

            event_id = call.data.get("event_id")
            if not event_id:
                _LOGGER.warning("Fuel Watcher: Missing event_id for delete_tank_event")
                return

            delete_tank_event(hass, cfg_entry, event_id=event_id)

        async def handle_clear_tank_history(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for clear_tank_history")
                return

            clear_tank_history(hass, cfg_entry)

        hass.services.async_register(DOMAIN, "send_test_notification", handle_test_notification)
        hass.services.async_register(DOMAIN, "add_tank_event", handle_add_tank_event)
        hass.services.async_register(DOMAIN, "update_tank_event", handle_update_tank_event)
        hass.services.async_register(DOMAIN, "delete_tank_event", handle_delete_tank_event)
        hass.services.async_register(DOMAIN, "clear_tank_history", handle_clear_tank_history)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Fuel Watcher config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
