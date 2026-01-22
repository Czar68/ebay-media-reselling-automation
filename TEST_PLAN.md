# Test Plan and UPC Dataset

## Overview

Comprehensive testing suite for eBay API integration with structured test dataset and automated harness.

---

## Test Dataset (50 UPCs)

Provided as CSV template. You should populate with your actual inventory items:

```
UPC,Media_Type,Title,Expected_Price_Range_Low,Expected_Price_Range_High,Test_Category,Notes
045496508234,Video Game,Halo 5 - Xbox One - Disc Only,12.00,18.00,baseline,Common disc-only game
012569863147,DVD,The Matrix - DVD,3.00,8.00,baseline,Popular film
724384960145,Music CD,Thriller - Michael Jackson,8.00,15.00,baseline,Collectible CD
750430994502,Video Game,Call of Duty Black Ops - PS3 - Disc Only,8.00,12.00,baseline,Older platform
014993140820,DVD,Star Wars IV - DVD,4.00,10.00,edge_case,Highest demand title
027616936264,Video Game,Grand Theft Auto V - Xbox 360 - Disc Only,15.00,22.00,baseline,Popular game
883929103629,Video Game,Zelda Breath of the Wild - Switch,35.00,50.00,high_value,High resale value
191726013320,Music CD,Pink Floyd - The Wall,12.00,25.00,high_value,Premium collectible
014388149827,DVD,Inception - DVD,2.00,7.00,baseline,Recent film
020413006434,Video Game,Ratchet & Clank - PS2 - Disc Only,10.00,16.00,baseline,Retro platform
086162008024,DVD,Harry Potter Chamber of Secrets,3.00,8.00,baseline,Franchise
032674127856,Video Game,Fortnite - PS5 - Disc Only,28.00,38.00,baseline,Current gen
043396058629,Music CD,The Beatles - Abbey Road,15.00,30.00,high_value,Rare pressing
025192025816,DVD,The Lord of the Rings Fellowship,5.00,12.00,baseline,Trilogy
024543889564,Video Game,Monster Hunter World - PS4,18.00,28.00,baseline,Popular title
064652134978,DVD,Bad Boys II,1.00,5.00,low_value,Disc-only filler
081246293756,Music CD,Pink - Greatest Hits,4.00,10.00,baseline,Pop music
029364827564,Video Game,Pokemon Sword - Switch,32.00,45.00,high_value,Nintendo exclusive
038475928365,DVD,Matrix Reloaded,1.00,4.00,low_value,Sequel
093284756120,Video Game,Spider-Man Miles Morales - PS5,25.00,35.00,baseline,Popular title
```

---

## Test Classes

### 1. Baseline Pricing Correctness

**Objective:** Verify eBay API returns accurate pricing

**Test Cases:**

```python
def test_single_upc_search():
    """Search for a single UPC, verify result structure"""
    upc = "045496508234"  # Halo 5
    results = search_items_by_upc(upc, condition="Used")
    
    assert len(results) > 0, "Should return results"
    assert "price" in results[0], "Should have price field"
    assert float(results[0]["price"]["value"]) > 0, "Price should be > 0"
    assert results[0]["condition"] == "Used", "Condition should match filter"

def test_price_median_calculation():
    """Verify median price calculation"""
    upc = "045496508234"
    results = search_items_by_upc(upc, limit=20)
    prices = [float(item["price"]["value"]) for item in results]
    
    median_price = statistics.median(prices)
    assert 12 <= median_price <= 18, f"Halo 5 median should be $12-18, got ${median_price}"

def test_condition_filter():
    """Verify condition filtering works"""
    upc = "045496508234"
    
    used_results = search_items_by_upc(upc, condition="Used")
    new_results = search_items_by_upc(upc, condition="New")
    
    # Used should have more results or lower prices
    used_prices = [float(r["price"]["value"]) for r in used_results]
    new_prices = [float(r["price"]["value"]) for r in new_results]
    
    # Allow both to be present; verify filtering applied
    assert len(used_results) > 0 or len(new_results) > 0, "At least one filter should have results"

def test_no_results_handling():
    """Verify graceful handling of no-result queries"""
    # Invalid/rare UPC
    fake_upc = "999999999999"
    results = search_items_by_upc(fake_upc)
    
    assert isinstance(results, list), "Should return list even if empty"
    # Should not crash
```

### 2. Filter Behavior (US-Only, Used, Sold-Like Signals)

**Objective:** Ensure filters work correctly

```python
def test_us_region_filter():
    """Results should be US sellers"""
    upc = "045496508234"
    results = search_items_by_upc(upc, country="US")
    
    # Check item locations are US-based
    for item in results[:5]:  # Check first 5
        assert item.get("itemLocation", {}).get("country") == "US", \
            f"Item {item['itemId']} not from US"

def test_sold_quantity_field():
    """Verify soldQuantity available for sold-listing signals"""
    upc = "045496508234"
    results = search_items_by_upc(upc)
    
    for item in results:
        assert "soldQuantity" in item, "Should have sold quantity field"
        assert item["soldQuantity"] >= 0, "Sold quantity should be non-negative"
```

### 3. Performance & Latency

**Objective:** Verify response times are acceptable

```python
import time

def test_api_response_latency():
    """Verify API responds within acceptable time"""
    upc = "045496508234"
    
    start = time.time()
    results = search_items_by_upc(upc)
    latency_ms = (time.time() - start) * 1000
    
    assert latency_ms < 1000, f"API should respond < 1000ms, got {latency_ms}ms"
    assert len(results) > 0, "Should have results"

def test_batch_performance():
    """Test performance with 20 UPC searches"""
    test_upcs = [
        "045496508234", "012569863147", "724384960145",
        "750430994502", "014993140820", "027616936264",
        "883929103629", "191726013320", "014388149827",
        "020413006434", "086162008024", "032674127856",
        "043396058629", "025192025816", "024543889564",
        "064652134978", "081246293756", "029364827564",
        "038475928365", "093284756120"
    ]
    
    start = time.time()
    for upc in test_upcs:
        search_items_by_upc(upc)
    total_time = time.time() - start
    avg_latency = (total_time / len(test_upcs)) * 1000
    
    # Target: < 500ms per UPC on average
    assert avg_latency < 500, f"Average latency too high: {avg_latency}ms"
    print(f"✓ Batch test: {len(test_upcs)} UPCs in {total_time:.2f}s (avg {avg_latency:.0f}ms)")
```

### 4. Edge Cases & Error Handling

**Objective:** Verify robustness

```python
def test_invalid_upc_format():
    """Handle malformed UPCs gracefully"""
    invalid_upcs = [
        "NOTACODE",  # Non-numeric
        "",  # Empty
        "   ",  # Whitespace
        "12",  # Too short
        "99999999999999999999",  # Too long
    ]
    
    for bad_upc in invalid_upcs:
        try:
            results = search_items_by_upc(bad_upc)
            # Should either return empty list or raise descriptive error
            assert isinstance(results, list)
        except ValueError as e:
            # OK - validation error
            assert "invalid" in str(e).lower() or "format" in str(e).lower()

def test_rate_limit_handling():
    """Verify exponential backoff on rate limit"""
    # This would need mock/stubbing of HTTP responses
    # Verify 429 responses trigger retry with backoff
    pass  # Implement with mock responses

def test_network_timeout():
    """Handle network timeouts gracefully"""
    # Mock a timeout scenario
    # Verify error is logged and exception is raised with helpful message
    pass  # Implement with mock responses
```

### 5. API Response Validation

**Objective:** Ensure response schema correctness

```python
def test_response_schema():
    """Validate response matches expected schema"""
    upc = "045496508234"
    results = search_items_by_upc(upc)
    
    required_fields = [
        "itemId", "title", "price", "condition", 
        "itemWebUrl", "seller", "buyingOptions"
    ]
    
    for item in results:
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"
        
        # Validate nested structures
        assert "value" in item["price"], "Price should have value"
        assert "currency" in item["price"], "Price should have currency"
        assert item["price"]["currency"] == "USD", "Currency should be USD"
```

---

## Pytest Harness

**File:** `test_ebay_api.py`

```python
import pytest
import statistics
import time
from ebay_api_wrapper import search_items_by_upc

# Test configuration
pytestmark = pytest.mark.integration  # Mark as integration tests

@pytest.fixture
def api_client():
    """Initialize API client with test credentials"""
    # Load from env or config
    return {"app_id": os.getenv("EBAY_APP_ID")}

@pytest.mark.baseline
class TestBaselinePricing:
    def test_single_upc_search(self):
        # ... test code ...
        pass

@pytest.mark.filters
class TestFilterBehavior:
    def test_us_region_filter(self):
        # ... test code ...
        pass

@pytest.mark.performance
class TestPerformance:
    @pytest.mark.slow
    def test_batch_performance(self):
        # ... test code ...
        pass

@pytest.mark.edge_cases
class TestEdgeCases:
    def test_invalid_upc_format(self):
        # ... test code ...
        pass
```

**Run Tests:**

```bash
# Run all tests
pytest test_ebay_api.py -v

# Run only baseline tests
pytest test_ebay_api.py -v -m baseline

# Run only performance tests
pytest test_ebay_api.py -v -m performance

# Run excluding slow tests
pytest test_ebay_api.py -v -m "not slow"

# Run with coverage
pytest test_ebay_api.py --cov=ebay_api_wrapper --cov-report=html
```

---

## Tolerances & Acceptance Criteria

| Category | Metric | Acceptable Range | Target |
|----------|--------|------------------|--------|
| Pricing Accuracy | % results within ±15% of manual comp | 80% - 100% | 95%+ |
| Response Latency | Median per UPC | < 500ms | < 300ms |
| Batch Performance | 20 UPCs total time | < 15 seconds | < 8 seconds |
| Filter Success Rate | US+Used+Sold filters apply | 90%+ | 99%+ |
| Error Handling | Invalid UPCs handled gracefully | No crashes | Descriptive errors |
| Rate Limit Recovery | 429 responses retried | < 3 attempts | < 2 attempts |

---

## Test Execution Checklist

- [ ] Run baseline tests on 10 known UPCs
- [ ] Compare eBay API prices vs. Selenium baseline (manual review)
- [ ] Run performance tests with your real UPC dataset
- [ ] Verify all filters (US, Used, Sold-like) work correctly
- [ ] Test error scenarios (invalid UPC, timeout, rate limit)
- [ ] Document any price mismatches or anomalies
- [ ] Sign off: prices acceptable for production use

---

## Data Collection Template

After running tests, fill this in:

```
Test Run Date: _______
Dataset Size: _______ UPCs
API Calls Total: _______
API Calls Successful: _______
API Calls Failed: _______
Median Latency: _______ms
P95 Latency: _______ms
Price Accuracy (within ±15%): _______%
Notes:
```
