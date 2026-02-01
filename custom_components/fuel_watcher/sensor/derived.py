from __future__ import annotations

from homeassistant.components.sensor import SensorEntity


class BaseDerivedSensor(SensorEntity):
    """Base class for derived Fuel Watcher sensors."""

    def __init__(self, main_sensor, name: str, attribute: str, unit: str | None = None):
        self._main = main_sensor
        self._attr_name = name
        self._attribute = attribute
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{main_sensor.unique_id}_{attribute}"

    @property
    def device_info(self):
        """Group all derived sensors under the same device as the main sensor."""
        return self._main.device_info

    @property
    def native_value(self):
        """Return the derived attribute value from the main sensor."""
        return self._main.extra_state_attributes.get(self._attribute)


# ---------------------------------------------------------------------------
# Preis & Tankstelle
# ---------------------------------------------------------------------------

class FuelWatcherPriceSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Preis", "price", "€/l")


class FuelWatcherStationNameSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Tankstelle", "station")


class FuelWatcherDistanceSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Entfernung", "distance_km", "km")


# ---------------------------------------------------------------------------
# Fahrzeugdaten
# ---------------------------------------------------------------------------

class FuelWatcherRangeSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Reichweite", "range_km", "km")


class FuelWatcherFuelLevelSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Tankfüllstand", "fuel_level", "%")


class FuelWatcherConsumptionSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(
            main_sensor,
            "Fuel Watcher Verbrauch",
            "consumption_l_100km",
            "l/100km",
        )


class FuelWatcherOdometerSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Kilometerstand", "odometer", "km")


# ---------------------------------------------------------------------------
# Strategie
# ---------------------------------------------------------------------------

class FuelWatcherStrategyDecisionSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Entscheidung", "strategy_decision")


class FuelWatcherStrategyReasonSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Begründung", "strategy_reason")


# ---------------------------------------------------------------------------
# Diagnose
# ---------------------------------------------------------------------------

class FuelWatcherHealthScoreSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Health Score", "health_score")


class FuelWatcherLastErrorSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(main_sensor, "Fuel Watcher Fehler", "last_error")


# ---------------------------------------------------------------------------
# Neuer Sensor: Erwarteter Verbrauch morgen
# ---------------------------------------------------------------------------

class FuelWatcherExpectedConsumptionTomorrowSensor(BaseDerivedSensor):
    def __init__(self, main_sensor):
        super().__init__(
            main_sensor,
            "Fuel Watcher Verbrauch Morgen",
            "expected_consumption_tomorrow",
            "km",
        )
