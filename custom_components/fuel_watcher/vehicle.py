def get_vehicle_data(hass, entry):
    def safe_get(entity_id):
        if not entity_id:
            return None
        state = hass.states.get(entity_id)
        if not state:
            return None
        return state.state

    def safe_attr(entity_id, attr):
        if not entity_id:
            return None
        state = hass.states.get(entity_id)
        if not state:
            return None
        return state.attributes.get(attr)

    return {
        "fuel_level": safe_get(entry.data.get("entity_fuel_level")),
        "range": safe_get(entry.data.get("entity_range")),
        "consumption": safe_get(entry.data.get("entity_consumption")),
        "odometer": safe_get(entry.data.get("entity_odometer")),
        "location": safe_get(entry.data.get("entity_location")),
    }
