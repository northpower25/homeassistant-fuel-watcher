from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .notify import send_test_notification
from .tank_history import (
    append_tank_event,
    update_tank_event,
    delete_tank_event,
    clear_tank_history,
)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    async def _get_entry(config_entry_id: str | None) -> ConfigEntry | None:
        if config_entry_id and config_entry_id in hass.data[DOMAIN]:
            return hass.data[DOMAIN][config_entry_id]
        return entry

    async def handle_test_service(call: ServiceCall):
        cfg_entry = await _get_entry(call.data.get("config_entry_id"))
        if cfg_entry:
            await send_test_notification(hass, cfg_entry)

    async def handle_add_tank_event(call: ServiceCall):
        cfg_entry = await _get_entry(call.data.get("config_entry_id"))
        if not cfg_entry:
            return
        append_tank_event(
            hass,
            cfg_entry,
            price_per_liter=call.data.get("price_per_liter"),
            liters=call.data.get("liters"),
            total_cost=call.data.get("total_cost"),
            station_name=call.data.get("station_name"),
            odometer=call.data.get("odometer"),
            suggested_price=call.data.get("suggested_price"),
            source=call.data.get("source", "manual"),
        )

    async def handle_update_tank_event(call: ServiceCall):
        cfg_entry = await _get_entry(call.data.get("config_entry_id"))
        if not cfg_entry:
            return
        event_id = call.data.get("event_id")
        if not event_id:
            return
        updates = {k: v for k, v in call.data.items() if k not in ("config_entry_id", "event_id")}
        update_tank_event(hass, cfg_entry, event_id=event_id, **updates)

    async def handle_delete_tank_event(call: ServiceCall):
        cfg_entry = await _get_entry(call.data.get("config_entry_id"))
        if not cfg_entry:
            return
        event_id = call.data.get("event_id")
        if not event_id:
            return
        delete_tank_event(hass, cfg_entry, event_id=event_id)

    async def handle_clear_tank_history(call: ServiceCall):
        cfg_entry = await _get_entry(call.data.get("config_entry_id"))
        if not cfg_entry:
            return
        clear_tank_history(hass, cfg_entry)

    hass.services.async_register(DOMAIN, "send_test_notification", handle_test_service)
    hass.services.async_register(DOMAIN, "add_tank_event", handle_add_tank_event)
    hass.services.async_register(DOMAIN, "update_tank_event", handle_update_tank_event)
    hass.services.async_register(DOMAIN, "delete_tank_event", handle_delete_tank_event)
    hass.services.async_register(DOMAIN, "clear_tank_history", handle_clear_tank_history)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
