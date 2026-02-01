import logging
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

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass, entry, async_add_entities):
    main_sensor = FuelWatcherSensor(hass, entry)
    diag_sensor = FuelWatcherDiagnosticsSensor(hass, entry, main_sensor)

    async_add_entities([main_sensor, diag_sensor])

    async def update(now):
        await main_sensor.async_update()
        diag_sensor.update_from_main()

    async_track_time_interval(hass, update, SCAN_INTERVAL)


class FuelWatcherSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry

        self._api = entry.data.get(CONF_TANKERKOENIG_API)
        self._token = entry.data.get(CONF_TELEGRAM_TOKEN)
        self._chat = entry.data.get(CONF_TELEGRAM_CHAT_ID)
        self._plz = entry.data.get(CONF_PLZ)
        self._radius = entry.data.get(CONF_RADIUS)
        self._fuel = entry.data.get(CONF_FUEL)
        self._source = entry.data.get(CONF_SOURCE, SOURCE_TANKERKOENIG)

        self._price_threshold = float(entry.data.get(CONF_PRICE_THRESHOLD, 0.0))
        self._distance_threshold = float(entry.data.get(CONF_DISTANCE_THRESHOLD, 10.0))

        self._attr_name = "Fuel Watcher"
        self._attr_native_unit_of_measurement = "€/l"
        self._last_price = None
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

        self._diag = {
            "last_update_ok": False,
            "last_error": None,
            "last_vehicle": None,
            "last_price_data": None,
            "last_distance": None,
            "last_strategy": None,
        }

    async def async_update(self):
        _LOGGER.debug("FuelWatcher: Update gestartet")

        # --- Preisquelle ---
        try:
            data = await get_cheapest(
                self.hass,
                self._source,
                self._api,
                self._plz,
                self._radius,
                self._fuel
            )
            self._diag["last_price_data"] = data
        except Exception as e:
            self._diag["last_error"] = f"Preisquelle Fehler: {e}"
            _LOGGER.error(self._diag["last_error"])
            return

        if not data:
            self._diag["last_error"] = "Keine Daten von Preisquelle"
            _LOGGER.error(self._diag["last_error"])
            return

        price = data.get("price")
        station = data.get("name")
        station_lat = data.get("lat")
        station_lng = data.get("lng")

        # --- Fahrzeugdaten ---
        try:
            vehicle = get_vehicle_data(self.hass, self._entry)
            self._diag["last_vehicle"] = vehicle
        except Exception as e:
            self._diag["last_error"] = f"Fahrzeugdaten Fehler: {e}"
            _LOGGER.error(self._diag["last_error"])
            return

        fuel_level = vehicle.get("fuel_level")
        range_km = vehicle.get("range")
        consumption = vehicle.get("consumption")
        odometer = vehicle.get("odometer")
        location_entity = vehicle.get("location")

        # --- Historie ---
        try:
            update_history(range_km, odometer)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in update_history: {e}")

        # --- Standort robust ---
        distance_info = None
        try:
            if isinstance(location_entity, str) and "," in location_entity:
                lat_str, lon_str = location_entity.split(",")
                vlat = float(lat_str)
                vlon = float(lon_str)
                distance_info = haversine_km(vlat, vlon, station_lat, station_lng)
            else:
                loc_state = self.hass.states.get(self._entry.data.get(CONF_ENTITY_LOCATION))
                if loc_state:
                    lat = loc_state.attributes.get("latitude")
                    lon = loc_state.attributes.get("longitude")
                    if lat is not None and lon is not None:
                        distance_info = haversine_km(float(lat), float(lon), station_lat, station_lng)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in Standortberechnung: {e}")

        self._diag["last_distance"] = distance_info

        # --- Strategie ---
        try:
            now = dt_util.utcnow()
            decision, reason = decide_tank_strategy(now, range_km)
            self._diag["last_strategy"] = {"decision": decision, "reason": reason}
        except Exception as e:
            self._diag["last_error"] = f"Strategie Fehler: {e}"
            _LOGGER.error(self._diag["last_error"])
            decision, reason = None, None

        # --- Sensorwerte setzen ---
        self._attr_native_value = price
        self._attr_extra_state_attributes = {
            "station": station,
            "fuel": self._fuel,
            "source": self._source,
            "fuel_level": fuel_level,
            "range_km": range_km,
            "consumption_l_100km": consumption,
            "odometer": odometer,
            "location": location_entity,
            "distance_km": distance_info,
            "strategy_decision": decision,
            "strategy_reason": reason,
        }

        self._diag["last_update_ok"] = True
        self._diag["last_error"] = None

        _LOGGER.debug("FuelWatcher: Update abgeschlossen")


class FuelWatcherDiagnosticsSensor(SensorEntity):
    def __init__(self, hass, entry, main_sensor):
        self.hass = hass
        self._entry = entry
        self._main = main_sensor

        self._attr_name = "Fuel Watcher Diagnostics"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    def update_from_main(self):
        diag = self._main._diag
        self._attr_native_value = "ok" if diag["last_update_ok"] else "error"
        self._attr_extra_state_attributes = diag
