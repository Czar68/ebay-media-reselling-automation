"""eBay Listing Module - Handles creating and managing eBay listings"""
import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import requests
import json

logger = logging.getLogger(__name__)

class eBayListingError(Exception):
    """Custom exception for eBay listing errors"""
    pass

class eBayLister:
    """Handles eBay listing creation and management"""

    # eBay API endpoints
    SANDBOX_URL = "https://api.sandbox.ebay.com"
    PRODUCTION_URL = "https://api.ebay.com"

    def __init__(self, use_sandbox: bool = True):
        """
        Initialize eBay Lister with tokens from environment variables.
        Tokens should be stored in Render environment variables:
        - EBAY_A_TOKEN: OAuth app token
        - EBAY_C_TOKEN: Client credentials token
        - EBAY_D_TOKEN: Developer token
        """
        self.use_sandbox = use_sandbox
        self.base_url = self.SANDBOX_URL if use_sandbox else self.PRODUCTION_URL
        
        # Read tokens from environment variables (set in Render)
        self.app_token = os.getenv('EBAY_A_TOKEN')
        self.client_token = os.getenv('EBAY_C_TOKEN')
        self.dev_token = os.getenv('EBAY_D_TOKEN')
        
        if not all([self.app_token, self.client_token, self.dev_token]):
            logger.error("Missing eBay tokens in environment variables")
            raise eBayListingError(
                "Missing eBay API credentials. "
                "Please set EBAY_A_TOKEN, EBAY_C_TOKEN, EBAY_D_TOKEN in Render env vars"
            )
        
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self) -> None:
        """Setup default headers for eBay API requests"""
        self.session.headers.update({
            'Authorization': f'Bearer {self.app_token}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        })

    def create_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a listing on eBay.
        
        Args:
            listing_data: Dictionary containing:
                - title: Item title (max 80 chars)
                - description: Item description
                - price: Starting price (float)
                - category: eBay category ID
                - quantity: Number of items
                - media_type: Type of media (video_game, movie, music_cd)
                - condition: Item condition (NEW, USED_LIKE_NEW, USED_GOOD, USED_ACCEPTABLE)
        
        Returns:
            Dictionary with listing details including listing_id
        """
        try:
            if not listing_data.get('title'):
                raise eBayListingError("Title is required")
            if not listing_data.get('price'):
                raise eBayListingError("Price is required")

            # Build eBay API payload
            payload = self._build_listing_payload(listing_data)
            
            # Create listing
            endpoint = f"{self.base_url}/sell/inventory/v1/inventory_item"
            response = self.session.post(endpoint, json=payload)
            
            if response.status_code not in [200, 201]:
                logger.error(f"eBay API error: {response.status_code} - {response.text}")
                raise eBayListingError(f"Failed to create listing: {response.text}")
            
            listing_id = response.json().get('listing_id')
            logger.info(f"Successfully created listing {listing_id}")
            
            return {
                'success': True,
                'listing_id': listing_id,
                'url': self._get_listing_url(listing_id),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error creating eBay listing: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _build_listing_payload(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build eBay API payload from listing data"""
        # Default eBay category IDs for media
        category_map = {
            'video_game': '16738',  # Video Games & Consoles
            'movie': '11116',       # DVDs & Movies
            'music_cd': '14016'     # CDs & Music
        }
        
        media_type = listing_data.get('media_type', 'video_game')
        category = listing_data.get('category', category_map.get(media_type, '16738'))
        
        payload = {
            'title': listing_data.get('title', 'Media Item'),
            'description': listing_data.get('description', ''),
            'price': float(listing_data.get('price', 9.99)),
            'quantity': int(listing_data.get('quantity', 1)),
            'condition': listing_data.get('condition', 'USED_GOOD'),
            'category_id': category,
            'sku': listing_data.get('sku', f"SKU-{datetime.utcnow().timestamp()}"),
            'location': listing_data.get('location', 'Erlanger, KY'),
        }
        
        # Add image URLs if provided
        if listing_data.get('image_urls'):
            payload['image_urls'] = listing_data['image_urls']
        
        return payload

    def _get_listing_url(self, listing_id: str) -> str:
        """Generate eBay listing URL"""
        if self.use_sandbox:
            return f"https://sandbox.ebay.com/itm/{listing_id}"
        return f"https://ebay.com/itm/{listing_id}"

    def update_listing(self, listing_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing eBay listing"""
        try:
            endpoint = f"{self.base_url}/sell/inventory/v1/inventory_item/{listing_id}"
            response = self.session.put(endpoint, json=updates)
            
            if response.status_code not in [200, 204]:
                raise eBayListingError(f"Failed to update listing: {response.text}")
            
            logger.info(f"Successfully updated listing {listing_id}")
            return {'success': True, 'listing_id': listing_id}
        
        except Exception as e:
            logger.error(f"Error updating eBay listing: {str(e)}")
            return {'success': False, 'error': str(e)}

    def end_listing(self, listing_id: str) -> Dict[str, Any]:
        """End an active eBay listing"""
        try:
            endpoint = f"{self.base_url}/sell/inventory/v1/inventory_item/{listing_id}"
            response = self.session.delete(endpoint)
            
            if response.status_code not in [200, 204]:
                raise eBayListingError(f"Failed to end listing: {response.text}")
            
            logger.info(f"Successfully ended listing {listing_id}")
            return {'success': True, 'listing_id': listing_id}
        
        except Exception as e:
            logger.error(f"Error ending eBay listing: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_listing(self, listing_id: str) -> Dict[str, Any]:
        """Get details of an existing listing"""
        try:
            endpoint = f"{self.base_url}/sell/inventory/v1/inventory_item/{listing_id}"
            response = self.session.get(endpoint)
            
            if response.status_code == 404:
                return {'success': False, 'error': 'Listing not found'}
            
            if response.status_code not in [200]:
                raise eBayListingError(f"Failed to get listing: {response.text}")
            
            return {'success': True, 'data': response.json()}
        
        except Exception as e:
            logger.error(f"Error retrieving eBay listing: {str(e)}")
            return {'success': False, 'error': str(e)}


def create_ebay_listing_from_media(media_data: Dict[str, Any], use_sandbox: bool = True) -> Dict[str, Any]:
    """
    Convenience function to create an eBay listing from media data.
    
    Args:
        media_data: Media information dict with fields:
            - title: Product title
            - description: Product description
            - price: Listing price
            - media_type: video_game, movie, or music_cd
            - condition: Item condition
            - image_urls: List of image URLs
        use_sandbox: Use sandbox API (default True)
    
    Returns:
        Dictionary with listing result
    """
    try:
        lister = eBayLister(use_sandbox=use_sandbox)
        result = lister.create_listing(media_data)
        return result
    except Exception as e:
        logger.error(f"Error in create_ebay_listing_from_media: {str(e)}")
        return {'success': False, 'error': str(e)}
