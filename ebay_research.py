#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eBay Market Research Module"""

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
    
    def search_ebay_sold_listings(self, query: str, category: str = 'video_game', max_results: int = 50) -> List[float]:
        try:
            logger.info(f'Searching eBay for: {query}')
            if not self.driver:
                self._setup_driver()
            search_url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
            params = {'_nkw': query, 'LH_Sold': '1', 'LH_Complete': '1', '_sop': '10'}
            param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
            full_url = f"{search_url}?{param_str}"
            logger.info(f'Navigating to: {full_url}')
            self.driver.get(full_url)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.s-item')))
            prices = self._extract_prices(max_results)
            return prices if prices else []
        except TimeoutException:
            logger.error('Timeout waiting for eBay page to load')
            return []
        except Exception as e:
            logger.error(f'Error searching eBay: {str(e)}')
            return []
    
    def _extract_prices(self, max_results: int) -> List[float]:
        prices = []
        try:
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            listings = soup.find_all('div', {'class': 's-item'})
            for listing in listings[:max_results]:
                try:
                    price_elem = listing.find('span', {'class': 's-price'})
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price_clean = price_text.replace('$', '').replace(',', '').strip()
                        if ' to ' in price_clean:
                            price_clean = price_clean.split(' to ')[0].strip()
                        try:
                            price = float(price_clean)
                            if 0.99 < price < 500:
                                prices.append(price)
                        except ValueError:
                            continue
                except Exception:
                    continue
            return prices
        except Exception as e:
            logger.error(f'Error parsing page HTML: {str(e)}')
            return []
    
    def calculate_median_price(self, prices: List[float]) -> Optional[Tuple[float, Dict]]:
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
                'timestamp': datetime.utcnow().isoformat()
            }
            logger.info(f'Price statistics: {stats}')
            return (median, stats)
        except Exception as e:
            logger.error(f'Error calculating statistics: {str(e)}')
            return None
    
    def research_category(self, query: str, category: str = 'video_game') -> Dict:
        logger.info(f'Starting research for: {query} ({category})')
        prices = self.search_ebay_sold_listings(query, category)
        if not prices:
            logger.warning(f'No prices found for: {query}')
            return {'query': query, 'category': category, 'status': 'failed', 'message': 'No sold listings found', 'timestamp': datetime.utcnow().isoformat()}
        result = self.calculate_median_price(prices)
        if result:
            median, stats = result
            research_data = {'query': query, 'category': category, 'status': 'success', 'median_price': median, 'statistics': stats, 'prices_collected': prices[:10], 'timestamp': datetime.utcnow().isoformat()}
            self.research_history.append(research_data)
            self.session_prices[query] = median
            return research_data
        else:
            return {'query': query, 'category': category, 'status': 'failed', 'message': 'Could not calculate statistics', 'timestamp': datetime.utcnow().isoformat()}
    
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

def research_item_pricing(query: str, category: str = 'video_game', headless: bool = True) -> Dict:
    researcher = eBayResearcher(headless=headless)
    try:
        result = researcher.research_category(query, category)
        return result
    finally:
        researcher.cleanup()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        query = sys.argv[1]
        category = sys.argv[2] if len(sys.argv) > 2 else 'video_game'
        result = research_item_pricing(query, category, headless=False)
        import json
        print(json.dumps(result, indent=2))
    else:
        print('Usage: python ebay_research.py "search query" [category]')
        print('Categories: video_game, dvd, music_cd')
