"""
Trip Cost Calculator

Phase 2: Cost calculation for trips
- Real fuel costs based on actual consumption
- German tax mileage rates calculation
- Cost comparison and savings analysis
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .trip_models import Trip, TripCategory
from . import storage

_LOGGER = logging.getLogger(__name__)


class TripCostCalculator:
    """Calculates trip costs and tax benefits."""
    
    # German tax mileage rates (as of 2024)
    TAX_RATE_DEFAULT = 0.30  # €/km for first 20 km
    TAX_RATE_LONG_DISTANCE = 0.38  # €/km from 21st km (one-way commute)
    TAX_RATE_THRESHOLD_KM = 20  # km threshold for long distance rate
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize cost calculator."""
        self.hass = hass
        self.entry = entry
    
    async def calculate_trip_costs(
        self,
        trip: Trip,
        fuel_price_per_liter: Optional[float] = None,
    ) -> Trip:
        """
        Calculate costs for a trip.
        
        Updates the trip object with calculated costs:
        - fuel_cost_euros: Real fuel costs
        - tax_mileage_amount: Tax deductible amount
        
        Args:
            trip: Trip object to calculate costs for
            fuel_price_per_liter: Current fuel price in €/l (optional, will use stored price if not provided)
        
        Returns:
            Updated trip object with cost calculations
        """
        # Get configuration
        config = await storage.get_trip_tracking_config(self.hass, self.entry)
        
        # Get custom tax rates if configured
        tax_rate_default = config.get("tax_mileage_rate_default", self.TAX_RATE_DEFAULT)
        tax_rate_long = config.get("tax_mileage_rate_long_distance", self.TAX_RATE_LONG_DISTANCE)
        
        # Calculate real fuel costs
        if trip.fuel_consumed_liters and fuel_price_per_liter:
            trip.fuel_cost_euros = round(
                trip.fuel_consumed_liters * fuel_price_per_liter,
                2
            )
        elif trip.fuel_consumed_liters:
            # Try to get last known fuel price from storage
            last_price = await storage.get_last_price(self.hass, self.entry)
            if last_price:
                trip.fuel_cost_euros = round(
                    trip.fuel_consumed_liters * last_price,
                    2
                )
        
        # Calculate tax mileage amount
        trip.tax_mileage_amount = self._calculate_tax_mileage(
            trip.distance_km,
            tax_rate_default,
            tax_rate_long,
        )
        
        # Update timestamp
        trip.updated_at = datetime.utcnow().isoformat()
        
        return trip
    
    @staticmethod
    def _calculate_tax_mileage(
        distance_km: float,
        tax_rate_default: float = TAX_RATE_DEFAULT,
        tax_rate_long: float = TAX_RATE_LONG_DISTANCE,
    ) -> float:
        """
        Calculate German tax mileage rate.
        
        In Germany, the standard mileage rate is:
        - €0.30/km for the first 20 km (one way)
        - €0.38/km from the 21st km onwards
        
        For commute trips, only one-way distance is considered.
        For business trips, full distance applies.
        
        Args:
            distance_km: Total trip distance in km
            tax_rate_default: Rate for first 20 km
            tax_rate_long: Rate from 21st km onwards
        
        Returns:
            Tax deductible amount in euros
        """
        if distance_km <= 0:
            return 0.0
        
        # For simplicity, we apply the rates to the full distance
        # In reality, commute trips would need special handling
        if distance_km <= TripCostCalculator.TAX_RATE_THRESHOLD_KM:
            amount = distance_km * tax_rate_default
        else:
            # First 20 km at default rate
            amount = TripCostCalculator.TAX_RATE_THRESHOLD_KM * tax_rate_default
            # Remaining km at long distance rate
            remaining_km = distance_km - TripCostCalculator.TAX_RATE_THRESHOLD_KM
            amount += remaining_km * tax_rate_long
        
        return round(amount, 2)
    
    def calculate_cost_comparison(self, trip: Trip) -> dict:
        """
        Compare real costs vs tax mileage rates.
        
        Returns:
            Dictionary with comparison data:
            - real_cost: Actual fuel cost
            - tax_benefit: Tax deductible amount
            - difference: Savings or additional cost
            - savings_percent: Percentage saved (if positive)
        """
        real_cost = trip.fuel_cost_euros or 0.0
        tax_benefit = trip.tax_mileage_amount or 0.0
        additional_costs = trip.additional_costs_euros or 0.0
        
        total_real_cost = real_cost + additional_costs
        
        # Positive difference means savings (tax benefit > real cost)
        difference = tax_benefit - total_real_cost
        
        savings_percent = 0.0
        if tax_benefit > 0:
            savings_percent = round((difference / tax_benefit) * 100, 2)
        
        return {
            "real_fuel_cost": real_cost,
            "additional_costs": additional_costs,
            "total_real_cost": total_real_cost,
            "tax_benefit": tax_benefit,
            "difference": round(difference, 2),
            "savings_percent": savings_percent,
        }
    
    async def calculate_trip_statistics_with_costs(self) -> dict:
        """
        Calculate comprehensive cost statistics for all trips.
        
        Returns:
            Dictionary with aggregated cost statistics
        """
        trips = await storage.get_trips(self.hass, self.entry)
        
        total_real_cost = 0.0
        total_tax_benefit = 0.0
        total_additional_costs = 0.0
        
        business_real_cost = 0.0
        business_tax_benefit = 0.0
        private_real_cost = 0.0
        commute_real_cost = 0.0
        commute_tax_benefit = 0.0
        
        for trip_dict in trips:
            trip = Trip.from_dict(trip_dict)
            
            real_cost = trip.fuel_cost_euros or 0.0
            tax_benefit = trip.tax_mileage_amount or 0.0
            additional = trip.additional_costs_euros or 0.0
            
            total_real_cost += real_cost
            total_tax_benefit += tax_benefit
            total_additional_costs += additional
            
            # Category breakdown
            if trip.category == TripCategory.BUSINESS.value:
                business_real_cost += real_cost
                business_tax_benefit += tax_benefit
            elif trip.category == TripCategory.PRIVATE.value:
                private_real_cost += real_cost
            elif trip.category == TripCategory.COMMUTE.value:
                commute_real_cost += real_cost
                commute_tax_benefit += tax_benefit
        
        total_difference = total_tax_benefit - (total_real_cost + total_additional_costs)
        
        return {
            "total_real_cost": round(total_real_cost, 2),
            "total_additional_costs": round(total_additional_costs, 2),
            "total_combined_cost": round(total_real_cost + total_additional_costs, 2),
            "total_tax_benefit": round(total_tax_benefit, 2),
            "total_difference": round(total_difference, 2),
            "business_real_cost": round(business_real_cost, 2),
            "business_tax_benefit": round(business_tax_benefit, 2),
            "private_real_cost": round(private_real_cost, 2),
            "commute_real_cost": round(commute_real_cost, 2),
            "commute_tax_benefit": round(commute_tax_benefit, 2),
        }
    
    async def update_trip_cost(
        self,
        trip_id: str,
        fuel_price_per_liter: Optional[float] = None,
        additional_costs: Optional[float] = None,
    ) -> bool:
        """
        Update cost calculations for an existing trip.
        
        Args:
            trip_id: Trip ID to update
            fuel_price_per_liter: New fuel price (optional)
            additional_costs: Additional costs like tolls, parking (optional)
        
        Returns:
            True if trip was found and updated, False otherwise
        """
        trips = await storage.get_trips(self.hass, self.entry)
        
        for i, trip_dict in enumerate(trips):
            if trip_dict.get("trip_id") == trip_id:
                trip = Trip.from_dict(trip_dict)
                
                # Update additional costs if provided
                if additional_costs is not None:
                    trip.additional_costs_euros = additional_costs
                
                # Recalculate costs
                trip = await self.calculate_trip_costs(trip, fuel_price_per_liter)
                
                # Update the trip in storage
                await storage.update_trip(self.hass, self.entry, trip_id, trip.to_dict())
                
                _LOGGER.info(
                    "Updated costs for trip %s: fuel=%.2f€, tax=%.2f€",
                    trip_id,
                    trip.fuel_cost_euros or 0.0,
                    trip.tax_mileage_amount or 0.0,
                )
                
                return True
        
        return False
