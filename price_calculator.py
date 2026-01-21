#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Price Calculator Module for eBay Media Reselling"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional
import argparse
from datetime import datetime

try:
    from ebay_research import research_item_pricing
except ImportError:
    research_item_pricing = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WEIGHT_VIDEO_GAME = 6
WEIGHT_DVD = 5
WEIGHT_CD = 5
WEIGHT_DISC_ONLY = 4

SHIPPING_COST = {'video_game': 0.00, 'dvd': 3.50, 'music_cd': 3.50}

DEFAULT_COG = 1.00
MIN_PROFIT_MARGIN = 2.75
MIN_LIST_PRICE = 5.00
MARGIN_THRESHOLD = 0.80

class PriceCalculator:
    """Calculate optimal pricing for eBay media listings."""
    
    def __init__(self, media_type: str, condition: str = 'Acceptable', cog: float = DEFAULT_COG):
        self.media_type = media_type
        self.condition = condition
        self.cog = cog
        self.median_price = None
        self.research_log = []
        
    def get_weight(self) -> int:
        """Get weight based on media type and condition."""
        if self.condition in ['New', 'Very Good']:
            return WEIGHT_VIDEO_GAME if self.media_type == 'video_game' else (WEIGHT_DVD if self.media_type == 'dvd' else WEIGHT_CD)
        return WEIGHT_DISC_ONLY
        
    def get_shipping_cost(self) -> float:
        """Get shipping cost for this item."""
        return SHIPPING_COST.get(self.media_type, 3.50)
        
    def research_median_price(self, search_query: str) -> Optional[float]:
        """Research eBay for comparable items to find median price."""
        if not research_item_pricing:
            logger.error('eBay research module not available')
            return None
        logger.info(f'Researching median price for: {search_query}')
        try:
            result = research_item_pricing(search_query, self.media_type, headless=True)
            if result.get('status') == 'success':
                self.median_price = result.get('median_price')
                self.research_log.append(result)
                logger.info(f'Found median price: ${self.median_price:.2f}')
                return self.median_price
            else:
                logger.warning(f'Research failed: {result.get("message")}')
                return None
        except Exception as e:
            logger.error(f'Error researching median price: {str(e)}')
            return None
    
    def calculate_list_price(self, median_price: float, markup: float = 0.10) -> float:
        """Calculate list price as median + markup."""
        price = median_price * (1 + markup)
        return max(price, MIN_LIST_PRICE)
        
    def calculate_best_offer_prices(self, list_price: float) -> Dict[str, float]:
        """Calculate best offer pricing strategy."""
        auto_accept = Decimal(str(list_price * 0.80)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        minimum = Decimal(str(list_price * 0.70)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        profit_auto = float(auto_accept) - self.cog - self.get_shipping_cost()
        profit_min = float(minimum) - self.cog - self.get_shipping_cost()
        
        if profit_auto < MIN_PROFIT_MARGIN:
            logger.warning(f'Auto-accept price ${float(auto_accept):.2f} yields only ${profit_auto:.2f} profit (minimum ${MIN_PROFIT_MARGIN:.2f} required)')
        if profit_min < MIN_PROFIT_MARGIN:
            logger.warning(f'Minimum ask ${float(minimum):.2f} yields only ${profit_min:.2f} profit (minimum ${MIN_PROFIT_MARGIN:.2f} required)')
        
        return {
            'auto_accept': float(auto_accept),
            'minimum': float(minimum),
            'profit_auto_accept': profit_auto,
            'profit_minimum': profit_min,
            'meets_margin_threshold': profit_auto >= MIN_PROFIT_MARGIN
        }
    
    def generate_pricing_matrix(self, median_price: float) -> Dict:
        """Generate complete pricing matrix for different scenarios."""
        matrix = {
            'media_type': self.media_type,
            'condition': self.condition,
            'cog': self.cog,
            'weight_oz': self.get_weight(),
            'shipping_cost': self.get_shipping_cost(),
            'median_price': median_price,
            'scenarios': []
        }
        
        for markup in [0.05, 0.10, 0.15, 0.20]:
            list_price = self.calculate_list_price(median_price, markup)
            offers = self.calculate_best_offer_prices(list_price)
            scenario = {
                'markup_percent': int(markup * 100),
                'list_price': round(list_price, 2),
                'best_offers': offers,
                'margin_check': {'80_percent_achieves_min': offers['meets_margin_threshold']}
            }
            matrix['scenarios'].append(scenario)
        
        return matrix

def build_sku(upc: str, condition: str) -> str:
    """Build SKU based on UPC and condition."""
    if condition == 'New':
        return upc
    elif condition == 'Very Good':
        return f'{upc}-VG'
    else:
        return f'{upc}-A'

def main():
    """Demonstrate price calculation with eBay research."""
    parser = argparse.ArgumentParser(description='eBay Media Price Calculator')
    parser.add_argument('--media-type', default='dvd', choices=['video_game', 'dvd', 'music_cd'])
    parser.add_argument('--condition', default='Acceptable', choices=['New', 'Very Good', 'Acceptable'])
    parser.add_argument('--cog', type=float, default=1.00)
    parser.add_argument('--search-query', type=str, help='Search query for eBay research')
    parser.add_argument('--median-price', type=float, help='Manual median price (skips eBay research)')
    
    args = parser.parse_args()
    
    calc = PriceCalculator(args.media_type, args.condition, args.cog)
    
    logger.info(f'Calculating prices for {args.media_type} ({args.condition})')
    logger.info(f'
