from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN
from ..tank_history import get_tank_events


class FuelWatcherTankHistorySensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher Tankhistorie"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_tank_history"
        self._events: list[dict] = []

    @property
    def native_value(self):
        return len(self._events)

    @property
    def extra_state_attributes(self):
        total_cost = sum(e.get("total_cost", 0) or 0 for e in self._events)
        avg_price = (
            sum((e.get("price_per_liter") or 0) for e in self._events) / len(self._events)
            if self._events else None
        )
        return {
            "events": self._events,
            "total_events": len(self._events),
            "total_cost": round(total_cost, 2),
            "avg_price": round(avg_price, 3) if avg_price is not None else None,
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    async def async_update(self):
        self._events = get_tank_events(self.hass, self.entry)
