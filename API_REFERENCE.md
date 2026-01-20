# API Reference

## eBay Media Reselling Automation Flask API

### Base URL
```
https://ebay-media-reselling-automation.onrender.com
```

---

## Endpoints

### 1. POST /webhook/airtable

**Description:**
Main webhook endpoint for processing video game disc images using Perplexity AI. Analyzes disc images to extract metadata and updates Airtable records.

**Authentication:**
None (IP whitelist via Make.com recommended)

**Request Format:**
```json
{
  "record_id": "recABC123XYZ",
  "image_url": "https://airtable-attachments.s3.us-west-2.amazonaws.com/..."
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| record_id | string | Yes | Airtable record ID to update (format: rec[alphanumeric]) |
| image_url | string | Yes | Direct URL to disc image (must be publicly accessible) |

**Response Format (Success - 200):**
```json
{
  "success": true,
  "record_id": "recABC123XYZ",
  "extracted_data": {
    "game_title": "The Legend of Zelda: Breath of the Wild",
    "platform": "Nintendo Switch",
    "upc": "045496590495",
    "publisher": "Nintendo",
    "esrb_rating": "E10+",
    "year": "2017",
    "condition_notes": "Disc pristine, no scratches",
    "disc_art_description": "Link holding Master Sword in landscape setting",
    "ebay_title": "Legend of Zelda Breath of the Wild - Nintendo Switch - Disc Only",
    "website_title": "The Legend of Zelda: Breath of the Wild for Nintendo Switch",
    "keywords": ["zelda", "nintendo switch", "action adventure"]
  },
  "updated_fields": {
    "Title": "Legend of Zelda Breath of the Wild - Nintendo Switch - Disc Only",
    "Status": "Analyzed",
    "UPC/Barcode": "045496590495",
    "Platform": "Nintendo Switch",
    "Notes": "Game: The Legend of Zelda: Breath of the Wild\nPublisher: Nintendo\nYear: 2017\nRating: E10+"
  }
}
```

**Response Format (Error - 400):**
```json
{
  "error": "Missing required fields: record_id and image_url"
}
```

**Response Format (Error - 500):**
```json
{
  "error": "Perplexity API error",
  "details": "Connection timeout after 30 seconds"
}
```

**Status Codes:**

| Code | Meaning | Reason |
|------|---------|--------|
| 200 | Success | Record successfully analyzed and Airtable updated |
| 400 | Bad Request | Missing or malformed required fields |
| 500 | Internal Error | Perplexity API failure, JSON parsing error, or Airtable update failed |

**Rate Limits:**
None (implement at Make.com level)

**Timeout:**
30 seconds per request

**Example cURL:**
```bash
curl -X POST https://ebay-media-reselling-automation.onrender.com/webhook/airtable \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "recABC123XYZ",
    "image_url": "https://example.com/disc-image.jpg"
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "https://ebay-media-reselling-automation.onrender.com/webhook/airtable",
    json={
        "record_id": "recABC123XYZ",
        "image_url": "https://example.com/disc-image.jpg"
    },
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data['extracted_data']['game_title']}")
else:
    print(f"Error: {response.json()['error']}")
```

---

### 2. GET /health

**Description:**
Health check endpoint to verify service is running.

**Authentication:**
None

**Response Format:**
```json
{
  "status": "healthy",
  "service": "ebay-media-reselling-automation"
}
```

**Status Code:**
- 200 OK - Service is healthy

**Example cURL:**
```bash
curl https://ebay-media-reselling-automation.onrender.com/health
```

**Use Cases:**
- Monitoring/alerting systems
- Pre-request validation in Make.com
- Load balancer health checks

---

## Data Models

### Extracted Game Data

This is the structure returned by the Perplexity API when analyzing a disc image.

```typescript
interface GameData {
  game_title: string;           // Exact game title from disc
  platform: string;             // Gaming platform (Switch, PS5, Xbox Series X, etc.)
  upc: string | null;           // UPC/Barcode (numbers only)
  publisher: string;            // Game publisher name
  esrb_rating: string | null;   // ESRB rating (E, E10+, T, M, AO, RP)
  year: string | null;          // Copyright/release year
  condition_notes: string;      // Disc condition assessment
  disc_art_description: string; // Visual description of disc artwork
  ebay_title: string;           // Optimized eBay listing title (<80 chars)
  website_title: string;        // Website product title
  keywords: string[];           // Array of eBay search keywords
}
```

### Airtable Field Mapping

The extracted data is mapped to Airtable fields as follows:

| Airtable Field | Source Data | Type | Notes |
|----------------|-------------|------|-------|
| Title | ebay_title | String | Max 80 characters |
| Notes | Concatenated fields | Text | Game info, publisher, year, rating, keywords |
| Status | Hardcoded | Select | Set to "Analyzed" on successful update |
| UPC/Barcode | upc | String | Numbers only, no spaces |
| UPC | upc | Barcode | Duplicate field for barcode scanning |
| Platform | platform | String | Gaming platform |
| Media Type | Hardcoded | Select | Set to "Video Game" |
| Condition | Hardcoded | Select | Set to "Disc Only" |

---

## Error Handling

### Error Response Structure
```json
{
  "error": "Human-readable error message",
  "details": "Technical details or raw API response"
}
```

### Common Errors

**Missing record_id:**
```json
{"error": "Missing required fields: record_id and image_url"}
```

**Invalid image URL:**
```json
{"error": "Perplexity API error: 400", "details": "Invalid image URL"}
```

**JSON parsing failure:**
```json
{"error": "Could not extract JSON from API response", "details": "...raw response..."}
```

**Airtable update failure:**
```json
{"error": "Airtable update failed: 401", "details": "Invalid API key"}
```

---

## Environment Variables

Required environment variables (set in Render dashboard):

```env
# Perplexity AI API Configuration
PERPLEXITY_API_KEY=pplx_xxxxxxxxxxxxx

# Airtable API Configuration
AIRTABLE_API_KEY=patxxxxxxxxxxxxx
AIRTABLE_BASE_ID=appN23V9vthSoYGe6
AIRTABLE_TABLE_NAME=eBay Listings

# Server Configuration
PORT=5000
```

---

## Integration with Make.com

The webhook is designed to be called from Make.com's HTTP module:

1. **HTTP Module Settings:**
   - URL: `https://ebay-media-reselling-automation.onrender.com/webhook/airtable`
   - Method: POST
   - Content-Type: application/json

2. **Airtable Watch Trigger:**
   - Base: eBay Media Reselling
   - Table: eBay Listings
   - Trigger Field: Last Modified Time
   - Fires every time a record is updated

3. **Request Body Mapping:**
   ```json
   {
     "record_id": "{{1.ID}}",
     "image_url": "{{1.Attachments[1].URL}}"
   }
   ```

4. **Airtable Update Mapping:**
   - Title ← `{{2.extracted_data.ebay_title}}`
   - Status ← "Analyzed"
   - UPC/Barcode ← `{{2.extracted_data.upc}}`
   - Platform ← `{{2.extracted_data.platform}}`

---

## Performance

**Typical Response Times:**
- Service up and running: 1-2 seconds
- Perplexity API processing: 5-20 seconds
- Airtable update: <1 second
- **Total: 6-22 seconds per request**

**Concurrency:**
- Single-instance Flask app
- Handles sequential requests
- For parallel processing, consider upgrading Render tier

**Data Transfer:**
- Average request: ~100 KB
- Average response: ~2 KB
- Make.com usage: ~2 operations per execution

---

## Security Considerations

1. **API Key Protection:**
   - Never commit .env files
   - API keys stored securely in Render dashboard
   - Rotate keys if suspected compromise

2. **Input Validation:**
   - Record IDs validated for format
   - Image URLs must be HTTPS or HTTP
   - No file uploads (only URL-based images)

3. **Rate Limiting:**
   - Implement at Make.com level using scenario scheduling
   - Currently: Every 15 minutes max
   - Prevents API rate limit hits

4. **Webhook Validation:**
   - Consider implementing webhook signature validation
   - Make.com can send HMAC-SHA256 signatures if configured

---

## Deployment

**Platform:** Render.com  
**Runtime:** Python 3.x Flask  
**Build Command:** `pip install -r requirements.txt`  
**Start Command:** `python app.py`  
**Health Check:** GET /health

---

## Changelog

**v1.0 (Current)**
- Initial release
- Perplexity AI disc image analysis
- Airtable integration
- Make.com webhook support
