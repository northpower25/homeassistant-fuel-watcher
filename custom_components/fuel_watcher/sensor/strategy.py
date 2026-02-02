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
    """Reichweite in km (aus range_entity)."""

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
        except (TypeError, ValueError):
            self._state = None


class FuelWatcherDaysLeftSensor(_BaseStrategySensor):
    """Reichweite in Tagen (aus Reichweite + Verbrauch)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Reichweite (Tage)", "days_left")

    async def async_update(self) -> None:
        range_entity_id = self.entry.options.get("range_entity")
        consumption_entity_id = self.entry.options.get("consumption_entity")

        if not range_entity_id or not consumption_entity_id:
            self._state = None
            return

        st_range = self.hass.states.get(range_entity_id)
        st_cons = self.hass.states.get(consumption_entity_id)

        if not st_range or not st_cons:
            self._state = None
            return

        try:
            km_left = float(st_range.state)
            cons_l_per_100km = float(st_cons.state)
        except (TypeError, ValueError):
            self._state = None
            return

        # sehr einfache Heuristik: Tageskilometer aus Verbrauch ableiten ist schwierig,
        # daher nutzen wir optional avg_daily_km, sonst 40 km/Tag.
        avg_daily_km = float(self.entry.options.get("avg_daily_km", 40))
        if avg_daily_km <= 0:
            self._state = None
            return

        self._state = round(km_left / avg_daily_km, 1)
        self._attrs["km_left"] = km_left
        self._attrs["avg_daily_km"] = avg_daily_km


class FuelWatcherPriceDeltaSensor(_BaseStrategySensor):
    """Preis-Delta zum letzten Tankvorgang."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Delta", "price_delta")

    async def async_update(self) -> None:
        main_price_entity = self.entry.options.get("main_price_entity")
        current_price = None

        if main_price_entity:
            st = self.hass.states.get(main_price_entity)
            if st:
                try:
                    current_price = float(st.state)
                except (TypeError, ValueError):
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
    """Preis-Spike (z.B. > X €/L über letztem Preis)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, "Preis-Spike", "price_spike")

    async def async_update(self) -> None:
        threshold = float(self.entry.options.get("price_spike_threshold", 0.08))
        main_price_entity = self.entry.options.get("main_price_entity")
        current_price = None

        if main_price_entity:
            st = self.hass.states.get(main_price_entity)
            if st:
                try:
                    current_price = float(st.state)
                except (TypeError, ValueError):
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
        # Tage bis leer
        days_sensor_id = self.entry.options.get("days_left_entity")
        days_left = None
        if days_sensor_id:
            st_days = self.hass.states.get(days_sensor_id)
            if st_days:
                try:
                    days_left = float(st_days.state)
                except (TypeError, ValueError):
                    days_left = None

        # Preis-Delta
        price_delta_entity = self.entry.options.get("price_delta_entity")
        price_delta = None
        if price_delta_entity:
            st_delta = self.hass.states.get(price_delta_entity)
            if st_delta:
                try:
                    price_delta = float(st_delta.state)
                except (TypeError, ValueError):
                    price_delta = None

        min_days_left = float(self.entry.options.get("min_days_left", 2))
        delta_threshold = float(self.entry.options.get("decision_delta_threshold", -0.03))

        reason_parts: list[str] = []

        # einfache Heuristik:
        # 1) Wenn Tage < min_days_left → Tanken
        # 2) Wenn Preis-Delta deutlich negativ → Tanken
        # 3) Sonst Warten
        decision = "Warten"

        if days_left is not None:
            reason_parts.append(f"Reichweite: {days_left} Tage")
            if days_left < min_days_left:
                decision = "Tanken"
                reason_parts.append(f"unter Schwellwert {min_days_left} Tage")

        if price_delta is not None:
            reason_parts.append(f"Preis-Delta: {price_delta} €/L")
            if price_delta <= delta_threshold:
                decision = "Tanken"
                reason_parts.append(f"Delta unter {delta_threshold} €/L")

        last = get_last_tank_event(self.hass, self.entry)
        if last:
            reason_parts.append(f"Letzter Preis: {last.get('price_per_liter')} €/L")

        self._state = decision
        self._attrs["reason"] = " | ".join(reason_parts)
