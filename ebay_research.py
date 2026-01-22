#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eBay Market Research Module - Search by UPC for exact matches"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import statistics

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class eBayResearcher:
    BASE_URL = "https://www.ebay.com"
    SEARCH_ENDPOINT = "/sch/i.html"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.session_prices = {}
        self.research_history = []
        
    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        return self.driver
    
    def search_ebay_sold_listings(self, query: str, category: str = 'video_game', max_results: int = 50, is_upc: bool = False) -> List[float]:
        """
        Search eBay US only, used items, sold listings. 
        Extract TOTAL PRICE (sale price + shipping)
        
        Args:
            query: UPC code or keyword search
            category: video_game, dvd, music_cd
            max_results: Number of listings to analyze
            is_upc: If True, treats query as UPC code
        """
        try:
            search_type = "UPC" if is_upc else "Keyword"
            logger.info(f'Searching eBay by {search_type}: {query}')
            logger.info('Filters: US Only, Used, Sold Items')
            
            if not self.driver:
                self._setup_driver()
            
            search_url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
            params = {
                '_nkw': query,
                'LH_Sold': '1',              # Sold items only
                'LH_Complete': '1',          # Completed listings
                '_sop': '10',                # Sort by newest
                'LH_ItemCondition': '3000',  # Used condition
                'LH_PrefLocation': '1'       # US Only
            }
            
            # If UPC, add parameter for exact matching
            if is_upc:
                params['_ssn'] = 'UPC'  # Search by UPC
                logger.info(f'UPC Search - Searching for exact UPC: {query}')
            
            param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
            full_url = f"{search_url}?{param_str}"
            logger.info(f'Navigating to: {full_url}')
            
            self.driver.get(full_url)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.s-item')))
            
            prices = self._extract_total_prices(max_results)
            return prices if prices else []
            
        except TimeoutException:
            logger.error('Timeout waiting for eBay page to load')
            return []
        except Exception as e:
            logger.error(f'Error searching eBay: {str(e)}')
            return []
    
    def _extract_total_prices(self, max_results: int) -> List[float]:
        """Extract TOTAL PRICE (sale price + shipping) from each listing"""
        prices = []
        try:
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            listings = soup.find_all('div', {'class': 's-item'})
            
            for listing in listings[:max_results]:
                try:
                    # Get sale price
                    price_elem = listing.find('span', {'class': 's-price'})
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.get_text(strip=True)
                    price_clean = price_text.replace('$', '').replace(',', '').strip()
                    
                    if ' to ' in price_clean:
                        price_clean = price_clean.split(' to ')[0].strip()
                    
                    try:
                        sale_price = float(price_clean)
                    except ValueError:
                        continue
                    
                    # Get shipping cost
                    shipping_elem = listing.find('span', {'class': 's-shipping'})
                    shipping_cost = 0.0
                    if shipping_elem:
                        shipping_text = shipping_elem.get_text(strip=True).lower()
                        if 'free' in shipping_text:
                            shipping_cost = 0.0
                        else:
                            try:
                                shipping_clean = shipping_text.replace('$', '').replace(',', '').split()[0]
                                shipping_cost = float(shipping_clean)
                            except (ValueError, IndexError):
                                shipping_cost = 0.0
                    
                    # Calculate total price (what buyer paid)
                    total_price = sale_price + shipping_cost
                    
                    # Only include reasonable prices
                    if 0.99 < total_price < 500:
                        prices.append(total_price)
                        logger.debug(f'Found: Sale ${sale_price:.2f} + Shipping ${shipping_cost:.2f} = Total ${total_price:.2f}')
                        
                except Exception as e:
                    logger.debug(f'Error extracting price: {str(e)}')
                    continue
            
            logger.info(f'Extracted {len(prices)} prices from listings')
            return prices
        except Exception as e:
            logger.error(f'Error parsing page HTML: {str(e)}')
            return []
    
    def calculate_median_price(self, prices: List[float]) -> Optional[Tuple[float, Dict]]:
        """Calculate median price and statistics"""
        if not prices or len(prices) < 3:
            logger.warning(f'Insufficient price data: {len(prices)} prices')
            return None
        
        try:
            median = statistics.median(prices)
            mean = statistics.mean(prices)
            stdev = statistics.stdev(prices) if len(prices) > 1 else 0
            
            stats = {
                'median': round(median, 2),
                'mean': round(mean, 2),
                'std_dev': round(stdev, 2),
                'min': round(min(prices), 2),
                'max': round(max(prices), 2),
                'count': len(prices),
                'note': 'Total price = sale price + shipping (what buyers actually paid)',
                'filters': 'US Only, Used condition, Sold items',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f'Price statistics (total paid by buyers): {stats}')
            return (median, stats)
        except Exception as e:
            logger.error(f'Error calculating statistics: {str(e)}')
            return None
    
    def research_category(self, query: str, category: str = 'video_game', is_upc: bool = False) -> Dict:
        """Complete research for a category/item"""
        search_type = "UPC" if is_upc else "Keyword"
        logger.info(f'Starting {search_type} research for: {query} ({category})')
        
        prices = self.search_ebay_sold_listings(query, category, is_upc=is_upc)
        
        if not prices:
            logger.warning(f'No prices found for: {query}')
            return {
                'query': query,
                'category': category,
                'search_type': search_type,
                'status': 'failed',
                'message': 'No sold listings found',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        result = self.calculate_median_price(prices)
        
        if result:
            median, stats = result
            research_data = {
                'query': query,
                'category': category,
                'search_type': search_type,
                'status': 'success',
                'median_price': median,
                'statistics': stats,
                'prices_collected': prices[:10],
                'timestamp': datetime.utcnow().isoformat()
            }
            self.research_history.append(research_data)
            self.session_prices[query] = median
            return research_data
        else:
            return {
                'query': query,
                'category': category,
                'search_type': search_type,
                'status': 'failed',
                'message': 'Could not calculate statistics',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info('Browser closed successfully')
            except Exception as e:
                logger.error(f'Error closing browser: {str(e)}')
            finally:
                self.driver = None
    
    def __del__(self):
        self.cleanup()

def research_item_pricing(query: str, category: str = 'video_game', headless: bool = True, is_upc: bool = False) -> Dict:
    """Convenience function to research an item's pricing (US only, used, sold, includes shipping)"""
    researcher = eBayResearcher(headless=headless)
    try:
        result = researcher.research_category(query, category, is_upc=is_upc)
        return result
    finally:
        researcher.cleanup()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
        category = sys.argv[2] if len(sys.argv) > 2 else 'video_game'
        is_upc = '--upc' in sys.argv
        
        search_type = "UPC" if is_upc else "Keyword"
        print(f'Searching eBay by {search_type}: {query}')
        
        result = research_item_pricing(query, category, headless=False, is_upc=is_upc)
        import json
        print(json.dumps(result, indent=2))
    else:
        print('Usage: python ebay_research.py "search query" [category] [--upc]')
        print('Categories: video_game, dvd, music_cd')
        print('Example UPC search: python ebay_research.py "0012569859324" dvd --upc')
        print('Example Keyword search: python ebay_research.py "Avatar DVD" dvd')

