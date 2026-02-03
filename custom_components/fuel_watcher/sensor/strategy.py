"""
Commit: feat(sensor): add strategy sensor exposing decision and price deltas

Fuel Watcher – Strategy Sensor
------------------------------
Zeigt:
- aktuelle Entscheidung (tanken / nicht)
- Grund
- Preisdelta absolut und prozentual
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import get_last_decision
from ..const import DOMAIN


class FuelWatcherStrategySensor(SensorEntity):
    """Sensor für die Tankstrategie."""

    _attr_icon = "mdi:chart-line"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_strategy"
        self._attr_name = f"Fuel Watcher {entry.title} Strategy"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Update sensor state from last decision."""
        decision = await get_last_decision(self.hass, self.entry)
        if not decision:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        should_tank = decision.get("should_tank")
        reason = decision.get("reason")
        delta = decision.get("delta")
        delta_percent = decision.get("delta_percent")

        self._attr_native_value = "tank" if should_tank else "wait"
        self._attr_extra_state_attributes = {
            "should_tank": should_tank,
            "reason": reason,
            "delta": delta,
            "delta_percent": delta_percent,
        }

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"Fuel Watcher {self.entry.title}",
            "manufacturer": "Fuel Watcher",
        }
