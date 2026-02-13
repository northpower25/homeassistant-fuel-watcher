"""
Trip Tracker - Trip Detection and Management

Phase 1: Basic trip detection and recording functionality
- Detects trip start/end based on vehicle movement
- Records odometer, fuel level, GPS coordinates
- Manages current trip state
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .trip_models import Trip, TripCategory
from . import storage

_LOGGER = logging.getLogger(__name__)


class TripTracker:
    """Manages trip detection and recording."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize trip tracker."""
        self.hass = hass
        self.entry = entry
        self._last_location = None
        self._last_odometer = None
        self._last_fuel_level = None
    
    async def check_trip_state(
        self,
        odometer: Optional[float],
        fuel_level: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        """
        Check and update trip state based on vehicle data.
        
        This should be called whenever vehicle data updates.
        """
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        
        # Check if trip tracking is enabled
        if not config.get("enabled", False):
            return
        
        current_trip = await storage.get_current_trip(self.hass, self.entry)
        
        # Determine if vehicle is moving (significant location or odometer change)
        is_moving = self._is_vehicle_moving(odometer, latitude, longitude)
        
        if is_moving and not current_trip:
            # Start new trip
            await self._start_trip(odometer, fuel_level, latitude, longitude)
        elif not is_moving and current_trip:
            # End current trip
            await self._end_trip(odometer, fuel_level, latitude, longitude)
        elif is_moving and current_trip:
            # Update ongoing trip
            await self._update_trip(odometer, fuel_level, latitude, longitude)
        
        # Update last known values
        self._last_location = (latitude, longitude) if latitude and longitude else None
        self._last_odometer = odometer
        self._last_fuel_level = fuel_level
    
    def _is_vehicle_moving(
        self,
        odometer: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> bool:
        """
        Determine if vehicle is currently moving.
        
        Uses odometer change or significant GPS movement.
        """
        # If we have odometer data, use that primarily
        if odometer and self._last_odometer:
            # Vehicle is moving if odometer increased by more than 0.1 km
            if odometer > self._last_odometer + 0.1:
                return True
        
        # Check GPS movement if available
        if latitude and longitude and self._last_location:
            last_lat, last_lon = self._last_location
            distance_km = self._calculate_distance(
                last_lat, last_lon, latitude, longitude
            )
            # Vehicle is moving if GPS moved more than 0.1 km
            if distance_km > 0.1:
                return True
        
        return False
    
    async def _start_trip(
        self,
        odometer: Optional[float],
        fuel_level: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        """Start a new trip."""
        trip_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        trip = Trip(
            trip_id=trip_id,
            started_at=now,
            odometer_start=odometer,
            fuel_level_start=fuel_level,
            start_latitude=latitude,
            start_longitude=longitude,
        )
        
        await storage.set_current_trip(self.hass, self.entry, trip.to_dict())
        
        _LOGGER.info(
            "Trip started: %s at odometer %s km",
            trip_id,
            odometer if odometer else "unknown",
        )
    
    async def _update_trip(
        self,
        odometer: Optional[float],
        fuel_level: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        """Update ongoing trip with current data."""
        current_trip_dict = await storage.get_current_trip(self.hass, self.entry)
        if not current_trip_dict:
            return
        
        trip = Trip.from_dict(current_trip_dict)
        
        # Update distance if we have odometer data
        if odometer and trip.odometer_start:
            trip.distance_km = max(0, odometer - trip.odometer_start)
        
        # Update end location (will become final when trip ends)
        trip.end_latitude = latitude
        trip.end_longitude = longitude
        
        # Update fuel data
        trip.fuel_level_end = fuel_level
        if fuel_level and trip.fuel_level_start:
            # Calculate fuel consumed (handling tank refills)
            fuel_diff = trip.fuel_level_start - fuel_level
            if fuel_diff > 0:  # Only record if fuel decreased
                trip.fuel_consumed_liters = fuel_diff
        
        trip.updated_at = datetime.utcnow().isoformat()
        
        await storage.set_current_trip(self.hass, self.entry, trip.to_dict())
    
    async def _end_trip(
        self,
        odometer: Optional[float],
        fuel_level: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> None:
        """End current trip and save it."""
        current_trip_dict = await storage.get_current_trip(self.hass, self.entry)
        if not current_trip_dict:
            return
        
        trip = Trip.from_dict(current_trip_dict)
        
        # Set end data
        trip.ended_at = datetime.utcnow().isoformat()
        trip.odometer_end = odometer
        trip.fuel_level_end = fuel_level
        trip.end_latitude = latitude
        trip.end_longitude = longitude
        
        # Calculate final distance
        if odometer and trip.odometer_start:
            trip.distance_km = max(0, odometer - trip.odometer_start)
        
        # Calculate fuel consumed
        if fuel_level and trip.fuel_level_start:
            fuel_diff = trip.fuel_level_start - fuel_level
            if fuel_diff > 0:
                trip.fuel_consumed_liters = fuel_diff
        
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        min_distance = config.get("min_trip_distance_km", 0.5)
        
        # Only save trip if it meets minimum distance requirement
        if trip.distance_km >= min_distance:
            await storage.add_trip(self.hass, self.entry, trip.to_dict())
            
            # Update statistics
            await self._update_statistics(trip)
            
            _LOGGER.info(
                "Trip ended: %s, distance: %.2f km",
                trip.trip_id,
                trip.distance_km,
            )
        else:
            _LOGGER.debug(
                "Trip discarded (too short): %.2f km < %.2f km",
                trip.distance_km,
                min_distance,
            )
        
        # Clear current trip
        await storage.set_current_trip(self.hass, self.entry, None)
    
    async def _update_statistics(self, trip: Trip) -> None:
        """Update trip statistics after saving a trip."""
        stats = await storage.get_trip_statistics(self.hass, self.entry)
        
        # Update totals
        stats["total_trips"] = stats.get("total_trips", 0) + 1
        stats["total_distance_km"] = stats.get("total_distance_km", 0.0) + trip.distance_km
        
        if trip.fuel_consumed_liters:
            stats["total_fuel_consumed_liters"] = (
                stats.get("total_fuel_consumed_liters", 0.0) + trip.fuel_consumed_liters
            )
        
        if trip.fuel_cost_euros:
            stats["total_fuel_cost_euros"] = (
                stats.get("total_fuel_cost_euros", 0.0) + trip.fuel_cost_euros
            )
        
        if trip.additional_costs_euros:
            stats["total_additional_costs_euros"] = (
                stats.get("total_additional_costs_euros", 0.0) + trip.additional_costs_euros
            )
        
        # Update category breakdowns
        category = trip.category
        if category == TripCategory.BUSINESS.value:
            stats["business_trips"] = stats.get("business_trips", 0) + 1
            stats["business_distance_km"] = (
                stats.get("business_distance_km", 0.0) + trip.distance_km
            )
        elif category == TripCategory.PRIVATE.value:
            stats["private_trips"] = stats.get("private_trips", 0) + 1
            stats["private_distance_km"] = (
                stats.get("private_distance_km", 0.0) + trip.distance_km
            )
        elif category == TripCategory.COMMUTE.value:
            stats["commute_trips"] = stats.get("commute_trips", 0) + 1
            stats["commute_distance_km"] = (
                stats.get("commute_distance_km", 0.0) + trip.distance_km
            )
        
        # Calculate averages
        total_trips = stats["total_trips"]
        if total_trips > 0:
            stats["avg_distance_km"] = stats["total_distance_km"] / total_trips
        
        if stats["total_distance_km"] > 0 and stats.get("total_fuel_consumed_liters", 0) > 0:
            stats["avg_fuel_consumption_per_100km"] = (
                stats["total_fuel_consumed_liters"] / stats["total_distance_km"] * 100
            )
        
        if stats["total_distance_km"] > 0 and stats.get("total_fuel_cost_euros", 0) > 0:
            stats["avg_cost_per_km"] = (
                stats["total_fuel_cost_euros"] / stats["total_distance_km"]
            )
        
        stats["last_updated"] = datetime.utcnow().isoformat()
        
        await storage.set_trip_statistics(self.hass, self.entry, stats)
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        Returns distance in kilometers.
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Earth radius in kilometers
        R = 6371.0
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return distance
