from homeassistant.components.sensor import SensorEntity

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
