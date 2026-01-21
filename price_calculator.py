#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Price Calculator Module for eBay Media Reselling

Handles:
- Median price research on eBay via browser automation
- Margin calculations (10% markup on median)
- Shipping cost calculations by media type
- Best Offer pricing strategies
- Minimum acceptable offer floor ($2.75)

SKU Categories:
- UPC-VG: Full item (case, disc, cover art, manual) - 6 oz
- UPC-A: Disc-only (no case, no cover) - 4 oz  
- UPC: New item - 6 oz
"""

import os
import json
import logging
import requests
import urllib.parse
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants - Weights in ounces
WEIGHT_VIDEO_GAME = 6  # Video game full item
WEIGHT_DVD = 5         # DVD (full item with case/cover)
WEIGHT_CD = 5          # CD (full item with case/cover)
WEIGHT_DISC_ONLY = 4   # Any disc without case/cover

# Shipping costs (USPS, media rate included in price)
SHIPPING_METHOD = {
    'video_game': 'Ground Advantage',  # Free shipping
    'dvd': 'Media Mail',
    'music_cd': 'Media Mail'
}

SHIPPING_COST = {
    'video_game': 0.00,  # Free, offer as Ground Advantage
    'dvd': 3.50,         # Media Mail estimate
    'music_cd': 3.50     # Media Mail estimate
}

# Cost of Goods
DEFAULT_COG = 1.00  # Current inventory clearing
MIN_PROFIT_MARGIN = 2.75  # Minimum acceptable profit
MIN_LIST_PRICE = 5.00  # Absolute minimum list price

# Margin requirements
MARGIN_THRESHOLD = 0.80  # 80% of list price must achieve $2.75 goal


class PriceCalculator:
    """Calculate optimal pricing for eBay media listings."""
    
    def __init__(self, media_type: str, condition: str = 'Acceptable', cog: float = DEFAULT_COG):
        """
        Initialize calculator.
        
        Args:
            media_type: 'video_game', 'dvd', or 'music_cd'
            condition: 'Very Good' (full), 'Acceptable' (disc-only), or 'New'
            cog: Cost of goods (default $1.00)
        """
        self.media_type = media_type
        self.condition = condition
        self.cog = cog
        self.median_price = None
        self.research_log = []
        
    def get_weight(self) -> int:
        """Get weight based on media type and condition."""
        if self.condition in ['New', 'Very Good']:
            if self.media_type == 'video_game':
                return WEIGHT_VIDEO_GAME
            else:
                return WEIGHT_DVD if self.media_type == 'dvd' else WEIGHT_CD
        else:  # Acceptable (disc-only)
            return WEIGHT_DISC_ONLY
            
    def get_shipping_cost(self) -> float:
        """Get shipping cost for this item."""
        return SHIPPING_COST.get(self.media_type, 3.50)
        
    def calculate_list_price(self, median_price: float, markup: float = 0.10) -> float:
        """
        Calculate list price as median + markup.
        
        Args:
            median_price: Median price from eBay research
            markup: Markup percentage (default 10%)
            
        Returns:
            List price
        """
        price = median_price * (1 + markup)
        # Ensure minimum
        return max(price, MIN_LIST_PRICE)
        
    def calculate_best_offer_prices(self, list_price: float) -> Dict[str, float]:
        """
        Calculate best offer pricing strategy.
        
        Strategy:
        - Auto-accept: 80% of list price
        - Minimum ask: 70% of list price
        
        Both must exceed minimum profit threshold.
        
        Args:
            list_price: The listing price
            
        Returns:
            Dict with 'auto_accept' and 'minimum' prices
        """
        auto_accept = Decimal(str(list_price * 0.80)).quantize(
            Decimal('0.01'), 
            rounding=ROUND_HALF_UP
        )
        minimum = Decimal(str(list_price * 0.70)).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # Verify margin threshold
        profit_auto = float(auto_accept) - self.cog - self.get_shipping_cost()
        profit_min = float(minimum) - self.cog - self.get_shipping_cost()
        
        if profit_auto < MIN_PROFIT_MARGIN:
            logger.warning(
                f'Auto-accept price ${float(auto_accept):.2f} yields only ${profit_auto:.2f} profit '
                f'(minimum ${MIN_PROFIT_MARGIN:.2f} required)'
            )
            
        if profit_min < MIN_PROFIT_MARGIN:
            logger.warning(
                f'Minimum ask ${float(minimum):.2f} yields only ${profit_min:.2f} profit '
                f'(minimum ${MIN_PROFIT_MARGIN:.2f} required)'
            )
        
        return {
            'auto_accept': float(auto_accept),
            'minimum': float(minimum),
            'profit_auto_accept': profit_auto,
            'profit_minimum': profit_min
        }
        
    def generate_pricing_matrix(self, median_prices: List[float]) -> Dict:
        """
        Generate complete pricing matrix for different scenarios.
        
        Args:
            median_prices: List of median prices at different markup levels
            
        Returns:
            Complete pricing matrix
        """
        matrix = {
            'media_type': self.media_type,
            'condition': self.condition,
            'cog': self.cog,
            'weight_oz': self.get_weight(),
            'shipping_cost': self.get_shipping_cost(),
            'scenarios': []
        }
        
        for markup in [0.05, 0.10, 0.15, 0.20]:
            median = median_prices[0] if median_prices else 0
            list_price = self.calculate_list_price(median, markup)
            offers = self.calculate_best_offer_prices(list_price)
            
            scenario = {
                'markup_percent': int(markup * 100),
                'median_price': median,
                'list_price': round(list_price, 2),
                'best_offers': offers,
                'margin_check': {
                    '80_percent_achieves_min': offers['profit_auto_accept'] >= MIN_PROFIT_MARGIN
                }
            }
            matrix['scenarios'].append(scenario)
            
        return matrix


class EbayResearcher:
    """Research eBay for comparable items to determine median pricing."""
    
    def __init__(self):
        """Initialize eBay researcher."""
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def search_ebay_sold_listings(self, 
                                 query: str, 
                                 category: str,
                                 max_results: int = 50) -> List[Dict]:
        """
        Search eBay sold listings for price research.
        
        Note: This is a stub for actual browser automation with Selenium.
        In production, would use Selenium to:
        1. Navigate to eBay.com
        2. Search for query
        3. Filter to sold items
        4. Extract prices
        5. Calculate median
        
        Args:
            query: Search query (e.g., "Nintendo Switch game")
            category: Category name (video_game, dvd, music_cd)
            max_results: Max items to retrieve
            
        Returns:
            List of sold item dictionaries with prices
        """
        logger.info(f'Researching {category}: {query}')
        
        # Placeholder - would implement actual Selenium automation
        # For now, returns empty list with guidance
        return {
            'status': 'pending_automation',
            'message': 'Requires Selenium browser automation - see PHASE_3_PRICING_STRATEGY.md',
            'query': query,
            'category': category
        }


def build_sku(upc: str, condition: str) -> str:
    """
    Build SKU based on UPC and condition.
    
    Args:
        upc: Product UPC code
        condition: 'New', 'Very Good', or 'Acceptable'
        
    Returns:
        SKU string
    """
    if condition == 'New':
        return upc
    elif condition == 'Very Good':
        return f'{upc}-VG'
    else:  # Acceptable (disc-only)
        return f'{upc}-A'


def main():
    """Demonstrate price calculation."""
    parser = argparse.ArgumentParser(description='eBay Media Price Calculator')
    parser.add_argument('--media-type', default='dvd', 
                       choices=['video_game', 'dvd', 'music_cd'])
    parser.add_argument('--condition', default='Acceptable',
                       choices=['New', 'Very Good', 'Acceptable'])
    parser.add_argument('--cog', type=float, default=1.00)
    parser.add_argument('--median-price', type=float, default=15.00)
    
    args = parser.parse_args()
    
    calc = PriceCalculator(args.media_type, args.condition, args.cog)
    
    logger.info(f'Calculating prices for {args.media_type} ({args.condition})')
    logger.info(f'Cost of goods: ${args.cog:.2f}')
    logger.info(f'Median market price: ${args.median_price:.2f}')
    logger.info(f'Shipping cost: ${calc.get_shipping_cost():.2f}')
    
    # Calculate at 10% markup
    list_price = calc.calculate_list_price(args.median_price, 0.10)
    offers = calc.calculate_best_offer_prices(list_price)
    
    logger.info(f'\nPricing at 10% markup:')
    logger.info(f'  List Price: ${list_price:.2f}')
    logger.info(f'  Auto-Accept: ${offers["auto_accept"]:.2f} (profit: ${offers["profit_auto_accept"]:.2f})')
    logger.info(f'  Minimum Ask: ${offers["minimum"]:.2f} (profit: ${offers["profit_minimum"]:.2f})')
    logger.info(f'  80% of list achieves $2.75 goal: {offers["profit_auto_accept"] >= 2.75}')
    
    # Generate matrix
    matrix = calc.generate_pricing_matrix([args.median_price])
    print('\nPricing Matrix:')
    print(json.dumps(matrix, indent=2))


if __name__ == '__main__':
    main()
