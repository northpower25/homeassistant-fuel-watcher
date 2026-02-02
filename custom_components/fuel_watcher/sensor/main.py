from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..statistics import get_expected_consumption_tomorrow
from ..statistics_engine import (
    update_odometer_history,
    compute_weekday_consumption,
    compute_days_left_from_weekdays,
)
from ..sources import get_price_data
from ..notify import send_notification
from ..price_engine import update_price_history, compute_price_delta
from ..tank_history import append_tank_event, get_last_tank_event
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
    CONF_NOTIFY_ON_PRICE_DELTA,
    CONF_NOTIFY_MSG_PRICE_DELTA,
    DEFAULT_NOTIFY_MSG_PRICE_DELTA,
)


class FuelWatcherSensor(SensorEntity):
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
            self._attrs["station"] = price_data.get("station")
            self._attrs["station_lat"] = price_data.get("lat")
            self._attrs["station_lng"] = price_data.get("lng")
            self._attrs["distance_km"] = price_data.get("distance_km")
            self._attrs["fuel"] = price_data.get("fuel")
            self._attrs["station_id"] = price_data.get("id")
            self._attrs["station_street"] = price_data.get("street")
            self._attrs["station_house_number"] = price_data.get("houseNumber")
            self._attrs["station_post_code"] = price_data.get("postCode")
            self._attrs["station_place"] = price_data.get("place")

        self._update_vehicle_data()

        # Statistik aktualisieren
        odometer = self._attrs.get("odometer")
        update_odometer_history(self.hass, self.entry, odometer)

        options = self.entry.options or self.entry.data
        weekday_consumption = compute_weekday_consumption(self.hass, self.entry, options)

        expected_tomorrow = get_expected_consumption_tomorrow(self.entry, weekday_consumption)
        self._attrs["expected_consumption_tomorrow"] = expected_tomorrow

        range_km = self._attrs.get("range_km")
        days_left = compute_days_left_from_weekdays(self.entry, weekday_consumption, range_km)
        self._attrs["days_left"] = days_left

        # Preis-Historie & Delta
        price = self._attrs.get("price")
        update_price_history(self.hass, self.entry, price)
        price_delta_info = compute_price_delta(self.hass, self.entry, price)
        self._attrs["price_delta"] = price_delta_info.get("delta")
        self._attrs["price_delta_percent"] = price_delta_info.get("delta_percent")

        decision, reason = self._compute_strategy(expected_tomorrow, days_left)
        self._attrs["strategy_decision"] = decision
        self._attrs["strategy_reason"] = reason

        self._attrs["health_score"] = self._compute_health_score()

        await self._maybe_send_notifications(decision, reason, days_left, price_delta_info)

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

    async def _maybe_send_notifications(
        self,
        decision: str,
        reason: str,
        days_left: float,
        price_delta_info: dict,
    ):
        options = self.entry.options or self.entry.data
        if not options.get(CONF_NOTIFY_ENABLED, False):
            return

        price = self._attrs.get("price")
        range_km = self._attrs.get("range_km")
        lat = self._attrs.get("station_lat")
        lng = self._attrs.get("station_lng")

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
                lat=lat if lat is not None else 0,
                lng=lng if lng is not None else 0,
            )
            await send_notification(self.hass, self.entry, text)

        if options.get(CONF_NOTIFY_ON_RANGE_DAYS, True):
            threshold_days = float(options.get(CONF_NOTIFY_RANGE_DAYS_THRESHOLD, 2.0))
            if days_left is not None and days_left <= threshold_days:
                template = options.get(CONF_NOTIFY_MSG_RANGE_DAYS, DEFAULT_NOTIFY_MSG_RANGE_DAYS)
                text = template.format(days_left=days_left)
                await send_notification(self.hass, self.entry, text)

        if options.get(CONF_NOTIFY_ON_PRICE_DELTA, False) and price_delta_info.get("trigger"):
            template = options.get(CONF_NOTIFY_MSG_PRICE_DELTA, DEFAULT_NOTIFY_MSG_PRICE_DELTA)
            text = template.format(
                delta=price_delta_info.get("delta"),
                delta_percent=price_delta_info.get("delta_percent"),
                price=price,
            )
            await send_notification(self.hass, self.entry, text)

        self._last_decision = decision

        # Beispiel: Tankvorgang manuell (hier nur als Hook – echte Erfassung über OptionsFlow)
        last_tank = get_last_tank_event(self.hass, self.entry)
        self._attrs["last_tank_event"] = last_tank
