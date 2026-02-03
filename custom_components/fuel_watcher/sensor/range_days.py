"""
Commit: feat(sensor): add range days sensor for remaining days estimation

Fuel Watcher – Range Days Sensor
--------------------------------
Schätzt:
- wie viele Tage die aktuelle Reichweite noch reicht

Nutzt:
- range_entity (km)
- einfache Annahme / spätere Statistik-Engine möglich
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN, CONF_ENTITY_RANGE


class FuelWatcherRangeDaysSensor(SensorEntity):
    """Sensor für verbleibende Tage basierend auf Reichweite."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_range_days"
        self._attr_name = f"Fuel Watcher {entry.title} Range Days"
        self._attr_native_unit_of_measurement = "d"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Estimate remaining days based on range entity."""
        range_entity_id = (
            self.entry.options.get(CONF_ENTITY_RANGE)
            or self.entry.data.get(CONF_ENTITY_RANGE)
        )

        if not range_entity_id:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        state_obj = self.hass.states.get(range_entity_id)
        if not state_obj:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        try:
            range_km = float(state_obj.state)
        except Exception:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        # TODO: später durch Statistik-Engine ersetzen
        # Annahme: 50 km/Tag
        daily_km = 50.0
        days_left = range_km / daily_km if daily_km > 0 else 0

        self._attr_native_value = round(days_left, 1)
        self._attr_extra_state_attributes = {
            "range_km": range_km,
            "assumed_daily_km": daily_km,
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
