# Phase 1 MVP Setup Guide

## Overview

This document covers the complete setup of **Phase 1: Python Bot MVP** for the eBay Media Reselling Automation system.

Phase 1 delivers a fully functional Telegram bot that:
- Receives disc images via Telegram
- Analyzes images using Perplexity AI
- Resolves metadata from external databases (IGDB, OMDb, MusicBrainz)
- Automatically catalogues listings to Airtable
- Costs ~$7-15/month to run on Render

## What's Included (Completed)

### Core Python Modules
- **config.py** - Centralized environment variable and feature flag management
- **media_models.py** - Unified record schema for games, movies, and music
- **media_analyzer.py** - Perplexity API integration with stub fallback
- **database_lookup.py** - IGDB, OMDb, MusicBrainz metadata resolution (stubbed)
- **airtable_handler.py** - Airtable API integration with unified field mapping
- **bot.py** - Telegram bot webhook handler with full pipeline orchestration
- **test_flow.py** - Local end-to-end testing without Telegram/APIs

### Infrastructure
- **app.py** - Updated Flask API with Telegram webhook and legacy Airtable support
- **requirements.txt** - All Python dependencies including Telegram, Airtable, Perplexity
- **Procfile** - Render deployment configuration
- **.env.example** - Template for all required environment variables
- **.gitignore** - Already configured (not committed)

## Local Setup (Development)

### Prerequisites
- Python 3.10+
- pip and virtualenv
- Git

### Steps

1. **Clone repository and enter directory**
   ```bash
   git clone https://github.com/Czar68/ebay-media-reselling-automation.git
   cd ebay-media-reselling-automation
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your API keys (see below)
   ```

5. **Test local pipeline (no Telegram/APIs needed)**
   ```bash
   python test_flow.py
   # Output: Full pipeline test with stub data
   ```

## API Keys & Configuration

You need to obtain these keys from the respective services. See `.env.example` for details.

### Required (for Phase 1 MVP)
1. **Telegram Bot Token** - Get from @BotFather on Telegram
2. **Perplexity API Key** - From Perplexity dashboard (for disc image analysis)
3. **Airtable PAT** - Personal Access Token from Airtable account settings

### Optional (for enhanced metadata)
- **OMDb API Key** - For movie metadata lookup (free tier available)
- **IGDB Credentials** - For game metadata via Twitch OAuth (free tier available)
- **MusicBrainz** - No key needed; just configure User-Agent in config

## Render Deployment

### One-time Setup

1. **Create Render account** at https://render.com (free tier available)

2. **Connect GitHub repository**
   - New Web Service
   - Connect your GitHub repo
   - Auto-deploy from main branch

3. **Set Environment Variables in Render**
   - Copy all values from `.env` into Render's Environment section
   - Key environment variables:
     - `TELEGRAM_BOT_TOKEN`
     - `PERPLEXITY_API_KEY`
     - `AIRTABLE_API_KEY`
     - `ENV=production`

4. **Configure Telegram Webhook**
   - After Render service is running, note the URL (e.g., `https://my-service.onrender.com`)
   - Call Telegram's `setWebhook` endpoint:
     ```bash
     curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://my-service.onrender.com/telegram-webhook"
     ```
   - Or set `TELEGRAM_WEBHOOK_URL` in Render env and the app will attempt this on startup

### Verify Deployment

- Health check: `https://my-service.onrender.com/health` should return `{"status": "healthy"}`
- Status: `https://my-service.onrender.com/status` shows which APIs are configured
- Send a photo to your Telegram bot - it should acknowledge receipt

## Usage: Telegram Bot

### Commands
- `/start` - Welcome message and bot information
- `/help` - Detailed usage instructions  
- `/status` - Check which external APIs are ready
- Send a disc photo - Automatic analysis and cataloging

### Flow

1. **User sends photo** → Telegram webhook receives update
2. **Image downloaded** from Telegram file API
3. **Image analyzed** by Perplexity (or stub if no key)
4. **Metadata resolved** from IGDB/OMDb/MusicBrainz (or stubs)
5. **Record created** in Airtable with all extracted data
6. **Confirmation sent** back to user with success status

## Testing

### Without API Keys (Stub Mode)

```bash
python test_flow.py
```

Tests the entire pipeline with mock data. No external services needed.

### With Real APIs

1. Fill `.env` with actual keys
2. Ensure `USE_STUB_ANALYZER=false` and `USE_STUB_LOOKUPS=false` in `.env`
3. Run `test_flow.py` again - will use real APIs
4. Or deploy to Render and test via Telegram bot

### Debugging

- Logs are written to `app.log` (locally) or Render's log viewer
- Check `/status` endpoint to see API readiness
- All requests are logged with `debug_logging.py` utilities

## Troubleshooting

### Bot not responding to photos
- Check Telegram webhook is set correctly: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Verify `TELEGRAM_BOT_TOKEN` is in Render env vars
- Check Render logs for errors

### Image analysis failing
- If stub: check `USE_STUB_ANALYZER` flag
- If real: verify `PERPLEXITY_API_KEY` is set and has sufficient credits
- Try `/status` command to verify Perplexity is ready

### Airtable not updating
- Verify `AIRTABLE_API_KEY` (must be PAT, not legacy API key)
- Check base ID is correct: `appN23V9vthSoYGe6`
- Verify table name is exact: `"eBay Listings"`
- Ensure PAT has read/write access to the base

## Next Steps

### Short Term (This Week)
1. ✅ Set up local environment
2. ✅ Test with `test_flow.py` using stubs
3. ✅ Deploy to Render
4. ✅ Obtain Telegram, Perplexity, Airtable tokens
5. ✅ Configure Telegram webhook
6. ✅ Send first test disc photo via bot
7. ✅ Verify record appears in Airtable

### Phase 2 (Week 4-5)
- Add web dashboard for inventory management
- Implement status filter views
- Add batch processing capability

### Phase 3 (Week 6-8)
- Convert to multi-tenant SaaS architecture
- Add Stripe payment processing
- Implement per-customer API key management
- Scale to Render paid tier

## Architecture Overview

```
Telegram User
      |
      | (sends photo)
      v
Telegram Bot API
      |
      | (webhook POST to)
      v
Render Web Service (app.py)
  ├─ /telegram-webhook (this is you)
  ├─ /webhook/airtable (legacy, still works)
  ├─ /health
  └─ /status
      |
      +─────────────────────┬──────────────────┬────────────────┐
      v                     v                  v                v
   bot.py           media_analyzer.py    database_lookup.py  airtable_handler.py
   (handles         (analyzes images     (resolves metadata   (writes to
    Telegram)       with Perplexity)    from IGDB/OMDb)      Airtable)
```

## Cost Breakdown (Monthly)

- **Render** (basic): $7 (free tier: $0, limited)
- **Perplexity API**: ~$5-10 (depending on image volume)
- **OMDb**: Free tier sufficient
- **IGDB**: Free tier sufficient
- **MusicBrainz**: Free
- **Airtable**: Free tier sufficient
- **Telegram**: Free
- **Total**: $12-20/month for full operation

## Questions or Issues?

Refer to:
- `.env.example` for all configuration options
- `debug_logging.py` for understanding log output
- Individual module docstrings for implementation details
- GitHub Issues for bugs or feature requests

---

**Last Updated**: January 2025
**Phase**: 1 (MVP)
**Status**: ✅ Complete and Ready for Testing
