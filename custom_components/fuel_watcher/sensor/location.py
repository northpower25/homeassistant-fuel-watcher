from homeassistant.components.sensor import SensorEntity
from ..const import CONF_ENTITY_LOCATION

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

        self._attr_native_value = f"{lat},{lon}" if lat and lon else "unknown"
        self._attr_extra_state_attributes = {
            "latitude": lat,
            "longitude": lon,
            "entity": entity_id,
        }
