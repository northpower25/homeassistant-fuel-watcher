"""
Commit: feat(sensor): add main fuel watcher sensor with storage-backed state and attributes

Fuel Watcher – Main Sensor
--------------------------
Dieser Sensor bildet das Herzstück der Integration.

Er zeigt:
- aktuellen Preis (von Tankerkoenig)
- letzte API-Daten
- letzte Telegram-Daten
- letzte Fehler
- beste Tankstelle
- letzte Tankhistorie
- Verbrauchs- und Preisstatistiken (Basisdaten)

Er dient als zentrale Übersicht für Dashboards.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import load_data
from ..price_engine import (
    compute_price_delta,
    compute_price_delta_percent,
)
from ..statistics_engine import get_avg_daily_km
from ..tank_history import get_last_tank_event


class FuelWatcherMainSensor(SensorEntity):
    """Main overview sensor for Fuel Watcher."""

    _attr_icon = "mdi:gas-station"
    _attr_native_unit_of_measurement = "€/L"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self._attr_name = "Fuel Watcher"
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_main"

        self._state: Optional[float] = None
        self._attrs: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Home Assistant properties
    # ------------------------------------------------------------------

    @property
    def native_value(self) -> Optional[float]:
        """Return the current fuel price."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extended attributes."""
        return self._attrs

    @property
    def device_info(self):
        return {
            "identifiers": {("fuel_watcher", self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    # ------------------------------------------------------------------
    # Update Logic
    # ------------------------------------------------------------------

    async def async_update(self) -> None:
        """Update sensor state and attributes."""

        data = await load_data(self.hass, self.entry)

        best_station = data.get("best_station")
        last_api = data.get("last_api")
        last_telegram = data.get("last_telegram")
        last_error = data.get("last_error")

        # Current price
        current_price = None
        if best_station:
            try:
                current_price = float(best_station.get("price"))
            except Exception:
                current_price = None

        self._state = current_price

        # Price deltas
        delta = await compute_price_delta(
            self.hass, self.entry, current_price=current_price
        )
        delta_percent = await compute_price_delta_percent(
            self.hass, self.entry, current_price=current_price
        )

        # Last tank event
        last_tank = await get_last_tank_event(self.hass, self.entry)

        # Learned statistics
        avg_daily_km = await get_avg_daily_km(self.hass, self.entry)

        # Build attributes
        self._attrs = {
            "best_station": best_station,
            "last_api": last_api,
            "last_telegram": last_telegram,
            "last_error": last_error,
            "price_delta": delta,
            "price_delta_percent": delta_percent,
            "avg_daily_km": avg_daily_km,
            "last_tank_event": last_tank,
        }
