import requests

def get_cheapest(api_key, plz, radius, fuel):
    url = (
        "https://creativecommons.tankerkoenig.de/json/list.php"
        f"?zip={plz}&rad={radius}&sort=price&type={fuel}&apikey={api_key}"
    )
    data = requests.get(url, timeout=10).json()
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
