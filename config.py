"""Configuration management for eBay Media Reselling Automation.
Centralized environment variable loading and feature flags.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Flask and API Configuration
ENV = os.getenv('ENV', 'development')
DEBUG = ENV != 'production'
PORT = int(os.getenv('PORT', '5000'))

# External API Keys and Secrets
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

# Airtable Configuration
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appN23V9vthSoYGe6')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'eBay Listings')

# MusicBrainz Configuration (no API key needed, but app identity required)
MUSICBRAINZ_APP_NAME = os.getenv('MUSICBRAINZ_APP_NAME', 'GamesMoviesMusicBot')
MUSICBRAINZ_APP_VERSION = os.getenv('MUSICBRAINZ_APP_VERSION', '0.1.0')
MUSICBRAINZ_CONTACT = os.getenv('MUSICBRAINZ_CONTACT', 'contact@gamesmoviesmusic.com')

# Feature Flags: Use stubs when keys are missing or testing locally
USE_STUB_ANALYZER = os.getenv('USE_STUB_ANALYZER', 'true').lower() == 'true'
USE_STUB_LOOKUPS = os.getenv('USE_STUB_LOOKUPS', 'true').lower() == 'true'

# If API keys are present, override stubs
if PERPLEXITY_API_KEY:
    USE_STUB_ANALYZER = False
if OMDB_API_KEY and IGDB_CLIENT_ID:
    USE_STUB_LOOKUPS = False

# Telegram Webhook Configuration
TELEGRAM_WEBHOOK_PATH = os.getenv('TELEGRAM_WEBHOOK_PATH', '/telegram-webhook')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')  # Set in Render: https://your-service.onrender.com

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# API Rate Limiting (for Phase 3 SaaS)
API_RATE_LIMIT_REQUESTS = int(os.getenv('API_RATE_LIMIT_REQUESTS', '100'))
API_RATE_LIMIT_PERIOD = int(os.getenv('API_RATE_LIMIT_PERIOD', '3600'))  # seconds

def get_config_status():
    """Return a dict showing which external APIs are ready."""
    return {
        'perplexity_ready': bool(PERPLEXITY_API_KEY),
        'telegram_ready': bool(TELEGRAM_BOT_TOKEN),
        'airtable_ready': bool(AIRTABLE_API_KEY),
        'omdb_ready': bool(OMDB_API_KEY),
        'igdb_ready': bool(IGDB_CLIENT_ID and IGDB_CLIENT_SECRET),
        'musicbrainz_ready': True,  # No API key required
        'use_stub_analyzer': USE_STUB_ANALYZER,
        'use_stub_lookups': USE_STUB_LOOKUPS,
        'environment': ENV,
    }
