# Shipping Pricing Strategy Analysis

## Executive Summary

**Recommendation for MVP: Option C (Hybrid)**
- Use static rates ($4.47 Media Mail, $5.25 Ground Advantage) as default
- Fall back to eBay Shipping API if available and real-time rates are cheaper
- Cap shipping at cost + 20% margin to ensure profitability

---

## Option A: Static Shipping Only (Current)

### Details
- **Media Mail:** $4.47 (flat rate, weight-based)
- **Ground Advantage (USPS):** $5.25 (flat rate)
- **Applied to all items** regardless of actual carrier rates

### Pros
- ✅ Simplest implementation
- ✅ Fast (no API calls needed)
- ✅ Predictable margins
- ✅ No rate fluctuations

### Cons
- ❌ May overshoot real cost (leaving money on the table)
- ❌ May undershoot and reduce margin (rare, but risky)
- ❌ Not competitive if buyers compare to other sellers
- ❌ No flexibility for multi-item bundles

### Financial Impact

**Scenario 1: Single DVD (approx 0.3 lbs)**
- Actual USPS Ground Advantage cost: ~$3.50-4.00
- Your charge: $5.25
- Margin: +$1.25-1.75 per item
- Annual (50 items/month): +$750-1050

**Scenario 2: Video Game Disc (approx 0.2 lbs)**
- Actual cost: ~$3.00-3.50
- Your charge: $5.25
- Margin: +$1.75-2.25

### Best for: MVP launch (simplicity over optimization)

---

## Option B: Real-Time eBay Shipping API

### Details
- Query eBay API for shipping rates on each listing
- Use `GET /buy/browse/v1/item/{itemId}/shipping_details`
- Apply a markup (10-20%) above real cost

### Pros
- ✅ Accurate pricing
- ✅ Maximizes competitiveness
- ✅ Captures carrier rate drops
- ✅ Can negotiate better rates based on volume

### Cons
- ❌ Adds API call overhead (+100-200ms per listing)
- ❌ Requires eBay API authentication
- ❌ Rate fluctuations reduce predictability
- ❌ Complex fallback logic needed if API fails
- ❌ Uses API quota (100 calls/hour)

### Financial Impact

**Same DVD example:**
- eBay API returns: $3.80 actual cost
- You charge: $3.80 × 1.15 = $4.37 (15% markup)
- Margin: +$0.37 per item
- Annual (50 items/month): +$222 (lower than static!)

**BUT:** You're more competitive, may sell faster → higher volume → better ROI

### Best for: Later phases when API integration is mature

---

## Option C: Hybrid (Recommended for MVP)

### Details
- Start with static rates ($4.47, $5.25)
- When eBay Shipping API is integrated:
  - Try to get real rate from API
  - If real rate < static rate: use real rate + 15% margin
  - If API fails or real rate > static: use static rate (safer)
  - Never go below cost + 5% margin

### Pseudo-Code

```python
def calculate_shipping_cost(item_id: str, default_method: str = "GROUND_ADVANTAGE") -> float:
    """
    Hybrid shipping: static fallback with API optimization.
    
    Default rates:
    - MEDIA_MAIL: $4.47
    - GROUND_ADVANTAGE: $5.25
    """
    static_rates = {
        "MEDIA_MAIL": 4.47,
        "GROUND_ADVANTAGE": 5.25
    }
    static_rate = static_rates.get(default_method, 5.25)
    
    try:
        # Try to get real rate from eBay API
        real_cost = get_ebay_shipping_estimate(item_id)
        
        if real_cost is None:
            # API returned no data
            return static_rate
        
        # Calculate markup (15% above cost)
        markup_rate = real_cost * 1.15
        
        # Use markup if cheaper than static, but never below cost + 5%
        min_rate = real_cost * 1.05
        
        return max(min_rate, min(markup_rate, static_rate))
    
    except Exception as e:
        # API call failed; use static rate
        logger.warning(f"Shipping API failed for {item_id}: {e}. Using static rate.")
        return static_rate
```

### Pros
- ✅ Starts simple (uses static by default)
- ✅ Gracefully degrades if API fails
- ✅ Ready to optimize when API is available
- ✅ Never leaves money on table (always at least as good as static)
- ✅ Protects margin (never undercuts cost)

### Cons
- ❌ Slightly more complex logic
- ❌ API overhead when available
- ❌ Requires error handling

### Financial Impact

**Same DVD at $3.80 real cost:**
- Hybrid rate = max($3.80 × 1.05, min($3.80 × 1.15, $5.25)) = min($3.99, $5.25) = **$3.99**
- Better than Option B (more competitive) 
- Better than Option A (still good margin at $3.99 vs. $3.80 cost)

**Breakeven:** If API finds rates that save ≥$0.05 per item, hybrid wins over static

### Best for: MVP with growth path

---

## Implementation Roadmap

### Phase 1 (MVP): Option A + Option C Framework

**Week 1:** 
- [ ] Keep current static rates
- [ ] Add config flag: `SHIPPING_STRATEGY=STATIC` (vs. `HYBRID`)
- [ ] Implement `calculate_shipping_cost()` stub

**Week 2:**
- [ ] Deploy with static-only
- [ ] Verify Airtable writes work
- [ ] Collect 2 weeks of real shipping data

### Phase 2 (After eBay API integration):

**Week 3:**
- [ ] Implement `get_ebay_shipping_estimate()` function
- [ ] Test with 10 known items
- [ ] Compare API rates vs. actual cost
- [ ] Set config: `SHIPPING_STRATEGY=HYBRID`

**Week 4:**
- [ ] Monitor for 1 week
- [ ] Analyze margin impact
- [ ] Decide: keep hybrid or tune markup

---

## Configuration Template

**In your config.py or environment:**

```python
# Shipping Configuration
SHIPPING_STRATEGY = "HYBRID"  # or "STATIC" for MVP
SHIPPING_STATIC_MEDIA_MAIL = 4.47
SHIPPING_STATIC_GROUND_ADVANTAGE = 5.25
SHIPPING_API_MARKUP_PERCENT = 15  # Mark up real cost by 15%
SHIPPING_MIN_MARGIN_PERCENT = 5   # Never go below cost + 5%
SHIPPING_CACHE_TTL_HOURS = 24  # Cache rates for 24 hours
```

**Environment Variables (for Render):**

```
SHIPPING_STRATEGY=STATIC
SHIPPING_STATIC_MEDIA_MAIL=4.47
SHIPPING_STATIC_GROUND_ADVANTAGE=5.25
```

---

## Decision Matrix

| Factor | Static (A) | API (B) | Hybrid (C) |
|--------|-----------|--------|----------|
| **Implementation Time** | 0 hours | 4 hours | 2 hours |
| **API Overhead** | None | +100-200ms | +100-200ms (opt-in) |
| **Margin Safety** | High | Medium | High |
| **Competitiveness** | Medium | High | High |
| **Fallback Logic** | N/A | Complex | Simple |
| **Ready for Production** | Now | Week 3 | Now |

---

## Next Steps

1. **Confirm MVP choice:** Static or Hybrid?
2. **Set static rates:** Approve $4.47 and $5.25 or adjust?
3. **Update price_calculator.py** with chosen strategy
4. **Phase 2:** When eBay API is ready, implement `get_ebay_shipping_estimate()`
