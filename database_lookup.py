"""External metadata database lookup module.
Provides unified queries to IGDB (games), OMDb (movies), and MusicBrainz (music).
All functions are stubbed for MVP testing; real API calls replace stubs when keys are provided.
"""
import requests
from typing import Dict, Optional, List, Any
from config import OMDB_API_KEY, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET
from config import MUSICBRAINZ_APP_NAME, MUSICBRAINZ_APP_VERSION, MUSICBRAINZ_CONTACT
from config import USE_STUB_LOOKUPS, get_config_status
from debug_logging import setup_debug_logger
from media_models import UnifiedMediaRecord, MediaType

logger = setup_debug_logger()


def lookup_game(
    title: str,
    platform_hint: Optional[str] = None,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Look up a video game in IGDB.

    Returns dict with keys: title, creator (developer), year, upc, external_ids
    """
    if USE_STUB_LOOKUPS or not IGDB_CLIENT_ID:
        return _stub_game_lookup(title, platform_hint, year_hint)

    # Real IGDB lookup would go here
    logger.debug(f"Looking up game: {title}")
    return _stub_game_lookup(title, platform_hint, year_hint)


def lookup_movie(
    title: str,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Look up a movie in OMDb.

    Returns dict with keys: title, creator (director), year, upc, external_ids
    """
    if USE_STUB_LOOKUPS or not OMDB_API_KEY:
        return _stub_movie_lookup(title, year_hint)

    # Real OMDb lookup would go here
    logger.debug(f"Looking up movie: {title}")
    return _stub_movie_lookup(title, year_hint)


def lookup_music(
    title: str,
    creator_hint: Optional[str] = None,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Look up music in MusicBrainz.

    Returns dict with keys: title, creator (artist), year, upc, external_ids
    """
    if USE_STUB_LOOKUPS:
        return _stub_music_lookup(title, creator_hint, year_hint)

    # MusicBrainz doesn't require API key but needs proper User-Agent
    logger.debug(f"Looking up music: {title} by {creator_hint}")
    return _stub_music_lookup(title, creator_hint, year_hint)


def resolve_metadata(
    analyzer_result: Dict[str, Any]
) -> UnifiedMediaRecord:
    """Resolve metadata from image analyzer into unified record.

    Dispatcher that routes to appropriate lookup function based on media_type.
    """
    media_type_str = analyzer_result.get("media_type")
    title_candidates = analyzer_result.get("title_candidates", [])
    year_hint = analyzer_result.get("year_hint")
    platform_hint = analyzer_result.get("platform_hint")
    confidence = analyzer_result.get("confidence", 0.0)
    analyzer_notes = analyzer_result.get("notes", "")

    # Pick best title candidate (first one for now)
    title = title_candidates[0] if title_candidates else "Unknown Title"

    try:
        if media_type_str == "game":
            lookup_result = lookup_game(title, platform_hint, year_hint)
            media_type = MediaType.GAME
        elif media_type_str == "movie":
            lookup_result = lookup_movie(title, year_hint)
            media_type = MediaType.MOVIE
        elif media_type_str == "music":
            lookup_result = lookup_music(title, None, year_hint)
            media_type = MediaType.MUSIC
        else:
            # Default to game if unclear
            lookup_result = lookup_game(title, platform_hint, year_hint)
            media_type = MediaType.GAME

        # Create unified record
        record = UnifiedMediaRecord(
            title=lookup_result.get("title", title),
            media_type=media_type,
            platform=lookup_result.get("platform") or platform_hint,
            creator=lookup_result.get("creator"),
            year=lookup_result.get("year") or year_hint,
            upc=lookup_result.get("upc"),
            cover_art=lookup_result.get("cover_art"),
            analyzer_confidence=confidence,
            analyzer_notes=analyzer_notes,
            external_ids=lookup_result.get("external_ids", {}),
        )
        return record
    except Exception as e:
        logger.error(f"Error resolving metadata: {str(e)}")
        # Return minimal record on error
        return UnifiedMediaRecord(
            title=title,
            media_type=MediaType.GAME,
            platform=platform_hint,
            analyzer_confidence=confidence,
            analyzer_notes=analyzer_notes,
        )


def _stub_game_lookup(
    title: str,
    platform_hint: Optional[str] = None,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Stub game lookup for testing."""
    return {
        "title": title,
        "creator": "Stub Developer",
        "year": year_hint or 2020,
        "platform": platform_hint or "PlayStation 4",
        "upc": None,
        "cover_art": None,
        "external_ids": {},
    }


def _stub_movie_lookup(
    title: str,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Stub movie lookup for testing."""
    return {
        "title": title,
        "creator": "Stub Director",
        "year": year_hint or 2020,
        "platform": "Blu-ray",
        "upc": None,
        "cover_art": None,
        "external_ids": {},
    }


def _stub_music_lookup(
    title: str,
    creator_hint: Optional[str] = None,
    year_hint: Optional[int] = None
) -> Dict[str, Any]:
    """Stub music lookup for testing."""
    return {
        "title": title,
        "creator": creator_hint or "Stub Artist",
        "year": year_hint or 2020,
        "platform": "CD",
        "upc": None,
        "cover_art": None,
        "external_ids": {},
    }
