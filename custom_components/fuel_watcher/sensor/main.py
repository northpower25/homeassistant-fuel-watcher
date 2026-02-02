from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..statistics import get_expected_consumption_tomorrow, compute_days_left
from ..sources import get_price_data
from ..notify import send_notification
from ..const import (
    DOMAIN,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_ODOMETER,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_ON_DECISION_TANKEN,
    CONF_NOTIFY_ON_RANGE_DAYS,
    CONF_NOTIFY_RANGE_DAYS_THRESHOLD,
    CONF_NOTIFY_MSG_TANKEN,
    CONF_NOTIFY_MSG_RANGE_DAYS,
    DEFAULT_NOTIFY_MSG_TANKEN,
    DEFAULT_NOTIFY_MSG_RANGE_DAYS,
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
        self._last_decision = None

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
        price_data = await get_price_data(self.hass, self.entry)
        if price_data:
            self._state = price_data.get("price")
            self._attrs["price"] = price_data.get("price")
            self._attrs["station"] = price_data.get("name") or price_data.get("station")
            self._attrs["station_lat"] = price_data.get("lat")
            self._attrs["station_lng"] = price_data.get("lng")
            self._attrs["distance_km"] = price_data.get("distance_km")
            self._attrs["fuel"] = price_data.get("fuel")

        self._update_vehicle_data()

        expected_tomorrow = get_expected_consumption_tomorrow(self.entry)
        self._attrs["expected_consumption_tomorrow"] = expected_tomorrow

        range_km = self._attrs.get("range_km")
        days_left = compute_days_left(self.entry, range_km) if range_km is not None else 0.0
        self._attrs["days_left"] = days_left

        decision, reason = self._compute_strategy(expected_tomorrow, days_left)
        self._attrs["strategy_decision"] = decision
        self._attrs["strategy_reason"] = reason

        self._attrs["health_score"] = self._compute_health_score()

        await self._maybe_send_notifications(decision, reason, days_left)

    def _update_vehicle_data(self):
        data = self.entry.data
        options = self.entry.options or {}

        def get_entity_id(key):
            return options.get(key) or data.get(key)

        if entity_id := get_entity_id(CONF_ENTITY_RANGE):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["range_km"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        if entity_id := get_entity_id(CONF_ENTITY_FUEL_LEVEL):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["fuel_level"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        if entity_id := get_entity_id(CONF_ENTITY_CONSUMPTION):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["consumption_l_100km"] = float(state.state)
                except (TypeError, ValueError):
                    pass

        if entity_id := get_entity_id(CONF_ENTITY_ODOMETER):
            if state := self.hass.states.get(entity_id):
                try:
                    self._attrs["odometer"] = float(state.state)
                except (TypeError, ValueError):
                    pass

    def _compute_strategy(self, expected_tomorrow: int, days_left: float):
        price = self._attrs.get("price")
        range_km = self._attrs.get("range_km")

        if price is None or range_km is None:
            return "Unbekannt", "Unzureichende Daten"

        safety_buffer = 50

        if days_left <= 1.0:
            return (
                "Tanken",
                f"Reichweite reicht nur noch für {days_left} Tage",
            )

        if range_km < expected_tomorrow + safety_buffer:
            return (
                "Tanken",
                f"Reichweite {range_km} km < erwarteter Verbrauch morgen {expected_tomorrow} km",
            )

        threshold = self.entry.options.get("price_threshold", 0)
        if threshold > 0 and price <= threshold:
            return (
                "Tanken",
                f"Preis {price} €/l liegt unter der Schwelle von {threshold} €/l",
            )

        return (
            "Warten",
            f"Reichweite {range_km} km reicht für die nächsten Tage (ca. {days_left} Tage)",
        )

    def _compute_health_score(self):
        score = 100
        if self._attrs.get("price") is None:
            score -= 30
        if self._attrs.get("range_km") is None:
            score -= 30
        if self._attrs.get("distance_km") is None:
            score -= 20
        return max(0, score)

    async def _maybe_send_notifications(self, decision: str, reason: str, days_left: float):
        options = self.entry.options or self.entry.data
        if not options.get(CONF_NOTIFY_ENABLED, False):
            return

        price = self._attrs.get("price")
        range_km = self._attrs.get("range_km")

        if (
            options.get(CONF_NOTIFY_ON_DECISION_TANKEN, True)
            and decision == "Tanken"
            and self._last_decision != "Tanken"
        ):
            template = options.get(CONF_NOTIFY_MSG_TANKEN, DEFAULT_NOTIFY_MSG_TANKEN)
            text = template.format(
                reason=reason,
                price=price if price is not None else "n/a",
                range_km=range_km if range_km is not None else "n/a",
            )
            await send_notification(self.hass, self.entry, text)

        if options.get(CONF_NOTIFY_ON_RANGE_DAYS, True):
            threshold_days = float(options.get(CONF_NOTIFY_RANGE_DAYS_THRESHOLD, 2.0))
            if days_left is not None and days_left <= threshold_days:
                template = options.get(CONF_NOTIFY_MSG_RANGE_DAYS, DEFAULT_NOTIFY_MSG_RANGE_DAYS)
                text = template.format(days_left=days_left)
                await send_notification(self.hass, self.entry, text)

        self._last_decision = decision
