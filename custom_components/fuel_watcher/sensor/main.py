import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt as dt_util

from ..sources import get_cheapest
from ..vehicle import get_vehicle_data
from ..statistics import haversine_km, update_history, decide_tank_strategy
from ..const import (
    CONF_TANKERKOENIG_API,
    CONF_TELEGRAM_TOKEN,
    CONF_TELEGRAM_CHAT_ID,
    CONF_RADIUS,
    CONF_FUEL,
    CONF_SOURCE,
    CONF_PRICE_THRESHOLD,
    CONF_DISTANCE_THRESHOLD,
    CONF_ENTITY_LOCATION,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


class FuelWatcherSensor(SensorEntity):
    """Hauptsensor für Fuel Watcher."""

    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry

        # API / Token
        self._api = entry.data.get(CONF_TANKERKOENIG_API)
        self._token = entry.data.get(CONF_TELEGRAM_TOKEN)
        self._chat = entry.data.get(CONF_TELEGRAM_CHAT_ID)

        # Konfiguration
        self._radius = entry.options.get(CONF_RADIUS) or entry.data.get(CONF_RADIUS)
        self._fuel = entry.options.get(CONF_FUEL) or entry.data.get(CONF_FUEL)
        self._source = entry.options.get(CONF_SOURCE) or entry.data.get(CONF_SOURCE)

        self._price_threshold = float(entry.options.get(CONF_PRICE_THRESHOLD, entry.data.get(CONF_PRICE_THRESHOLD, 0.0)))
        self._distance_threshold = float(entry.options.get(CONF_DISTANCE_THRESHOLD, entry.data.get(CONF_DISTANCE_THRESHOLD, 10.0)))

        # Sensor-Metadaten
        self._attr_name = "Fuel Watcher"
        self._attr_native_unit_of_measurement = "€/l"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

        # Diagnose-Daten
        self._diag = {
            "last_update_ok": False,
            "last_error": None,
            "last_vehicle": None,
            "last_price_data": None,
            "last_distance": None,
            "last_strategy": None,
            "health_score": 0,
            "checks": {},
            "manual_test": None,
        }

    async def async_update(self):
        """Haupt-Update-Logik."""
        _LOGGER.debug("FuelWatcher: Update gestartet")

        # ---------------------------------------------------------
        # 1) Standort ermitteln (für Tankerkönig)
        # ---------------------------------------------------------
        loc_entity_id = self._entry.options.get(CONF_ENTITY_LOCATION) or self._entry.data.get(CONF_ENTITY_LOCATION)
        loc_state = self.hass.states.get(loc_entity_id) if loc_entity_id else None

        lat = None
        lon = None

        if loc_state:
            lat = loc_state.attributes.get("latitude")
            lon = loc_state.attributes.get("longitude")

        if lat is None or lon is None:
            self._diag["last_error"] = "Keine gültigen Koordinaten für Tankerkönig"
            _LOGGER.error(self._diag["last_error"])
            return

        # ---------------------------------------------------------
        # 2) Preisquelle (Tankerkoenig via lat/lng)
        # ---------------------------------------------------------
        try:
            data = await get_cheapest(
                self.hass,
                self._source,
                self._api,
                float(lat),
                float(lon),
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

        # ---------------------------------------------------------
        # 3) Fahrzeugdaten
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 4) Historie aktualisieren
        # ---------------------------------------------------------
        try:
            update_history(range_km, odometer)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in update_history: {e}")

        # ---------------------------------------------------------
        # 5) Distanz berechnen
        # ---------------------------------------------------------
        distance_info = None
        try:
            if station_lat and station_lng:
                distance_info = haversine_km(float(lat), float(lon), station_lat, station_lng)
        except Exception as e:
            _LOGGER.error(f"FuelWatcher: Fehler in Standortberechnung: {e}")

        self._diag["last_distance"] = distance_info

        # ---------------------------------------------------------
        # 6) Strategie berechnen
        # ---------------------------------------------------------
        try:
            now = dt_util.utcnow()
            decision, reason = decide_tank_strategy(now, range_km)
            self._diag["last_strategy"] = {"decision": decision, "reason": reason}
        except Exception as e:
            self._diag["last_error"] = f"Strategie Fehler: {e}"
            _LOGGER.error(self._diag["last_error"])
            decision, reason = None, None

        # ---------------------------------------------------------
        # 7) Sensorwerte setzen
        # ---------------------------------------------------------
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
            "lat": lat,
            "lon": lon,
        }

        # ---------------------------------------------------------
        # 8) Health-Check
        # ---------------------------------------------------------
        checks = {
            "price_source": data is not None,
            "vehicle_data": vehicle is not None and any(vehicle.values()),
            "location_valid": distance_info is not None,
            "strategy_valid": decision is not None,
            "history_ok": True,
            "telegram_ready": bool(self._token and self._chat),
        }

        self._diag["checks"] = checks
        self._diag["health_score"] = sum(1 for v in checks.values() if v)
        self._diag["last_update_ok"] = True
        self._diag["last_error"] = None

        _LOGGER.debug("FuelWatcher: Update abgeschlossen")
