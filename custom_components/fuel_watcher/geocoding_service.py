"""
Geocoding Service

Phase 3: Address resolution using OpenStreetMap Nominatim
- Reverse geocoding (coordinates to address)
- Geocoding cache to reduce API calls
- Rate limiting to respect OSM usage policy
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import storage

_LOGGER = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding and reverse geocoding using OSM Nominatim."""
    
    # OSM Nominatim API endpoint
    NOMINATIM_URL = "https://nominatim.openstreetmap.org"
    
    # Rate limiting: 1 request per second per OSM usage policy
    MIN_REQUEST_INTERVAL = 1.0  # seconds
    
    # Cache expiry: 30 days
    CACHE_EXPIRY_DAYS = 30
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize geocoding service."""
        self.hass = hass
        self.entry = entry
        self._last_request_time = None
        self._cache = {}
        self._user_agent = f"HomeAssistant-FuelWatcher/{entry.entry_id}"
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        use_cache: bool = True,
    ) -> Optional[str]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            use_cache: Whether to use cached results
        
        Returns:
            Address string or None if geocoding fails
        """
        # Check configuration
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        if not config.get("geocoding_enabled", True):
            _LOGGER.debug("Geocoding is disabled")
            return None
        
        # Create cache key
        cache_key = f"{latitude:.6f},{longitude:.6f}"
        
        # Check cache
        if use_cache and config.get("geocoding_cache_enabled", True):
            cached_address = await self._get_cached_address(cache_key)
            if cached_address:
                _LOGGER.debug("Using cached address for %s", cache_key)
                return cached_address
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        try:
            # Make API request
            address = await self._request_nominatim_reverse(latitude, longitude)
            
            if address:
                # Cache the result
                if config.get("geocoding_cache_enabled", True):
                    await self._cache_address(cache_key, address)
                
                _LOGGER.debug("Geocoded %s to: %s", cache_key, address)
                return address
            
        except Exception as e:
            _LOGGER.error("Geocoding failed for %s: %s", cache_key, str(e))
        
        return None
    
    async def _request_nominatim_reverse(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[str]:
        """Make reverse geocoding request to Nominatim API."""
        url = f"{self.NOMINATIM_URL}/reverse"
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": "1",
            "zoom": "18",  # Street level
        }
        
        headers = {
            "User-Agent": self._user_agent,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract address
                        address = data.get("display_name")
                        if address:
                            return address
                        
                        # Fallback: construct from address components
                        addr = data.get("address", {})
                        parts = []
                        
                        # Street
                        street = addr.get("road") or addr.get("pedestrian")
                        house_number = addr.get("house_number")
                        if street:
                            if house_number:
                                parts.append(f"{street} {house_number}")
                            else:
                                parts.append(street)
                        
                        # City
                        city = (
                            addr.get("city") or
                            addr.get("town") or
                            addr.get("village") or
                            addr.get("municipality")
                        )
                        if city:
                            parts.append(city)
                        
                        # Country
                        country = addr.get("country")
                        if country:
                            parts.append(country)
                        
                        if parts:
                            return ", ".join(parts)
                    
                    elif response.status == 429:
                        _LOGGER.warning("Nominatim rate limit exceeded")
                    else:
                        _LOGGER.warning("Nominatim returned status %d", response.status)
        
        except asyncio.TimeoutError:
            _LOGGER.warning("Nominatim request timed out")
        except Exception as e:
            _LOGGER.error("Nominatim request failed: %s", str(e))
        
        return None
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limit."""
        if self._last_request_time:
            elapsed = datetime.now().timestamp() - self._last_request_time
            if elapsed < self.MIN_REQUEST_INTERVAL:
                wait_time = self.MIN_REQUEST_INTERVAL - elapsed
                _LOGGER.debug("Rate limiting: waiting %.2f seconds", wait_time)
                await asyncio.sleep(wait_time)
        
        self._last_request_time = datetime.now().timestamp()
    
    async def _get_cached_address(self, cache_key: str) -> Optional[str]:
        """Get address from cache if not expired."""
        # Load geocoding cache from storage
        data = await storage._load_data(self.hass, self.entry)
        geocoding_cache = data.get("geocoding_cache", {})
        
        cached_entry = geocoding_cache.get(cache_key)
        if not cached_entry:
            return None
        
        # Check expiry
        cached_time = datetime.fromisoformat(cached_entry.get("cached_at", ""))
        expiry = cached_time + timedelta(days=self.CACHE_EXPIRY_DAYS)
        
        if datetime.now() > expiry:
            _LOGGER.debug("Cache expired for %s", cache_key)
            return None
        
        return cached_entry.get("address")
    
    async def _cache_address(self, cache_key: str, address: str) -> None:
        """Cache geocoding result."""
        data = await storage._load_data(self.hass, self.entry)
        
        if "geocoding_cache" not in data:
            data["geocoding_cache"] = {}
        
        data["geocoding_cache"][cache_key] = {
            "address": address,
            "cached_at": datetime.now().isoformat(),
        }
        
        await storage._save_data(self.hass, self.entry, data)
    
    async def clear_cache(self) -> int:
        """
        Clear geocoding cache.
        
        Returns:
            Number of entries cleared
        """
        data = await storage._load_data(self.hass, self.entry)
        cache_size = len(data.get("geocoding_cache", {}))
        
        data["geocoding_cache"] = {}
        await storage._save_data(self.hass, self.entry, data)
        
        _LOGGER.info("Cleared %d geocoding cache entries", cache_size)
        return cache_size
    
    async def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        data = await storage._load_data(self.hass, self.entry)
        geocoding_cache = data.get("geocoding_cache", {})
        
        now = datetime.now()
        removed = 0
        
        for cache_key in list(geocoding_cache.keys()):
            cached_entry = geocoding_cache[cache_key]
            cached_time = datetime.fromisoformat(cached_entry.get("cached_at", ""))
            expiry = cached_time + timedelta(days=self.CACHE_EXPIRY_DAYS)
            
            if now > expiry:
                del geocoding_cache[cache_key]
                removed += 1
        
        if removed > 0:
            data["geocoding_cache"] = geocoding_cache
            await storage._save_data(self.hass, self.entry, data)
            _LOGGER.info("Removed %d expired geocoding cache entries", removed)
        
        return removed
