# eBay API Integration Guide

## Overview

This guide maps the current Selenium-based eBay scraping to the official eBay APIs, enabling production-ready pricing lookups without browser automation.

## Current State vs. Future State

**Current (Selenium + BeautifulSoup):**
- Browser automation to load eBay search results
- HTML parsing to extract price, condition, sold listings
- Fragile to UI changes, rate limited
- Slow (5-15 seconds per query)

**Future (eBay Browse API):**
- Direct API calls with authentication
- Structured JSON responses
- 100 calls/hour rate limit (sufficient for MVP)
- Fast (<500ms per query)
- Production-ready

---

## eBay Browse API Mapping

### 1. Search Items by UPC/Keyword

**Endpoint:** `GET https://api.ebay.com/buy/browse/v1/item_summary/search`

**Current Selenium Flow:**
```python
# barcode_intake.py: scan_upc() -> parse_ebay_prices()
# Navigates to: https://www.ebay.com/sch/i.html?_nkw=UPC
# Extracts: title, price, condition, sold status
```

**Replacement eBay API Flow:**
```python
def search_items_by_upc(upc: str, 
                        condition: str = "Used",
                        country: str = "US",
                        limit: int = 20) -> List[ItemSummary]:
    """
    Search for items by UPC/keyword.
    
    Args:
        upc: UPC code or keyword
        condition: "Used", "New", or "NotSpecified"
        country: Country code (US only for MVP)
        limit: Max results (1-200, default 20)
    
    Returns:
        List of ItemSummary objects with price, condition, seller info
    """
    params = {
        "q": upc,
        "filter": f"conditions:{condition}",
        "limit": limit,
        "sort": "newlyListed"  # Sort by recently listed
    }
    
    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=_get_auth_headers(),
        params=params,
        timeout=10
    )
    
    return response.json()["itemSummaries"]
```

### 2. Get Item Details

**Endpoint:** `GET https://api.ebay.com/buy/browse/v1/item/{itemId}`

Use this to get full details for a specific item (pricing history, shipping, returns policy).

```python
def get_item_details(item_id: str) -> ItemDetails:
    """
    Fetch complete item details for pricing and shipping analysis.
    """
    response = requests.get(
        f"https://api.ebay.com/buy/browse/v1/item/{item_id}",
        headers=_get_auth_headers(),
        timeout=10
    )
    
    return response.json()
```

### 3. Get Shipping Estimates

**Endpoint:** `GET https://api.ebay.com/buy/browse/v1/item/{itemId}/shipping_details`

**Use Case:** Get real-time shipping rates instead of hardcoded $4.47 / $5.25.

```python
def get_shipping_estimates(item_id: str, postal_code: str = "75001") -> ShippingEstimate:
    """
    Get real-time shipping cost estimates.
    
    Args:
        item_id: eBay item ID
        postal_code: Destination postal code (test with 75001)
    
    Returns:
        ShippingEstimate with cost and delivery timeframe
    """
    response = requests.get(
        f"https://api.ebay.com/buy/browse/v1/item/{item_id}/shipping_details",
        headers=_get_auth_headers(),
        params={"from_postal_code": postal_code},
        timeout=10
    )
    
    return response.json()
```

---

## Authentication Strategy

### Option A: Application Access Token (Recommended for MVP)

**Your Current Setup:**
- `EBAY_APP_ID` (Client ID)
- `EBAY_CERT_ID` (Client Secret)
- `EBAY_DEV_ID` (User ID)

**Get OAuth2 App Token:**

```python
def get_oauth_token():
    """
    Get OAuth2 application access token for Browse API.
    
    Token expires in ~2 hours; cache and refresh as needed.
    """
    response = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        auth=(EBAY_APP_ID, EBAY_CERT_ID),
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope/buy.browse.readonly"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        token_data = response.json()
        return {
            "access_token": token_data["access_token"],
            "expires_in": token_data["expires_in"],
            "timestamp": time.time()
        }
    else:
        raise Exception(f"Auth failed: {response.text}")
```

### Option B: User Consent Token (For Selling API in Phase 2)

Defer this until you need to list items via API. Browse API (read-only) uses Option A.

---

## Response Shape Examples

### ItemSummary (from /item_summary/search)

```json
{
  "itemId": "v1|123456789012|0",
  "title": "XBOX ONE GAME - HALO 5 - DISC ONLY - TESTED",
  "price": {
    "value": "14.99",
    "currency": "USD"
  },
  "condition": "Used",
  "conditionId": "3000",
  "itemWebUrl": "https://www.ebay.com/itm/123456789012",
  "itemLocation": {
    "city": "Austin",
    "stateOrProvince": "TX",
    "country": "US"
  },
  "seller": {
    "username": "seller_name",
    "feedbackScore": 1250,
    "feedbackPercentage": "99.8"
  },
  "soldQuantity": 5,
  "buyingOptions": ["FIXED_PRICE"],
  "image": {
    "imageUrl": "https://i.ebayimg.com/..."
  },
  "epid": "123456789"
}
```

### Mapping to price_calculator.py

**Current code:**
```python
# price_calculator.py
median_price = extract_from_selenium_parse()
list_price = calculate_list_price(median_price, 0.10)  # +10% markup
```

**Updated code:**
```python
# price_calculator.py
results = search_items_by_upc(upc, condition="Used")
prices = [float(item["price"]["value"]) for item in results]
median_price = statistics.median(prices)
list_price = calculate_list_price(median_price, 0.10)
```

---

## Implementation Checklist

### Phase 1: Basic Integration

- [ ] Create `ebay_api_wrapper.py` module
  - [ ] OAuth2 token management with caching
  - [ ] `search_items_by_upc()` function
  - [ ] Error handling for rate limits, timeouts, invalid UPCs
  - [ ] Fallback to Selenium if API fails

- [ ] Update `price_calculator.py`
  - [ ] Replace Selenium call with `search_items_by_upc()`
  - [ ] Test with 10-20 UPCs from your inventory
  - [ ] Verify prices match manual spot checks

- [ ] Test on Render staging
  - [ ] Confirm `EBAY_APP_ID`, `EBAY_CERT_ID` are set
  - [ ] Run `/health` and `/status` endpoints
  - [ ] Hit pricing endpoint with test UPC

### Phase 2: Advanced Features (Post-MVP)

- [ ] Add `get_shipping_estimates()` for real-time rates
- [ ] Cache results (24-hour TTL for UPCs)
- [ ] Implement Selling API for auto-listing

---

## Rate Limits & Quotas

**Browse API (Read-Only):**
- 100 calls/hour per application
- 10,000 calls/day per application
- Sufficient for MVP (scanning 50-100 items = ~150 API calls)

**Strategy:** Implement exponential backoff if 429 (Rate Limit) is hit.

---

## Environment Variables

Ensure these are set in Render Dashboard:

```
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_client_secret
EBAY_DEV_ID=your_user_id
EBAY_ENVIRONMENT=PRODUCTION  # or "SANDBOX" for testing
```

Sandbox URLs (for testing):
```
https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search
https://api.sandbox.ebay.com/identity/v1/oauth2/token
```

---

## Decision: Sandbox vs. Production for MVP

**Recommendation:** Use PRODUCTION directly.

- Sandbox has limited listings and less realistic pricing.
- Browse API (read-only) is safe; you're not modifying eBay data.
- Your current Selenium is already hitting production.

**Backup Plan:** If you see odd pricing, can quickly switch to Sandbox for diagnostic testing.

---

## Next Steps

1. **Confirm:** Sandbox vs. Production choice for MVP.
2. **Build:** `ebay_api_wrapper.py` with auth and search function.
3. **Test:** Run 20 UPCs, compare results to Selenium baseline.
4. **Deploy:** Update Render and verify `/status` endpoint.
5. **Monitor:** Track API latency and error rates for 48 hours.
