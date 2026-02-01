from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..statistics import get_expected_consumption_tomorrow
from ..sources import get_price_data
from ..const import (
    DOMAIN,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_ODOMETER,
)


class FuelWatcherSensor(SensorEntity):
    """Main Fuel Watcher sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_name = "Fuel Watcher"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._state = None
        self._attrs: dict = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "Fuel Watcher",
            "manufacturer": "Fuel Watcher",
            "model": "Fuel Strategy Engine",
        }

    async def async_update(self):
        """Update all data sources and compute strategy."""

        # --- 1. Preis- & Tankstellendaten ------------------------------------
        price_data = await get_price_data(self.hass, self.entry)
        if price_data:
            self._state = price_data.get("price")
            self._attrs["price"] = price_data.get("price")
            self._attrs["station"] = price_data.get("station")
            self._attrs["station_lat"] = price_data.get("lat")
            self._attrs["station_lng"] = price_data.get("lng")
            self._attrs["distance_km"] = price_data.get("distance_km")
            self._attrs["fuel"] = price_data.get("fuel")

        # --- 2. Fahrzeugdaten aus konfigurierten Entitäten -------------------
        self._update_vehicle_data()

        # --- 3. Erwarteter Verbrauch morgen ----------------------------------
        expected_tomorrow = get_expected_consumption_tomorrow(self.entry)
        self._attrs["expected_consumption_tomorrow"] = expected_tomorrow

        # --- 4. Strategie -----------------------------------------------------
        decision, reason = self._compute_strategy(expected_tomorrow)
        self._attrs["strategy_decision"] = decision
        self._attrs["strategy_reason"] = reason

        # --- 5. Health Score --------------------------------------------------
        self._attrs["health_score"] = self._compute_health_score()

    # -------------------------------------------------------------------------
    # Fahrzeugdaten
    # -------------------------------------------------------------------------
    def _update_vehicle_data(self):
        data = self.entry.data
        options = self.entry.options or {}

        def get_entity_id(key):
            return options.get(key) or data.get(key)

        # Reichweite
        if entity_id := get_entity_id(CONF_ENTITY_RANGE):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["range_km"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        # Tankfüllstand
        if entity_id := get_entity_id(CONF_ENTITY_FUEL_LEVEL):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["fuel_level"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        # Verbrauch
        if entity_id := get_entity_id(CONF_ENTITY_CONSUMPTION):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["consumption_l_100km"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        # Odometer
        if entity_id := get_entity_id(CONF_ENTITY_ODOMETER):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["odometer"] = float(state.state)
                except (TypeError, ValueError):
                    pass

    # -------------------------------------------------------------------------
    # Strategie-Logik
    # -------------------------------------------------------------------------
    def _compute_strategy(self, expected_tomorrow: int):
        price = self._attrs.get("price")
        range_km = self._attrs.get("range_km")

        if price is None or range_km is None:
            return "Unbekannt", "Unzureichende Daten"

        safety_buffer = 50  # km

        # Reicht die Reichweite bis morgen?
        if range_km < expected_tomorrow + safety_buffer:
            return (
                "Tanken",
                f"Reichweite {range_km} km < erwarteter Verbrauch morgen {expected_tomorrow} km",
            )

        # Preisbasierte Entscheidung
        threshold = self.entry.options.get("price_threshold", 0)
        if threshold > 0 and price <= threshold:
            return (
                "Tanken",
                f"Preis {price} €/l liegt unter der Schwelle von {threshold} €/l",
            )

        return (
            "Warten",
            f"Reichweite {range_km} km reicht für morgen (erwartet {expected_tomorrow} km)",
        )

    # -------------------------------------------------------------------------
    # Health Score
    # -------------------------------------------------------------------------
    def _compute_health_score(self):
        score = 100

        if self._attrs.get("price") is None:
            score -= 30
        if self._attrs.get("range_km") is None:
            score -= 30
        if self._attrs.get("distance_km") is None:
            score -= 20

        return max(0, score)
