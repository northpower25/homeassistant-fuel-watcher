import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .sources import get_cheapest
from .sources.geocode import get_dynamic_postcode
from .telegram import send_telegram
from .vehicle import get_vehicle_data
from .statistics import (
    haversine_km,
    update_history,
    decide_tank_strategy,
)
from .const import (
    DOMAIN,
    CONF_TANKERKOENIG_API,
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_PLZ,
    CONF_RADIUS,
    CONF_FUEL,
    CONF_SOURCE,
    CONF_PRICE_THRESHOLD,
    CONF_DISTANCE_THRESHOLD,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_RANGE,
    CONF_ENTITY_CONSUMPTION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_LOCATION,
    CONF_DYNAMIC_PLZ,
    SOURCE_TANKERKOENIG,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


def validate_entities(hass, entry):
    """Check if all configured entities exist in Home Assistant."""
    missing = []

    def check(key):
        entity_id = entry.options.get(key) or entry.data.get(key)
        if entity_id and hass.states.get(entity_id) is None:
            missing.append(entity_id)

    check(CONF_ENTITY_FUEL_LEVEL)
    check(CONF_ENTITY_RANGE)
    check(CONF_ENTITY_CONSUMPTION)
    check(CONF_ENTITY_ODOMETER)
    check(CONF_ENTITY_LOCATION)

    return missing


async def async_setup_entry(hass, entry, async_add_entities):
    main_sensor = FuelWatcherSensor(hass, entry)
    diag_sensor = FuelWatcherDiagnosticsSensor(hass, entry, main_sensor)
    location_sensor = FuelWatcherLocationSensor(hass, entry)
    postcode_sensor = FuelWatcherPostcodeSensor(hass, entry, main_sensor)

    async_add_entities([main_sensor, diag_sensor, location_sensor, postcode_sensor])

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN]["sensor"] = main_sensor

    missing = validate_entities(hass, entry)
    if missing:
        _LOGGER.warning(f"[FuelWatcher] Fehlende Entities: {missing}")
        main_sensor._diag["missing_entities"] = missing
    else:
        main_sensor._diag["missing_entities"] = []

    async def update(now):
        await main_sensor.async_update()
        await location_sensor.async_update()
        await postcode_sensor.async_update()
        diag_sensor.update_from_main()

    async_track_time_interval(hass, update, SCAN_INTERVAL)


class FuelWatcherSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry

        self._api = entry.data.get(CONF_TANKERKOENIG_API)
        self._token = entry.data.get(CONF_TELEGRAM_TOKEN)
        self._chat = entry.data.get(CONF_TELEGRAM_CHAT_ID)

        self._plz = entry.options.get(CONF_PLZ) or entry.data.get(CONF_PLZ)
        self._radius = entry.options.get(CONF_RADIUS) or entry.data.get(CONF_RADIUS)
        self._fuel = entry.options.get(CONF_FUEL) or entry.data.get(CONF_FUEL)
        self._source = entry.options.get(CONF_SOURCE) or entry.data.get(CONF_SOURCE, SOURCE_TANKERKOENIG)
        self._dynamic_plz = entry.options.get(CONF_DYNAMIC_PLZ, entry.data.get(CONF_DYNAMIC_PLZ, False))

        self._price_threshold = float(entry.options.get(CONF_PRICE_THRESHOLD, entry.data.get(CONF_PRICE_THRESHOLD, 0.0)))
        self._distance_threshold = float(entry.options.get(CONF_DISTANCE_THRESHOLD, entry.data.get(CONF_DISTANCE_THRESHOLD, 10.0)))

        self._attr_name = "Fuel Watcher"
        self._attr_native_unit_of_measurement = "€/l"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

        self._diag = {
            "last_update_ok": False,
            "last_error": None,
            "last_vehicle": None,
            "last_price_data": None,
            "last_distance": None,
            "last_strategy": None,
            "missing_entities": [],
            "dynamic_plz": None,
            "health_score": 0,
            "checks": {},
            "manual_test": None,
        }

    async def async_update(self):
        _LOGGER.debug("FuelWatcher: Update gestartet")

        # Dynamische PLZ
        if self._dynamic_plz:
            entity_loc = self._entry.options.get(CONF_ENTITY_LOCATION) or self._entry.data.get(CONF_ENTITY_LOCATION)
            dynamic_plz = None
            if entity_loc:
                dynamic_plz = await get_dynamic_postcode(self.hass, entity_loc)
            plz_to_use = dynamic_plz or self._plz
            self._diag["dynamic_plz"] = plz_to_use
        else:
            plz_to_use = self._plz
            self._diag["dynamic_plz"] = None

        # Preisquelle
        try:
            data = await get_cheapest(
                self.hass,
                self._source,
                self._api,
                plz_to_use,
                self._radius,
                self._fuel,
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

        # Fahrzeugdaten
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

        # Historie
        try:
            update_history(range_km, odometer)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in update_history: {e}")

        # Standort / Distanz
        distance_info = None
        try:
            if isinstance(location_entity, str) and "," in location_entity:
                lat_str, lon_str = location_entity.split(",")
                vlat = float(lat_str)
                vlon = float(lon_str)
                distance_info = haversine_km(vlat, vlon, station_lat, station_lng)
            else:
                loc_state = self.hass.states.get(self._entry.options.get(CONF_ENTITY_LOCATION) or self._entry.data.get(CONF_ENTITY_LOCATION))
                if loc_state:
                    lat = loc_state.attributes.get("latitude")
                    lon = loc_state.attributes.get("longitude")
                    if lat is not None and lon is not None:
                        distance_info = haversine_km(float(lat), float(lon), station_lat, station_lng)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in Standortberechnung: {e}")

        self._diag["last_distance"] = distance_info

        # Strategie
        try:
            now = dt_util.utcnow()
            decision, reason = decide_tank_strategy(now, range_km)
            self._diag["last_strategy"] = {"decision": decision, "reason": reason}
        except Exception as e:
            self._diag["last_error"] = f"Strategie Fehler: {e}"
            _LOGGER.error(self._diag["last_error"])
            decision, reason = None, None

        # Sensorwerte
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
            "plz_used": plz_to_use,
        }

        checks = {}
        checks["price_source"] = data is not None
        checks["vehicle_data"] = vehicle is not None and any(vehicle.values())
        checks["location_valid"] = distance_info is not None
        checks["strategy_valid"] = decision is not None
        checks["history_ok"] = True
        checks["telegram_ready"] = bool(self._token and self._chat)

        health_score = sum(1 for v in checks.values() if v)

        self._diag["checks"] = checks
        self._diag["health_score"] = health_score
        self._diag["last_update_ok"] = True
        self._diag["last_error"] = None

        _LOGGER.debug("FuelWatcher: Update abgeschlossen")

    async def run_test(self):
        _LOGGER.warning("FuelWatcher: Starte manuelle Testdiagnose")

        results = {}

        try:
            data = await get_cheapest(
                self.hass,
                self._source,
                self._api,
                self._plz,
                self._radius,
                self._fuel,
            )
            results["price_source"] = data is not None
        except Exception:
            results["price_source"] = False
            data = None

        try:
            vehicle = get_vehicle_data(self.hass, self._entry)
            results["vehicle_data"] = vehicle is not None and any(vehicle.values())
        except Exception:
            results["vehicle_data"] = False
            vehicle = {}

        try:
            loc = vehicle.get("location")
            results["location_valid"] = loc is not None
        except Exception:
            results["location_valid"] = False

        try:
            now = dt_util.utcnow()
            decision, reason = decide_tank_strategy(now, vehicle.get("range"))
            results["strategy_valid"] = decision is not None
        except Exception:
            results["strategy_valid"] = False

        try:
            update_history(vehicle.get("range"), vehicle.get("odometer"))
            results["history_ok"] = True
        except Exception:
            results["history_ok"] = False

        results["telegram_ready"] = bool(self._token and self._chat)

        self._diag["manual_test"] = results
        _LOGGER.warning(f"FuelWatcher Testdiagnose: {results}")


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


class FuelWatcherLocationSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        self._attr_name = "Fuel Watcher Location"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        entity_id = self._entry.options.get(CONF_ENTITY_LOCATION) or self._entry.data.get(CONF_ENTITY_LOCATION)
        if not entity_id:
            self._attr_native_value = "unknown"
            self._attr_extra_state_attributes = {}
            return

        state = self.hass.states.get(entity_id)
        if not state:
            self._attr_native_value = "unknown"
            self._attr_extra_state_attributes = {}
            return

        lat = state.attributes.get("latitude")
        lon = state.attributes.get("longitude")

        self._attr_native_value = f"{lat},{lon}" if lat is not None and lon is not None else "unknown"
        self._attr_extra_state_attributes = {
            "latitude": lat,
            "longitude": lon,
            "entity": entity_id,
        }


class FuelWatcherPostcodeSensor(SensorEntity):
    def __init__(self, hass, entry, main_sensor):
        self.hass = hass
        self._entry = entry
        self._main = main_sensor
        self._attr_name = "Fuel Watcher Postcode"
        self._attr_native_value = None

    async def async_update(self):
        dynamic_plz = self._main._diag.get("dynamic_plz")
        self._attr_native_value = dynamic_plz or "unknown"
