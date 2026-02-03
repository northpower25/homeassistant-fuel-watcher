from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, CONF_TANK_HISTORY_RETENTION_MONTHS, DEFAULT_TANK_HISTORY_RETENTION_MONTHS

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_tank_history"

SIGNAL_TANK_HISTORY_UPDATED = f"{DOMAIN}_tank_history_updated"

# legacy file path helper (for migration)
def _legacy_data_path(hass: HomeAssistant, entry: ConfigEntry) -> str:
    base = hass.config.path(f"custom_components/{DOMAIN}/data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{entry.entry_id}.json")


class TankHistoryStore:
    """Asynchronous, versioned store for tank events."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        # include entry_id in key so each config entry is isolated
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")

    async def async_initialize(self) -> None:
        """Initialize store; perform migration from legacy file if needed."""
        data = await self._store.async_load()
        if data is None:
            legacy = _legacy_data_path(self.hass, self.entry)
            if os.path.exists(legacy):
                try:
                    with open(legacy, "r", encoding="utf-8") as f:
                        legacy_data = json.load(f)
                    events = legacy_data.get("tank_events", []) if isinstance(legacy_data, dict) else []
                    await self._store.async_save({"tank_events": events})
                    _LOGGER.info("Migrated legacy tank history for entry %s to Store", self.entry.entry_id)
                except Exception as e:
                    _LOGGER.error("Error migrating legacy tank history %s: %s", legacy, e)
            else:
                await self._store.async_save({"tank_events": []})

    async def async_get_events(self) -> list[dict]:
        data = await self._store.async_load() or {"tank_events": []}
        return data.get("tank_events", [])

    async def async_get_last_event(self) -> dict | None:
        events = await self.async_get_events()
        return events[-1] if events else None

    def _get_retention_months(self) -> int:
        options = self.entry.options or self.entry.data
        return int(options.get(CONF_TANK_HISTORY_RETENTION_MONTHS, DEFAULT_TANK_HISTORY_RETENTION_MONTHS))

    def _apply_retention_to_list(self, events: list[dict]) -> list[dict]:
        months = self._get_retention_months()
        if months <= 0:
            return events
        cutoff = datetime.utcnow() - relativedelta(months=months)
        filtered: list[dict] = []
        for ev in events:
            ts = ev.get("ts")
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                # keep malformed timestamps to avoid data loss
                filtered.append(ev)
                continue
            if dt >= cutoff:
                filtered.append(ev)
        return filtered

    async def async_append_event(
        self,
        *,
        price_per_liter: float,
        liters: float | None = None,
        total_cost: float | None = None,
        station_name: str | None = None,
        suggested_price: float | None = None,
        odometer: float | None = None,
        source: str = "manual",
        # future: accept vehicle_id, fuel_type, raw_message, station_coords, etc.
    ) -> dict:
        data = await self._store.async_load() or {"tank_events": []}
        events = data.get("tank_events", [])

        if liters is not None and total_cost is None:
            total_cost = round(liters * price_per_liter, 2)

        savings = None
        if suggested_price is not None:
            savings = round(suggested_price - price_per_liter, 3)

        next_id = max((int(e.get("id", 0)) for e in events), default=0) + 1

        event = {
            "id": next_id,
            "ts": datetime.utcnow().isoformat(),
            "price_per_liter": price_per_liter,
            "liters": liters,
            "total_cost": total_cost,
            "station_name": station_name,
            "suggested_price": suggested_price,
            "savings": savings,
            "odometer": odometer,
            "source": source,
        }

        events.append(event)
        events = self._apply_retention_to_list(events)
        await self._store.async_save({"tank_events": events})

        # notify listeners (pass entry_id so listeners can filter)
        async_dispatcher_send(self.hass, SIGNAL_TANK_HISTORY_UPDATED, self.entry.entry_id)
        return event

    async def async_update_event(self, *, event_id: int, **updates) -> bool:
        data = await self._store.async_load() or {"tank_events": []}
        events = data.get("tank_events", [])

        changed = False
        for ev in events:
            if int(ev.get("id")) == int(event_id):
                ev.update(updates)
                price = ev.get("price_per_liter")
                suggested = ev.get("suggested_price")
                if price is not None and suggested is not None:
                    ev["savings"] = round(suggested - price, 3)
                changed = True
                break

        if changed:
            events = self._apply_retention_to_list(events)
            await self._store.async_save({"tank_events": events})
            async_dispatcher_send(self.hass, SIGNAL_TANK_HISTORY_UPDATED, self.entry.entry_id)
        return changed

    async def async_delete_event(self, *, event_id: int) -> bool:
        data = await self._store.async_load() or {"tank_events": []}
        events = data.get("tank_events", [])
        new_events = [e for e in events if int(e.get("id")) != int(event_id)]
        if len(new_events) == len(events):
            return False
        await self._store.async_save({"tank_events": new_events})
        async_dispatcher_send(self.hass, SIGNAL_TANK_HISTORY_UPDATED, self.entry.entry_id)
        return True

    async def async_clear(self) -> None:
        await self._store.async_save({"tank_events": []})
        async_dispatcher_send(self.hass, SIGNAL_TANK_HISTORY_UPDATED, self.entry.entry_id)
