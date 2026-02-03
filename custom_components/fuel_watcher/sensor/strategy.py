"""
Commit: feat(sensor): add full strategy sensor suite (range, days_left, delta, percent, spike, decision)

Fuel Watcher – Strategy Sensors
-------------------------------
Diese Datei implementiert alle Strategie-Sensoren aus v0.0.27 – jetzt basierend
auf der neuen Storage-, Statistik- und Preis-Engine.

Sensoren:
- sensor.fuel_watcher_range_km
- sensor.fuel_watcher_days_left
- sensor.fuel_watcher_price_delta
- sensor.fuel_watcher_price_delta_percent
- sensor.fuel_watcher_price_spike
- sensor.fuel_watcher_decision

Alle Sensoren sind async und nutzen:
- storage.py
- price_engine.py
- statistics_engine.py
- tank_history.py
"""

from __future__ import annotations

from typing import Optional, Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..storage import load_data
from ..price_engine import (
    compute_price_delta,
    compute_price_delta_percent,
    detect_price_spike,
)
from ..statistics_engine import estimate_days_left
from ..tank_history import get_last_tank_event


# ---------------------------------------------------------------------------
# Base Class
# ---------------------------------------------------------------------------

class _BaseStrategySensor(SensorEntity):
    """Base class for all strategy sensors."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, uid: str):
        self.hass = hass
        self.entry = entry
        self._attr_name = name
        self._attr_unique_id = f"fuel_watcher_{entry.entry_id}_{uid}"
        self._state: Optional[Any] = None
        self._attrs: Dict[str, Any] = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def device_info(self):
        return {
            "identifiers": {("fuel_watcher", self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }


# ---------------------------------------------------------------------------
# Range (km)
# ---------------------------------------------------------------------------

class FuelWatcherRangeKmSensor(_BaseStrategySensor):
    """Range in km (from user-provided entity)."""

    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "km"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Range (km)", "range_km")

    async def async_update(self):
        entity_id = self.entry.options.get("range_entity")
        if not entity_id:
            self._state = None
            return

        st = self.hass.states.get(entity_id)
        if not st:
            self._state = None
            return

        try:
            self._state = float(st.state)
        except Exception:
            self._state = None


# ---------------------------------------------------------------------------
# Days Left
# ---------------------------------------------------------------------------

class FuelWatcherDaysLeftSensor(_BaseStrategySensor):
    """Estimated days left based on km_left and learned daily km."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Days Left", "days_left")

    async def async_update(self):
        entity_id = self.entry.options.get("range_entity")
        if not entity_id:
            self._state = None
            return

        st = self.hass.states.get(entity_id)
        if not st:
            self._state = None
            return

        try:
            km_left = float(st.state)
        except Exception:
            self._state = None
            return

        days = await estimate_days_left(self.hass, self.entry, km_left=km_left)
        self._state = days
        self._attrs["km_left"] = km_left


# ---------------------------------------------------------------------------
# Price Delta
# ---------------------------------------------------------------------------

class FuelWatcherPriceDeltaSensor(_BaseStrategySensor):
    """Absolute price delta."""

    _attr_icon = "mdi:currency-eur"
    _attr_native_unit_of_measurement = "€/L"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Price Delta", "price_delta")

    async def async_update(self):
        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        if not station:
            self._state = None
            return

        try:
            current_price = float(station.get("price"))
        except Exception:
            self._state = None
            return

        delta = await compute_price_delta(self.hass, self.entry, current_price=current_price)
        self._state = delta
        self._attrs["current_price"] = current_price


# ---------------------------------------------------------------------------
# Price Delta Percent
# ---------------------------------------------------------------------------

class FuelWatcherPriceDeltaPercentSensor(_BaseStrategySensor):
    """Percent price delta."""

    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Price Delta (%)", "price_delta_percent")

    async def async_update(self):
        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        if not station:
            self._state = None
            return

        try:
            current_price = float(station.get("price"))
        except Exception:
            self._state = None
            return

        percent = await compute_price_delta_percent(self.hass, self.entry, current_price=current_price)
        self._state = percent
        self._attrs["current_price"] = current_price


# ---------------------------------------------------------------------------
# Price Spike
# ---------------------------------------------------------------------------

class FuelWatcherPriceSpikeSensor(_BaseStrategySensor):
    """Detect price spike."""

    _attr_icon = "mdi:alert"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Price Spike", "price_spike")

    async def async_update(self):
        threshold = float(self.entry.options.get("price_spike_threshold", 0.08))

        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        if not station:
            self._state = None
            return

        try:
            current_price = float(station.get("price"))
        except Exception:
            self._state = None
            return

        spike = await detect_price_spike(
            self.hass,
            self.entry,
            current_price=current_price,
            threshold=threshold,
        )

        self._state = spike
        self._attrs["threshold"] = threshold
        self._attrs["current_price"] = current_price


# ---------------------------------------------------------------------------
# Decision Sensor
# ---------------------------------------------------------------------------

class FuelWatcherDecisionSensor(_BaseStrategySensor):
    """Final tanking decision based on days_left + price_delta."""

    _attr_icon = "mdi:thought-bubble"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "Fuel Watcher Decision", "decision")

    async def async_update(self):
        # Load data
        data = await load_data(self.hass, self.entry)
        station = data.get("best_station")

        # Current price
        try:
            current_price = float(station.get("price")) if station else None
        except Exception:
            current_price = None

        # Last tank event
        last_tank = await get_last_tank_event(self.hass, self.entry)
        last_price = last_tank.get("price_per_liter") if last_tank else None

        # Range (km)
        range_entity = self.entry.options.get("range_entity")
        km_left = None
        if range_entity:
            st = self.hass.states.get(range_entity)
            if st:
                try:
                    km_left = float(st.state)
                except Exception:
                    km_left = None

        # Days left
        days_left = await estimate_days_left(self.hass, self.entry, km_left=km_left)

        # Price delta
        delta = await compute_price_delta(self.hass, self.entry, current_price=current_price)

        # Decision thresholds
        min_days = float(self.entry.options.get("min_days_left", 2))
        delta_threshold = float(self.entry.options.get("decision_delta_threshold", -0.03))

        # Decision logic
        decision = "WAIT"
        reasons = []

        if days_left is not None:
            reasons.append(f"Days left: {days_left}")
            if days_left < min_days:
                decision = "TANK"
                reasons.append(f"Below threshold {min_days} days")

        if delta is not None:
            reasons.append(f"Price delta: {delta}")
            if delta <= delta_threshold:
                decision = "TANK"
                reasons.append(f"Delta below {delta_threshold}")

        # Set state
        self._state = decision
        self._attrs = {
            "days_left": days_left,
            "km_left": km_left,
            "current_price": current_price,
            "last_price": last_price,
            "price_delta": delta,
            "reasons": " | ".join(reasons),
        }
