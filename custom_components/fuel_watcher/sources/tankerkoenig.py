import async_timeout


async def get_cheapest_tankerkoenig(hass, api_key, plz, radius, fuel):
    url = (
        "https://creativecommons.tankerkoenig.de/json/list.php"
        f"?zip={plz}&rad={radius}&sort=price&type={fuel}&apikey={api_key}"
    )

    session = hass.helpers.aiohttp_client.async_get_clientsession()

    try:
        async with async_timeout.timeout(10):
            async with session.get(url) as resp:
                data = await resp.json()
    except Exception as e:
        raise RuntimeError(f"Tankerkoenig API Fehler: {e}")

    stations = data.get("stations", [])
    if not stations:
        return None

    stations = [s for s in stations if s.get("price") is not None]
    if not stations:
        return None

    cheapest = min(stations, key=lambda x: x["price"])

    return {
        "price": cheapest["price"],
        "name": cheapest["name"],
        "lat": cheapest.get("lat"),
        "lng": cheapest.get("lng"),
    }
