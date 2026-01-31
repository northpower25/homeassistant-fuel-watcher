def _read_state(hass, entity_id):
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if not state or state.state in ("unknown", "unavailable"):
        return None
    return state.state

def get_vehicle_data(hass, entry):
    data = {
        "fuel_level": _read_state(hass, entry.data.get("entity_fuel_level")),
        "range": _read_state(hass, entry.data.get("entity_range")),
        "consumption": _read_state(hass, entry.data.get("entity_consumption")),
        "odometer": _read_state(hass, entry.data.get("entity_odometer")),
        "location": _read_state(hass, entry.data.get("entity_location")),
    }
    return data
