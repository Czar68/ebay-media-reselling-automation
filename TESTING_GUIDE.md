# Testing Guide

## When to Test

✅ **Test NOW** - Run these tests immediately after deployment

## Pre-Deployment Checklist

Before running any tests, verify these prerequisites:

1. eBay credentials are set in Render environment:
   ```bash
   EBAY_APP_ID=your_client_id
   EBAY_CERT_ID=your_client_secret
   EBAY_DEV_ID=your_user_id
   ```

2. Airtable API key configured:
   ```bash
   AIRTABLE_API_KEY=your_token
   AIRTABLE_BASE_ID=your_base_id
   ```

3. Telegram bot token (if using alerts):
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## Test 1: Health Check (5 minutes)

**Purpose:** Verify service is running and responding

### Command:
```bash
curl -v https://ebay-media-reselling-automation.onrender.com/health
```

### Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T14:00:00Z",
  "version": "1.0.0"
}
```

### Success Criteria:
- HTTP 200 status
- Response time < 500ms
- All services responsive

---

## Test 2: Rate Limiter Test (10 minutes)

**Purpose:** Verify rate limiting is enforced

### Commands:

#### Test 1: Normal Request (should succeed)
```bash
curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

Expected: HTTP 200

#### Test 2: Rapid Fire Requests (test rate limit)
```bash
for i in {1..51}; do
  curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
    -H "Content-Type: application/json" \
    -d '{"test": "data'}' \
    -w "Request $i: %{http_code}\n" -o /dev/null -s
  sleep 0.1
done
```

Expected:
- First 50 requests: HTTP 200
- Request 51+: HTTP 429 (Too Many Requests)
- Response header includes `Retry-After: XX` seconds

---

## Test 3: Webhook Security Test (10 minutes)

**Purpose:** Verify webhook validation and sanitization

### Test 1: Invalid Content-Type
```bash
curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
  -H "Content-Type: text/plain" \
  -d 'invalid'
```

Expected: HTTP 400, error: "Invalid content type"

### Test 2: Missing JSON
```bash
curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
  -H "Content-Type: application/json" \
  -d 'not json'
```

Expected: HTTP 400, error: "Invalid JSON"

### Test 3: Valid JSON with dangerous input
```bash
curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
  -H "Content-Type: application/json" \
  -d '{"message": "<script>alert(xss)</script>"}'
```

Expected: HTTP 200 but script tags removed in processing

---

## Test 4: Shipping Calculator Test (10 minutes)

**Purpose:** Verify weight-based shipping calculations

### Test via Python:
```python
from shipping_calculator import ShippingCalculator

calc = ShippingCalculator()

# Test 1: DVD (typical 4-6 oz)
cost, details = calc.calculate_cost('media_mail', weight_oz=5.0)
print(f"DVD Media Mail: ${cost}")
assert cost == 4.47, f"Expected 4.47, got {cost}"

# Test 2: Heavy item (12 oz)
cost, details = calc.calculate_cost('media_mail', weight_oz=12.0)
print(f"Heavy Media Mail: ${cost}")
assert cost == 4.97, f"Expected 4.97 (4.47 + 0.50), got {cost}"

# Test 3: Box set (24 oz)
cost, details = calc.calculate_cost('ground_advantage', weight_oz=24.0)
print(f"Boxset Ground: ${cost}")
assert cost == 5.75, f"Expected 5.75 (5.25 + 0.50), got {cost}"

print("✅ All shipping tests passed!")
```

### Expected Results:
- 0-16 oz: Base rate + $0.00
- 16-32 oz: Base rate + $0.50
- 32-48 oz: Base rate + $1.00
- 48-64 oz: Base rate + $1.50
- 64+ oz: Base rate + $2.00+

---

## Test 5: eBay API Integration (15 minutes)

**Purpose:** Verify eBay API authentication and endpoints

### Prerequisites:
- eBay sandbox or production credentials
- Test UPC codes

### Test Script:
```python
import requests
import os

APP_ID = os.getenv('EBAY_APP_ID')
CERT_ID = os.getenv('EBAY_CERT_ID')

# Test 1: Get OAuth token
response = requests.post(
    'https://api.ebay.com/identity/v1/oauth2/token',
    auth=(APP_ID, CERT_ID),
    data={
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope/buy.browse.readonly'
    }
)

if response.status_code != 200:
    print(f"❌ OAuth failed: {response.text}")
    exit(1)

token = response.json()['access_token']
print(f"✅ Got OAuth token")

# Test 2: Search by UPC
upc = '012345678901'  # Replace with real UPC
response = requests.get(
    'https://api.ebay.com/buy/browse/v1/item_summary/search',
    headers={'Authorization': f'Bearer {token}'},
    params={
        'q': upc,
        'filter': 'conditions:[Used]',
        'limit': 10
    }
)

if response.status_code == 200:
    results = response.json()['itemSummaries']
    print(f"✅ Found {len(results)} items for UPC {upc}")
    if results:
        print(f"   Sample: {results[0]['title']} - ${results[0]['price']['value']}")
else:
    print(f"❌ Search failed: {response.text}")
```

---

## Test 6: End-to-End Telegram Alert (10 minutes)

**Purpose:** Verify Telegram notifications work

### Manual Test:
```python
import requests
import os

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

response = requests.post(
    f'https://api.telegram.org/bot{token}/sendMessage',
    json={
        'chat_id': chat_id,
        'text': '✅ Test: eBay Media Reselling Bot is working!'
    }
)

if response.status_code == 200:
    print("✅ Telegram alert sent successfully")
else:
    print(f"❌ Telegram failed: {response.text}")
```

### Expected:
- Message appears in Telegram chat
- Contains "Test: eBay Media Reselling Bot is working!"

---

## Test 7: Load Test (Optional, 15 minutes)

**Purpose:** Verify performance under load

### Using Apache Bench:
```bash
ab -n 100 -c 10 https://ebay-media-reselling-automation.onrender.com/health
```

### Expected:
- Requests/sec > 10
- Mean response time < 1000ms
- Failed requests = 0

---

## Monitoring During Tests

### Watch Render Logs:
```bash
# In Render dashboard or via curl:
curl "https://api.render.com/v1/services/srv-d5imev75r7bs73bmjdb0/events" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -s | jq '.[] | select(.level=="error")'
```

### Check Resource Usage:
- CPU: Should stay < 50%
- Memory: Should stay < 200MB
- Disk: Not a concern on Render

---

## Test Result Reporting

After running all tests, report:

```markdown
## Test Summary - [DATE]

| Test | Status | Time | Notes |
|------|--------|------|-------|
| Health Check | ✅ | <500ms | API responsive |
| Rate Limiter | ✅ | 2min | 429 after 50 req |
| Webhook Security | ✅ | 5min | Sanitization works |
| Shipping Calc | ✅ | 3min | Surcharges correct |
| eBay API | ⏳ | TBD | Pending OAuth |
| Telegram | ⏳ | TBD | Pending setup |
| Load Test | ✅ | 10min | >10 req/sec |

**Conclusion:** Ready for production ✅
```

---

## Troubleshooting

### Rate Limiter Not Working?
- Check Render logs: `No rate limiting configured`
- Verify imports in app.py
- Restart service

### eBay API Timeouts?
- Check network: `curl ipinfo.io`
- Verify credentials in Render env vars
- Test OAuth manually (see Test 5)

### Webhook Validation Failing?
- Check Content-Type header
- Validate JSON syntax: `python -m json.tool`
- Check payload size < 100MB

---

## Next: Production Deployment

Once all tests pass:

1. ✅ All tests green
2. ✅ Render logs clean
3. ✅ No performance issues
4. ✅ Telegram alerts working

**Then proceed to:**
- [ ] Enable Make.com scenario
- [ ] Add test item to Airtable
- [ ] Monitor for 24 hours
- [ ] Scale up if needed
