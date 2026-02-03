from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .notify import send_test_notification
from .tank_history import TankHistoryStore, SIGNAL_TANK_HISTORY_UPDATED

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Fuel Watcher (YAML not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fuel Watcher from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # store a dict per entry to allow multiple stored items
    hass.data[DOMAIN][entry.entry_id] = {"entry": entry}

    # initialize tank history store
    store = TankHistoryStore(hass, entry)
    await store.async_initialize()
    hass.data[DOMAIN][entry.entry_id]["tank_history_store"] = store

    # Services registrieren (einmalig pro HA-Instanz)
    if not hass.services.has_service(DOMAIN, "send_test_notification"):

        async def _get_entry(config_entry_id: str | None) -> ConfigEntry | None:
            if config_entry_id and config_entry_id in hass.data.get(DOMAIN, {}):
                return hass.data[DOMAIN][config_entry_id].get("entry")
            # Fallback: erster Eintrag
            if hass.data.get(DOMAIN):
                first = next(iter(hass.data[DOMAIN].values()))
                return first.get("entry")
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
            store = hass.data[DOMAIN][cfg_entry.entry_id]["tank_history_store"]
            await store.async_append_event(
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
            store = hass.data[DOMAIN][cfg_entry.entry_id]["tank_history_store"]
            updates = {k: v for k, v in call.data.items() if k not in ("config_entry_id", "event_id")}
            await store.async_update_event(event_id=int(event_id), **updates)

        async def handle_delete_tank_event(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for delete_tank_event")
                return
            event_id = call.data.get("event_id")
            if not event_id:
                _LOGGER.warning("Fuel Watcher: Missing event_id for delete_tank_event")
                return
            store = hass.data[DOMAIN][cfg_entry.entry_id]["tank_history_store"]
            await store.async_delete_event(event_id=int(event_id))

        async def handle_clear_tank_history(call: ServiceCall) -> None:
            cfg_entry = await _get_entry(call.data.get("config_entry_id"))
            if not cfg_entry:
                _LOGGER.warning("Fuel Watcher: No config entry for clear_tank_history")
                return
            store = hass.data[DOMAIN][cfg_entry.entry_id]["tank_history_store"]
            await store.async_clear()

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
