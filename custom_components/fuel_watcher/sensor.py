from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .sources import get_cheapest
from .telegram import send_telegram
from .vehicle import get_vehicle_data
from .statistics import (
    haversine_km,
    update_history,
    decide_tank_strategy,
)
from .const import *

SCAN_INTERVAL = timedelta(minutes=5)

async def async_setup_entry(hass, entry, async_add_entities):
    sensor = FuelWatcherSensor(hass, entry)
    async_add_entities([sensor])

    async def update(now):
        await sensor.async_update()

    async_track_time_interval(hass, update, SCAN_INTERVAL)

class FuelWatcherSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry

        self._api = entry.data[CONF_TANKERKOENIG_API]
        self._token = entry.data[CONF_TELEGRAM_TOKEN]
        self._chat = entry.data[CONF_TELEGRAM_CHAT_ID]
        self._plz = entry.data[CONF_PLZ]
        self._radius = entry.data[CONF_RADIUS]
        self._fuel = entry.data[CONF_FUEL]
        self._source = entry.data.get(CONF_SOURCE, SOURCE_TANKERKOENIG)

        self._price_threshold = float(entry.data.get(CONF_PRICE_THRESHOLD, 0.0))
        self._distance_threshold = float(entry.data.get(CONF_DISTANCE_THRESHOLD, 10.0))

        self._attr_name = "Fuel Watcher"
        self._attr_native_unit_of_measurement = "€/l"
        self._last_price = None
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        data = get_cheapest(self._source, self._api, self._plz, self._radius, self._fuel)
        if not data:
            return

        price = data["price"]
        station = data["name"]
        station_lat = data.get("lat")
        station_lng = data.get("lng")

        vehicle = get_vehicle_data(self.hass, self._entry)
        fuel_level = vehicle["fuel_level"]
        range_km = vehicle["range"]
        consumption = vehicle["consumption"]
        odometer = vehicle["odometer"]
        location = vehicle["location"]

        # Historie aktualisieren (aus Reichweite + Odometer)
        update_history(range_km, odometer)

        distance_info = None
        distance_ok = True

        if location and station_lat is not None and station_lng is not None:
            try:
                lat_str, lon_str = [x.strip() for x in location.split(",")]
                vlat = float(lat_str)
                vlon = float(lon_str)
                dist = haversine_km(vlat, vlon, station_lat, station_lng)
                distance_info = dist
                if self._distance_threshold > 0 and dist > self._distance_threshold:
                    distance_ok = False
            except Exception as e:
                print("Location parse error:", e)

        price_ok = True
        if self._price_threshold > 0 and price > self._price_threshold:
            price_ok = False

        context = []

        if fuel_level is not None:
            try:
                if float(fuel_level) < 20:
                    context.append("Tankinhalt niedrig")
            except ValueError:
                pass

        if range_km is not None:
            try:
                r = float(range_km)
                if r < 100:
                    context.append("Reichweite gering")
            except ValueError:
                pass

        if consumption is not None:
            context.append(f"Verbrauch (Sensor): {consumption} L/100km")

        if distance_info is not None:
            context.append(f"Entfernung zur Tankstelle: {distance_info:.1f} km")

        now = dt_util.utcnow()
        decision, reason = decide_tank_strategy(now, range_km)

        if decision:
            context.append(f"Strategie: {decision}")
            context.append(reason)

        should_notify = False

        if self._last_price is None or price < self._last_price:
            should_notify = True

        if not price_ok:
            should_notify = False

        if not distance_ok:
            should_notify = False

        if should_notify:
            msg = f"⛽ Preis gefallen: {price:.3f} €/l ({self._fuel}) bei {station}"
            if context:
                msg += "\n" + " • ".join(context)
            send_telegram(self._token, self._chat, msg)

        self._last_price = price
        self._attr_native_value = price
        attrs = {"station": station, "fuel": self._fuel, "source": self._source}
        if distance_info is not None:
            attrs["distance_km"] = round(distance_info, 2)
        if fuel_level is not None:
            attrs["fuel_level"] = fuel_level
        if range_km is not None:
            attrs["range_km"] = range_km
        if consumption is not None:
            attrs["consumption_l_100km"] = consumption
        attrs["strategy_decision"] = decision
        attrs["strategy_reason"] = reason
        self._attr_extra_state_attributes = attrs
