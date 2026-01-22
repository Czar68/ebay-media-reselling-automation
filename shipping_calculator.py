# -*- coding: utf-8 -*-
"""
Shipping Calculator Module

Calculates shipping costs with weight-based adjustments.
Supports static rates with dynamic overrides for heavier items.
"""

from typing import Dict, Optional, Tuple
from enum import Enum


class ShippingMethod(Enum):
    """Supported shipping methods."""
    MEDIA_MAIL = "media_mail"
    GROUND_ADVANTAGE = "ground_advantage"


class ShippingCalculator:
    """Calculates shipping costs with weight-based adjustments."""

    # Base rates (DVD/CD weight typically 4-8 oz)
    BASE_RATES = {
        ShippingMethod.MEDIA_MAIL: 4.47,
        ShippingMethod.GROUND_ADVANTAGE: 5.25,
    }

    # Weight thresholds and surcharges (oz -> additional cost)
    WEIGHT_SURCHARGES = [
        (16, 0.00),     # Up to 16 oz (1 lb): no surcharge
        (32, 0.50),     # 16-32 oz: +$0.50
        (48, 1.00),     # 32-48 oz: +$1.00
        (64, 1.50),     # 48-64 oz: +$1.50 (4 lbs)
        (128, 2.00),    # 64-128 oz: +$2.00 (8 lbs)
        (float('inf'), 3.00),  # 8+ lbs: +$3.00
    ]

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None):
        """Initialize calculator.

        Args:
            custom_rates: Override base rates (e.g., {'media_mail': 4.50})
        """
        self.rates = self.BASE_RATES.copy()
        if custom_rates:
            for method, rate in custom_rates.items():
                method_enum = ShippingMethod(method) if isinstance(method, str) else method
                self.rates[method_enum] = rate

    def calculate_surcharge(self, weight_oz: float) -> float:
        """Calculate weight-based surcharge.

        Args:
            weight_oz: Item weight in ounces

        Returns:
            Surcharge amount
        """
        if weight_oz <= 0:
            return 0.0

        for threshold, surcharge in self.WEIGHT_SURCHARGES:
            if weight_oz < threshold:
                return surcharge

        return self.WEIGHT_SURCHARGES[-1][1]

    def calculate_cost(self, method: str, weight_oz: float = 6.0) -> Tuple[float, Dict]:
        """Calculate total shipping cost.

        Args:
            method: Shipping method ('media_mail' or 'ground_advantage')
            weight_oz: Item weight in ounces (default 6oz for typical CD)

        Returns:
            Tuple of (total_cost, details_dict)
        """
        try:
            method_enum = ShippingMethod(method)
        except ValueError:
            raise ValueError(f"Unknown method: {method}")

        base_rate = self.rates[method_enum]
        surcharge = self.calculate_surcharge(weight_oz)
        total = round(base_rate + surcharge, 2)

        return total, {
            'method': method,
            'base_rate': base_rate,
            'weight_oz': weight_oz,
            'surcharge': surcharge,
            'total': total
        }

    def estimate_for_media_type(self, media_type: str, weight_oz: float = None) -> Dict:
        """Estimate shipping for common media types.

        Args:
            media_type: 'dvd', 'bluray', 'cd', 'vinyl', 'steelbook', 'boxset'
            weight_oz: Override weight estimate

        Returns:
            Dict with estimates for both methods
        """
        # Default weights by media type
        default_weights = {
            'dvd': 4.5,
            'bluray': 4.0,
            'cd': 3.0,
            'vinyl': 6.0,
            'steelbook': 8.0,
            'boxset': 12.0,
        }

        actual_weight = weight_oz or default_weights.get(media_type.lower(), 5.0)

        media_mail_cost, media_mail_details = self.calculate_cost(
            ShippingMethod.MEDIA_MAIL.value,
            actual_weight
        )
        ground_cost, ground_details = self.calculate_cost(
            ShippingMethod.GROUND_ADVANTAGE.value,
            actual_weight
        )

        return {
            'media_type': media_type,
            'estimated_weight_oz': actual_weight,
            'media_mail': media_mail_details,
            'ground_advantage': ground_details,
            'recommended': 'media_mail' if media_mail_cost < ground_cost else 'ground_advantage'
        }

    def bulk_estimate(self, items: list) -> Dict:
        """Estimate shipping for multiple items.

        Args:
            items: List of {'method': str, 'weight_oz': float} dicts

        Returns:
            Dict with individual and total estimates
        """
        estimates = []
        total_cost = 0.0

        for item in items:
            method = item.get('method', 'media_mail')
            weight = item.get('weight_oz', 5.0)
            cost, details = self.calculate_cost(method, weight)
            estimates.append(details)
            total_cost += cost

        return {
            'items': estimates,
            'total_cost': round(total_cost, 2),
            'count': len(items)
        }
