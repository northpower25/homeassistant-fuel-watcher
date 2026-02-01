from homeassistant.components.sensor import SensorEntity

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
