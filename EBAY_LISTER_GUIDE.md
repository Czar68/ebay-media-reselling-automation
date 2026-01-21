# eBay Lister Guide - Complete Setup & Usage

## Overview

The eBay Lister module (`ebay_lister.py`) handles automated listing creation on eBay. It integrates seamlessly with the media identification pipeline to create complete end-to-end automation: **scan → identify → catalog → list on eBay**.

## Features

✅ **Automated Listing Creation** - Creates eBay listings directly from Airtable records
✅ **Multi-Media Support** - Handles video games, movies, and music CDs with appropriate categories
✅ **Environment-Based Auth** - Uses Render environment variables for secure API tokens
✅ **Sandbox/Production** - Supports both sandbox testing and live production
✅ **Error Handling** - Graceful error handling with logging and user feedback
✅ **Smart Pricing** - Configurable pricing with defaults

## Prerequisites

### eBay Requirements
- **eBay Business Account** with Seller Center access
- **eBay API Credentials**:
  - Application Token (OAuth Bearer Token) → `EBAY_A_TOKEN`
  - Client Credentials Token → `EBAY_C_TOKEN`
  - Developer Token → `EBAY_D_TOKEN`

### Environment Setup (Render)

All tokens are stored in Render environment variables (NEVER hardcoded in files):

```
EBAY_A_TOKEN=<your-oauth-token>
EBAY_C_TOKEN=<your-client-credentials-token>
EBAY_D_TOKEN=<your-developer-token>
```

### Airtable Integration
- Base ID: `appN23V9vthSoYGe6`
- Table: `eBay Listings`
- Columns: Title, Description, Price, Media Type, Condition, Quantity, etc.

## Architecture

### Bot Workflow

1. **User sends disc image to Telegram bot**
2. **Image Analysis** - Media analyzer identifies the disc (game/movie/music)
3. **Metadata Lookup** - Queries IGDB/OMDB/MusicBrainz for complete info
4. **Airtable Creation** - Stores record in `eBay Listings` table
5. **eBay Listing** - Creates listing on eBay automatically ← NEW
6. **User Confirmation** - Telegram confirms with listing URL and details

### eBayLister Class

```python
from ebay_lister import eBayLister, create_ebay_listing_from_media

# Initialize with environment tokens
lister = eBayLister(use_sandbox=True)  # True for testing, False for production

# Create listing
listing_data = {
    'title': 'The Legend of Zelda: Breath of the Wild',
    'description': 'Nintendo Switch game - Complete with case and manual',
    'price': 39.99,
    'media_type': 'video_game',  # 'video_game', 'movie', or 'music_cd'
    'condition': 'USED_GOOD',
    'quantity': 1
}

result = lister.create_listing(listing_data)
if result['success']:
    listing_id = result['listing_id']
    url = result['url']
```

## eBay Category Mappings

| Media Type | Category | eBay ID |
|----------|----------|----------|
| Video Games | Video Games & Consoles | 16738 |
| Movies | DVDs & Movies | 11116 |
| Music CDs | CDs & Music | 14016 |

## Bot Integration (bot.py)

After Airtable record creation, bot.py automatically calls eBay lister:

```python
from ebay_lister import create_ebay_listing_from_media

# ... after Airtable record created ...

ebay_listing_data = {
    'title': chosen_title,
    'description': media_record.description,
    'price': media_record.price or 9.99,
    'media_type': media_record.media_type.value,
    'condition': media_record.condition or 'USED_GOOD',
    'quantity': media_record.quantity or 1,
    'sku': record_id  # Use Airtable record ID as SKU
}

ebay_result = create_ebay_listing_from_media(ebay_listing_data, use_sandbox=True)

if ebay_result.get('success'):
    listing_id = ebay_result['listing_id']
    confirmation_text += f"\n💰 eBay Listing Created!\nListing ID: {listing_id}"
else:
    confirmation_text += f"\n⚠️ eBay listing failed: {ebay_result['error']}"
```

## Getting eBay API Tokens

### Step 1: Create Application in eBay DevCenter

1. Go to https://developer.ebay.com/signin
2. Sign in with eBay account (business account preferred)
3. Click "Application Keys" → "Get Production/Sandbox Keys"
4. Copy the **App ID** (Client ID)
5. Copy the **Cert ID** (Client Secret)
6. Copy the **Dev ID** (Developer ID)

### Step 2: Get OAuth Token

1. Use eBay's OAuth token generation tool
2. Scope: `https://api.ebay.com/oauth/api_scope` (basic)
3. Generate token for your seller account
4. Token format: `Bearer <token_string>`

### Step 3: Set Render Environment Variables

1. Go to Render Dashboard
2. Select your service (`ebay-media-reselling-automation`)
3. Click "Environment"
4. Add variables:
   - `EBAY_A_TOKEN`: Your OAuth Bearer token
   - `EBAY_C_TOKEN`: Your Client Credentials token
   - `EBAY_D_TOKEN`: Your Developer ID
5. Save and redeploy

## Sandbox vs Production

### Sandbox (Testing)
```python
lister = eBayLister(use_sandbox=True)
# Listing URL: https://sandbox.ebay.com/itm/{listing_id}
```

### Production (Live)
```python
lister = eBayLister(use_sandbox=False)
# Listing URL: https://ebay.com/itm/{listing_id}
```

## Error Handling

All errors are caught and reported:

- **Missing Tokens** → Error logged, user notified
- **API Failures** → Airtable record saved, eBay failure noted in confirmation
- **Missing Required Fields** → Title and price validation
- **Network Errors** → Graceful fallback with warning message

## Logging

All eBay operations are logged:

```
logger.debug("Creating eBay listing...")        # Start
logger.info(f"eBay listing created: {id}")      # Success
logger.warning(f"eBay listing creation failed") # Warnings
logger.error(f"Error creating eBay listing")    # Errors
```

View logs in Render Dashboard → Logs tab.

## Testing

### Manual Test

```bash
python -c "
from ebay_lister import eBayLister
lister = eBayLister(use_sandbox=True)
result = lister.create_listing({
    'title': 'Test Game',
    'price': 9.99,
    'media_type': 'video_game'
})
print(result)
"
```

### Via Telegram Bot

1. Send disc image to bot
2. Bot will:
   - Analyze image
   - Look up metadata
   - Create Airtable record
   - Create eBay listing
   - Send confirmation with URL

## Common Issues & Solutions

### Missing Tokens
**Error**: `Missing eBay API credentials`
**Solution**: Verify env vars in Render:
```bash
echo $EBAY_A_TOKEN  # Should output token
```

### Auth Failures
**Error**: `Unauthorized (401)`
**Solution**:
- Verify tokens are current (tokens expire)
- Check token format includes `Bearer ` prefix
- Regenerate tokens in eBay DevCenter

### Category Not Found
**Error**: `Invalid category`
**Solution**:
- Verify media_type is 'video_game', 'movie', or 'music_cd'
- Check category IDs in eBay Category Mappings table above

### Rate Limiting
**Error**: `Too many requests (429)`
**Solution**:
- Space out listings (1-2 second delay between requests)
- eBay allows 5,000 calls/hour

## File Structure

```
ebay-media-reselling-automation/
├── ebay_lister.py              # Main eBay listing module
├── bot.py                      # Telegram bot with eBay integration
├── EBAY_LISTER_GUIDE.md        # This file
├── requirements.txt            # All Python dependencies
├── .env.example                # Environment variables template
└── Render deployment           # Auto-deploys on GitHub push
```

## Deployment

Automatically deployed on Render:

1. Push changes to GitHub → `main` branch
2. Render detects changes
3. Installs dependencies from `requirements.txt`
4. Restarts bot service
5. New code live immediately

Enable automatic deployments in Render Dashboard:
- Settings → Auto-Deploy → On (main branch)

## Success Metrics

✅ eBay listing created within 2-3 seconds of image submission
✅ Listing URL sent to user via Telegram
✅ Listing ID stored in Airtable for tracking
✅ Multiple listings per day without errors
✅ Sandbox/production toggle for safe testing

## Next Steps

1. Get eBay API credentials (step-by-step guide above)
2. Set environment variables in Render
3. Test in sandbox mode first
4. Switch to production when confident
5. Monitor logs and adjust pricing/descriptions as needed

## Support

For issues:
1. Check logs in Render Dashboard
2. Verify environment variables are set
3. Test with sandbox mode first
4. Review EBAY_LISTER_GUIDE.md this file

---

**Created**: Phase 2 - eBay Listing Automation
**Status**: ✅ Complete and integrated
**Last Updated**: 2025
