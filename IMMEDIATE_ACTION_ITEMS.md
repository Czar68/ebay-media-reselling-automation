# Immediate Action Items - Priority Fixes & Quick Wins

**Date Created**: January 21, 2026
**Priority Level**: CRITICAL → HIGH → MEDIUM
**Est. Time to Complete**: 8-12 hours total

---

## 🔴 CRITICAL - Fix Before Next Run

### 1. Test eBay Research Module for Bot Detection

**Issue**: Selenium headless browser may be blocked by eBay
**Current Status**: Unclear if working in production
**Action**: 
```bash
# Run in local PowerShell at C:\Users\Media-Czar Desktop\ebay-media-reselling-automation
python ebay_research.py "0012569859324" dvd --upc
```

**What to Watch For**:
- If you get 429 error → eBay is blocking us
- If you get timeout → May be proxy/connection issue
- If you get pricing data → SUCCESS!

**If Blocked (429 Error)**:
- Add delays: `time.sleep(random.uniform(3, 7))` between requests
- Rotate user agents
- Consider: cheap proxy service ($20-50/month)

**Time Estimate**: 30 mins

---

### 2. Verify Airtable Integration After UPC Changes

**Issue**: Updated UPC search may have broken integration
**Current Status**: Last tested 3 hours ago
**Action**:
1. Go to your Airtable base: appN23V9vthSoYGe6
2. Create a test record with:
   - UPC: `0012569859324` (DVD)
   - Condition: Acceptable
   - Webhook: Trigger Make.com scenario
3. Watch Render logs for errors:
   ```
   https://dashboard.render.com/web/srv-d5imev75r7bs73bmjdb0/logs?r=1h
   ```

**Success Criteria**:
- ✅ Record updates with pricing data
- ✅ No 400/500 errors in Flask logs
- ✅ Pricing = (Sale Price + Shipping) calculation works

**If Fails**:
- Check error message in Render logs
- Review most recent commit: `ff099d3` (UPC changes)
- Revert if necessary: `git revert ff099d3`

**Time Estimate**: 45 mins

---

### 3. Document Current Airtable Performance

**Issue**: Don't know if Airtable is bottleneck
**Action**:
1. Test batch operations (should fail currently)
   ```bash
   # Create test script in PowerShell
   python -c "
   from barcode_intake import IntakeWorkflow
   wf = IntakeWorkflow()
   for i in range(50):
       result = wf.process_item(f'0012569859324')
       print(f'Item {i}: {result[\"status\"]}')
   "
   ```
2. Time how long 50 items take
3. Note any rate limit errors (429 from Airtable)

**Expected Result**: Should take ~5-10 minutes for 50 items
**If Slower**: Airtable batch operations need optimization

**Time Estimate**: 30 mins

---

## 🟡 HIGH PRIORITY - Do This Week

### 4. Add Request Rate Limiting to ebay_research.py

**Why**: Prevent eBay from blocking us
**Effort**: 1-2 hours
**Steps**:

1. Add to requirements.txt:
   ```
   ratelimit==2.2.1
   ```

2. Update in PowerShell:
   ```powershell
   pip install -r requirements.txt
   git add requirements.txt
   ```

3. Create new file: `ebay_research_rate_limited.py`
   ```python
   from ratelimit import limits, RateLimitException
   import time
   import random
   
   @limits(calls=2, period=60)  # 2 requests per minute
   def search_ebay_safe(self, query, is_upc):
       # Add random delays
       delay = random.uniform(3, 7)
       time.sleep(delay)
       # Call original search
       return self.search_ebay_sold_listings(query, 'dvd', is_upc=is_upc)
   ```

4. Test:
   ```bash
   python ebay_research.py "0012569859324" dvd --upc
   # Should pause 3-7 seconds before search
   ```

5. Commit:
   ```bash
   git add ebay_research_rate_limited.py
   git commit -m "Add rate limiting to prevent eBay bot detection"
   git push
   ```

**Time Estimate**: 1.5 hours

---

### 5. Create Error Recovery in barcode_intake.py

**Why**: Failed items currently crash workflow
**Effort**: 2-3 hours
**Quick Fix**:

```python
# Add to IntakeWorkflow.process_item() method
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def process_item_with_retry(self, barcode, image_url, manual_condition, median_price):
    try:
        # Original logic here
        return self.process_item(barcode, image_url, manual_condition, median_price)
    except Exception as e:
        logger.error(f"Failed processing {barcode}: {str(e)}")
        # Don't crash, return error status
        return {
            'status': 'error',
            'barcode': barcode,
            'error': str(e),
            'retry_count': 3
        }
```

**Add to requirements.txt**:
```
tenacity==8.2.3
```

**Time Estimate**: 2-3 hours

---

## 🟢 MEDIUM PRIORITY - This Month

### 6. Create Redis Caching Layer

**Cost**: $15-30/month with Heroku Redis
**Benefit**: 80% reduction in eBay API calls
**Effort**: 3-4 hours
**Steps**: Follow caching section in FEATURE_ROADMAP_AND_IMPROVEMENTS.md

---

### 7. Implement Batch Processing

**Cost**: Free (code change only)
**Benefit**: Process 100 items in 2 min vs. 50 minutes
**Effort**: 2-3 hours

---

### 8. Add Production Monitoring (Sentry)

**Cost**: $50-100/month
**Benefit**: Error alerts + debugging info
**Effort**: 1.5-2 hours
**Setup**:
1. Create Sentry account
2. Add to Flask:
   ```python
   import sentry_sdk
   sentry_sdk.init("your-sentry-dsn", traces_sample_rate=1.0)
   ```
3. Add to environment variables in Render

---

## Quick Wins (30 mins each)

- [ ] Add package_dimensions constant to config:
  ```python
  PACKAGE_DIMENSIONS = {'length': 10, 'width': 6, 'height': 2}  # inches
  ```

- [ ] Add logging to track API calls:
  ```python
  logger.info(f"eBay API call: {query} - Response time: {time.time()-start:.2f}s")
  ```

- [ ] Create production deployment checklist

- [ ] Document all environment variables needed

---

## Testing Checklist Before Any Deployment

**Before pushing to Render**:

- [ ] Run locally: `python ebay_research.py "0012569859324" dvd --upc`
- [ ] Run locally: `python test_barcode_intake.py`
- [ ] Run locally: `python test_integration.py`
- [ ] Check Airtable for updates
- [ ] Verify Render logs don't show errors
- [ ] Test with 5 items manually
- [ ] Test with 50+ items to find breaking point

---

## Deployment Process

**Safe Deployment**:

1. Make changes locally
2. Test thoroughly (see checklist above)
3. Commit with descriptive message:
   ```bash
   git add .
   git commit -m "fix: Add rate limiting and error recovery"
   git push origin main
   ```
4. Watch Render logs for 5 minutes
5. If errors: `git revert <commit-hash>`
6. If success: Keep monitoring for 24 hours

---

## Questions to Answer This Week

1. **Does eBay research work without blocking?** → RUN TEST #1
2. **Is Airtable the bottleneck?** → RUN TEST #3
3. **How much will rate limiting impact speed?** → Compare before/after
4. **Should we use Redis caching?** → Check if cost/benefit justified
5. **What's acceptable latency for bot detection avoidance?** → Document for future

---

## Success Metrics After This Week

✅ eBay research works reliably (0 bot blocks)
✅ Error recovery prevents crashes
✅ Rate limiting implemented
✅ Can process 50+ items without failure
✅ Airtable integration verified

---

## PowerShell Commands Ready to Copy/Paste

```powershell
# Change to repo directory
cd "C:\Users\Media-Czar Desktop\ebay-media-reselling-automation"

# Test current UPC search
python ebay_research.py "0012569859324" dvd --upc

# Run barcode intake tests
python test_barcode_intake.py

# Run integration tests
python test_integration.py

# Add package dimensions to config
echo 'PACKAGE_DIMENSIONS = {"length": 10, "width": 6, "height": 2}' >> config.py

# Check git status
git status

# Push to GitHub
git add .
git commit -m "[YOUR MESSAGE HERE]"
git push origin main
```

---

## When to Reach Out (Issues You Can't Resolve)

Message me if:
- 🔴 eBay blocks requests (429 errors) - May need proxy service
- 🔴 Airtable consistently failing - May need rate limit adjustment
- 🔴 Don't understand error message in logs
- 🟡 Want to set up Sentry monitoring
- 🟡 Ready to implement Redis caching
- 🟡 Need help debugging parallel processing

---

**Last Updated**: January 21, 2026
**Next Review**: After completing CRITICAL items (Feb 1, 2026)
