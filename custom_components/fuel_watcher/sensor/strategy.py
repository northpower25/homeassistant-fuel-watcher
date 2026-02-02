from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er

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
        range_entity_id = self.entry.options.get("range_entity")
        if not range_entity_id:
            self._state = None
            return
        st = self.hass.states.get(range_entity_id)
        if not st:
            self._state = None
            return
        try:
            self._state = float(st.state)
        except ValueError:
            self._state = None


class FuelWatcherDaysLeftSensor(_BaseStrategySensor):
    """Reichweite in Tagen."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Reichweite (Tage)", "days_left")

    async def async_update(self) -> None:
        # sehr vereinfachtes Modell: km / (durchschnittliche Tageskilometer)
        avg_daily_km = float(self.entry.options.get("avg_daily_km", 40))
        range_entity_id = self.entry.options.get("range_entity")
        if not range_entity_id:
            self._state = None
            return
        st = self.hass.states.get(range_entity_id)
        if not st:
            self._state = None
            return
        try:
            km_left = float(st.state)
        except ValueError:
            self._state = None
            return
        self._state = round(km_left / avg_daily_km, 1)


class FuelWatcherPriceDeltaSensor(_BaseStrategySensor):
    """Preis-Delta zum letzten Tankvorgang."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Delta", "price_delta")

    async def async_update(self) -> None:
        main_entity_id = self.entry.options.get("main_price_entity")
        current_price = None

        if main_entity_id:
            st = self.hass.states.get(main_entity_id)
            if st:
                try:
                    current_price = float(st.state)
                except ValueError:
                    current_price = None

        last = get_last_tank_event(self.hass, self.entry)
        if not last or current_price is None:
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
    """Preis-Spike (z.B. > X Cent über letztem Preis)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Spike", "price_spike")

    async def async_update(self) -> None:
        threshold = float(self.entry.options.get("price_spike_threshold", 0.08))
        main_entity_id = self.entry.options.get("main_price_entity")
        current_price = None

        if main_entity_id:
            st = self.hass.states.get(main_entity_id)
            if st:
                try:
                    current_price = float(st.state)
                except ValueError:
                    current_price = None

        last = get_last_tank_event(self.hass, self.entry)
        if not last or current_price is None:
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
    """Entscheidung: Tanken / Warten + Begründung."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Entscheidung", "decision")

    async def async_update(self) -> None:
        # sehr vereinfachte Heuristik: wenn Tage < X oder Preis-Spike negativ → Tanken
        days_entity_id = f"sensor.fuel_watcher_reichweite_tage"  # optional: anpassen
        days_left = None
        st_days = self.hass.states.get(days_entity_id)
        if st_days:
            try:
                days_left = float(st_days.state)
            except ValueError:
                days_left = None

        last = get_last_tank_event(self.hass, self.entry)
        reason_parts = []

        if days_left is not None and days_left < float(self.entry.options.get("min_days_left", 2)):
            decision = "Tanken"
            reason_parts.append(f"Reichweite nur noch {days_left} Tage")
        else:
            decision = "Warten"
            if days_left is not None:
                reason_parts.append(f"Reichweite noch {days_left} Tage")

        if last:
            reason_parts.append(f"Letzter Preis: {last.get('price_per_liter')} €/L")

        self._state = decision
        self._attrs["reason"] = " | ".join(reason_parts)
