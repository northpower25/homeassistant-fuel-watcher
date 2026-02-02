from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..const import DOMAIN
from ..tank_history import get_last_tank_event


class _BaseStrategySensor(SensorEntity):
    """Base class for strategy-related sensors."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name_suffix: str, unique_suffix: str) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = f"Fuel Watcher {name_suffix}"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{unique_suffix}"
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


class FuelWatcherRangeKmSensor(_BaseStrategySensor):
    """Reichweite in km."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Reichweite (km)", "range_km")

    async def async_update(self) -> None:
        entity = self.entry.options.get("range_entity")
        if not entity:
            self._state = None
            return

        st = self.hass.states.get(entity)
        if not st:
            self._state = None
            return

        try:
            self._state = float(st.state)
        except:
            self._state = None


class FuelWatcherDaysLeftSensor(_BaseStrategySensor):
    """Reichweite in Tagen."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Reichweite (Tage)", "days_left")

    async def async_update(self) -> None:
        range_entity = self.entry.options.get("range_entity")
        consumption_entity = self.entry.options.get("consumption_entity")

        if not range_entity or not consumption_entity:
            self._state = None
            return

        st_range = self.hass.states.get(range_entity)
        st_cons = self.hass.states.get(consumption_entity)

        if not st_range or not st_cons:
            self._state = None
            return

        try:
            km_left = float(st_range.state)
            cons = float(st_cons.state)  # L/100km
        except:
            self._state = None
            return

        avg_daily_km = float(self.entry.options.get("avg_daily_km", 40))
        self._state = round(km_left / avg_daily_km, 1)
        self._attrs["km_left"] = km_left
        self._attrs["avg_daily_km"] = avg_daily_km


class FuelWatcherPriceDeltaSensor(_BaseStrategySensor):
    """Preis-Delta zum letzten Tankvorgang."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Delta", "price_delta")

    async def async_update(self) -> None:
        price_entity = self.entry.options.get("main_price_entity")
        if not price_entity:
            self._state = None
            return

        st = self.hass.states.get(price_entity)
        if not st:
            self._state = None
            return

        try:
            current_price = float(st.state)
        except:
            self._state = None
            return

        last = get_last_tank_event(self.hass, self.entry)
        if not last:
            self._state = None
            return

        last_price = last.get("price_per_liter")
        if last_price is None:
            self._state = None
            return

        delta = current_price - float(last_price)
        self._state = round(delta, 3)
        self._attrs["current_price"] = current_price
        self._attrs["last_price"] = last_price


class FuelWatcherPriceSpikeSensor(_BaseStrategySensor):
    """Preis-Spike."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Spike", "price_spike")

    async def async_update(self) -> None:
        threshold = float(self.entry.options.get("price_spike_threshold", 0.08))
        price_entity = self.entry.options.get("main_price_entity")

        if not price_entity:
            self._state = None
            return

        st = self.hass.states.get(price_entity)
        if not st:
            self._state = None
            return

        try:
            current_price = float(st.state)
        except:
            self._state = None
            return

        last = get_last_tank_event(self.hass, self.entry)
        if not last:
            self._state = None
            return

        last_price = last.get("price_per_liter")
        if last_price is None:
            self._state = None
            return

        delta = current_price - float(last_price)
        self._attrs["delta"] = round(delta, 3)
        self._attrs["threshold"] = threshold
        self._state = delta >= threshold


class FuelWatcherDecisionSensor(_BaseStrategySensor):
    """Entscheidung: Tanken / Warten."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Entscheidung", "decision")

    async def async_update(self) -> None:
        days_entity = self.entry.options.get("days_left_entity")
        delta_entity = self.entry.options.get("price_delta_entity")

        days_left = None
        price_delta = None

        if days_entity:
            st = self.hass.states.get(days_entity)
            if st:
                try:
                    days_left = float(st.state)
                except:
                    pass

        if delta_entity:
            st = self.hass.states.get(delta_entity)
            if st:
                try:
                    price_delta = float(st.state)
                except:
                    pass

        min_days_left = float(self.entry.options.get("min_days_left", 2))
        delta_threshold = float(self.entry.options.get("decision_delta_threshold", -0.03))

        decision = "Warten"
        reasons = []

        if days_left is not None:
            reasons.append(f"Reichweite: {days_left} Tage")
            if days_left < min_days_left:
                decision = "Tanken"
                reasons.append(f"unter {min_days_left} Tagen")

        if price_delta is not None:
            reasons.append(f"Preis-Delta: {price_delta} €/L")
            if price_delta <= delta_threshold:
                decision = "Tanken"
                reasons.append(f"Delta unter {delta_threshold} €/L")

        self._state = decision
        self._attrs["reason"] = " | ".join(reasons)
