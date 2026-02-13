"""
Trip Tracking Models

Data models for trip tracking (Fahrtenbuch) functionality:
- Trip: Individual trip records
- TripPattern: Recurring trip patterns
- PointOfInterest: Locations of interest

Phase 1: Basic trip data model
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum


class TripCategory(str, Enum):
    """Trip category enumeration."""
    BUSINESS = "business"
    PRIVATE = "private"
    COMMUTE = "commute"


class POIType(str, Enum):
    """Point of Interest type enumeration."""
    HOME = "home"
    WORK = "work"
    GAS_STATION = "gas_station"
    SHOP = "shop"
    PARKING = "parking"
    CUSTOM = "custom"


@dataclass
class Trip:
    """Data model for a single trip."""
    
    trip_id: str
    started_at: str  # ISO 8601 timestamp
    ended_at: Optional[str] = None  # ISO 8601 timestamp
    
    # Distance and odometer
    distance_km: float = 0.0
    odometer_start: Optional[float] = None
    odometer_end: Optional[float] = None
    
    # Fuel data
    fuel_level_start: Optional[float] = None
    fuel_level_end: Optional[float] = None
    fuel_consumed_liters: Optional[float] = None
    
    # Location data (nullable for privacy)
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    
    # Address data (resolved via geocoding)
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    
    # Cost data
    fuel_cost_euros: Optional[float] = None
    tax_mileage_amount: Optional[float] = None
    additional_costs_euros: float = 0.0
    
    # Trip metadata
    purpose: Optional[str] = None
    category: str = TripCategory.PRIVATE.value
    pattern_id: Optional[str] = None
    
    # Privacy
    is_anonymized: bool = False
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert trip to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Trip:
        """Create trip from dictionary."""
        return cls(**data)
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate trip duration in minutes."""
        if not self.ended_at:
            return None
        
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.ended_at)
        return (end - start).total_seconds() / 60
    
    @property
    def is_completed(self) -> bool:
        """Check if trip is completed."""
        return self.ended_at is not None


@dataclass
class TripPattern:
    """Data model for recurring trip patterns."""
    
    pattern_id: str
    name: str
    
    # Location matching (with radius)
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    start_radius_meters: float = 500.0
    
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    end_radius_meters: float = 500.0
    
    # Time constraints
    weekdays: Optional[list[int]] = None  # 0-6 (Monday-Sunday), None = all days
    time_start: Optional[str] = None  # HH:MM format
    time_end: Optional[str] = None  # HH:MM format
    
    # Pattern metadata
    category: str = TripCategory.COMMUTE.value
    is_anonymized: bool = False
    auto_apply: bool = False  # Requires user confirmation first
    
    # Statistics
    match_count: int = 0
    avg_distance_km: float = 0.0
    avg_duration_minutes: float = 0.0
    avg_fuel_consumption: float = 0.0
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert pattern to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> TripPattern:
        """Create pattern from dictionary."""
        return cls(**data)


@dataclass
class PointOfInterest:
    """Data model for points of interest."""
    
    poi_id: str
    name: str
    
    # Location
    latitude: float
    longitude: float
    radius_meters: float = 100.0
    
    # POI metadata
    poi_type: str = POIType.CUSTOM.value
    address: Optional[str] = None
    
    # Statistics
    visit_count: int = 0
    last_visited: Optional[str] = None  # ISO 8601 timestamp
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert POI to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> PointOfInterest:
        """Create POI from dictionary."""
        return cls(**data)


@dataclass
class TripTrackingConfig:
    """Configuration for trip tracking feature."""
    
    # Feature enable/disable
    enabled: bool = False
    privacy_notice_accepted: bool = False
    
    # Trip detection settings
    min_trip_distance_km: float = 0.5
    merge_time_window_minutes: int = 5
    
    # Cost calculation settings
    tax_mileage_rate_default: float = 0.30  # €/km (German standard)
    tax_mileage_rate_long_distance: float = 0.38  # €/km (from 21st km in Germany)
    
    # Data retention
    retention_days: int = 365
    
    # Privacy settings
    anonymization_schedules: list[dict] = field(default_factory=list)
    
    # Geocoding
    geocoding_enabled: bool = True
    geocoding_cache_enabled: bool = True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> TripTrackingConfig:
        """Create config from dictionary."""
        return cls(**data)


@dataclass
class TripStatistics:
    """Statistics for trip tracking."""
    
    total_trips: int = 0
    total_distance_km: float = 0.0
    total_fuel_consumed_liters: float = 0.0
    total_fuel_cost_euros: float = 0.0
    total_additional_costs_euros: float = 0.0
    
    # Category breakdowns
    business_trips: int = 0
    business_distance_km: float = 0.0
    private_trips: int = 0
    private_distance_km: float = 0.0
    commute_trips: int = 0
    commute_distance_km: float = 0.0
    
    # Averages
    avg_distance_km: float = 0.0
    avg_fuel_consumption_per_100km: float = 0.0
    avg_cost_per_km: float = 0.0
    
    # Last updated
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert statistics to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> TripStatistics:
        """Create statistics from dictionary."""
        return cls(**data)
