from datetime import datetime, timedelta
import json
import os
import math
from .const import HISTORY_FILE

CHEAP_HOURS = {
    "monday": [18, 19, 20],
    "tuesday": [19, 20],
    "wednesday": [19, 20, 21],
    "thursday": [19, 20, 21],
    "friday": [20, 21],
    "saturday": [20, 21],
    "sunday": [20],
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {
            "daily_km": {},
            "last_range": None,
            "last_odometer": None,
            "last_ts": None,
            "avg_consumption": None,
        }
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "daily_km": {},
            "last_range": None,
            "last_odometer": None,
            "last_ts": None,
            "avg_consumption": None,
        }

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception as e:
        print("History save error:", e)

def update_history(range_km, odometer):
    history = load_history()
    now = datetime.utcnow()
    today = now.date().isoformat()

    last_range = history.get("last_range")
    last_odometer = history.get("last_odometer")

    # km aus Odometer
    driven_km = None
    if odometer is not None and last_odometer is not None:
        try:
            driven_km = float(odometer) - float(last_odometer)
            if driven_km < 0:
                driven_km = None
        except ValueError:
            driven_km = None

    # Reichweitenänderung
    range_diff = None
    if range_km is not None and last_range is not None:
        try:
            range_diff = float(last_range) - float(range_km)
            if range_diff < 0:
                range_diff = None
        except ValueError:
            range_diff = None

    daily_km = history.get("daily_km", {})

    if driven_km is not None and driven_km > 0:
        daily_km[today] = daily_km.get(today, 0.0) + driven_km

    # Verbrauchsschätzung
    avg_consumption = history.get("avg_consumption")
    if driven_km is not None and range_diff is not None and range_diff > 0:
        try:
            consumption = (driven_km / range_diff) * 100.0
            if avg_consumption is None:
                avg_consumption = consumption
            else:
                avg_consumption = (avg_consumption * 0.7) + (consumption * 0.3)
        except ZeroDivisionError:
            pass

    history["daily_km"] = daily_km
    history["last_range"] = range_km
    history["last_odometer"] = odometer
    history["last_ts"] = now.isoformat()
    history["avg_consumption"] = avg_consumption

    save_history(history)

def average_daily_km(days=14):
    history = load_history()
    daily_km = history.get("daily_km", {})
    if not daily_km:
        return None
    items = sorted(daily_km.items(), key=lambda x: x[0], reverse=True)[:days]
    if not items:
        return None
    total = sum(v for _, v in items)
    return total / len(items)

def get_avg_consumption():
    history = load_history()
    return history.get("avg_consumption")

def find_next_cheap_slot(now):
    weekday = now.strftime("%A").lower()
    hours = CHEAP_HOURS.get(weekday, [19, 20, 21])
    for h in hours:
        candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if candidate > now:
            return candidate
    for i in range(1, 3):
        day = now + timedelta(days=i)
        wd = day.strftime("%A").lower()
        hours = CHEAP_HOURS.get(wd, [19, 20])
        candidate = day.replace(hour=hours[0], minute=0, second=0, microsecond=0)
        return candidate
    return now + timedelta(hours=24)

def estimate_km_until(target_dt, avg_daily):
    if avg_daily is None:
        return None
    now = datetime.utcnow()
    delta_h = (target_dt - now).total_seconds() / 3600.0
    if delta_h <= 0:
        return 0.0
    return avg_daily * (delta_h / 24.0)

def decide_tank_strategy(now, range_km):
    if range_km is None:
        return None, "Keine Reichweite verfügbar"

    try:
        range_km = float(range_km)
    except ValueError:
        return None, "Reichweite nicht numerisch"

    avg = average_daily_km()
    next_slot = find_next_cheap_slot(now)

    if avg is None:
        return "tank_now", "Keine Verbrauchshistorie vorhanden – konservative Empfehlung: tanken"

    km_until_slot = estimate_km_until(next_slot, avg)
    if km_until_slot is None:
        return "tank_now", "Keine Verbrauchshistorie – konservative Empfehlung"

    if range_km < km_until_slot:
        return "tank_now", (
            f"Reichweite {range_km:.0f} km reicht voraussichtlich nicht bis zur günstigen Zeit "
            f"{next_slot.strftime('%a %H:%M')} (erwartet ~{km_until_slot:.0f} km)."
        )

    if range_km < km_until_slot * 1.2:
        return "warning", (
            f"Reichweite {range_km:.0f} km könnte knapp werden bis "
            f"{next_slot.strftime('%a %H:%M')} (erwartet ~{km_until_slot:.0f} km)."
        )

    return "wait", (
        f"Reichweite {range_km:.0f} km reicht komfortabel bis zur günstigen Zeit "
        f"{next_slot.strftime('%a %H:%M')} (erwartet ~{km_until_slot:.0f} km)."
    )
