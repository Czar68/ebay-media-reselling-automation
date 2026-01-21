"""Unified media record models for games, movies, and music.
Provides consistent data structure across all media types.
"""

from typing import Optional, List, Dict, Any
from enum import Enum


class MediaType(str, Enum):
    """Enumeration of supported media types."""
    GAME = "game"
    MOVIE = "movie"
    MUSIC = "music"


class MediaStatus(str, Enum):
    """Enumeration of inventory status values."""
    NEW = "New"
    READY_TO_LIST = "Ready to list"
    LISTED = "Listed"
    SOLD = "Sold"
    HOLD = "Hold"


class UnifiedMediaRecord:
    """Unified data model for all media types: games, movies, music."""

    def __init__(
        self,
        title: str,
        media_type: MediaType,
        platform: Optional[str] = None,
        creator: Optional[str] = None,
        year: Optional[int] = None,
        upc: Optional[str] = None,
        cover_art: Optional[str] = None,
        status: MediaStatus = MediaStatus.NEW,
        notes: Optional[str] = None,
        analyzer_confidence: float = 0.0,
        analyzer_notes: Optional[str] = None,
        external_ids: Optional[Dict[str, str]] = None,
    ):
        """Initialize a unified media record.

        Args:
            title: The title of the media item.
            media_type: One of GAME, MOVIE, MUSIC.
            platform: Gaming platform, video format, or audio format.
            creator: Developer, director, or artist.
            year: Release or copyright year.
            upc: Universal Product Code (if available).
            cover_art: URL to cover art image.
            status: Current inventory status.
            notes: Free-form notes for the item.
            analyzer_confidence: Confidence score from Perplexity (0–1).
            analyzer_notes: Raw notes from the image analyzer.
            external_ids: Dict of IDs from external databases (e.g., {"igdb": "123", "omdb": "tt456"}).
        """
        self.title = title
        self.media_type = media_type
        self.platform = platform
        self.creator = creator
        self.year = year
        self.upc = upc
        self.cover_art = cover_art
        self.status = status
        self.notes = notes or ""
        self.analyzer_confidence = analyzer_confidence
        self.analyzer_notes = analyzer_notes or ""
        self.external_ids = external_ids or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for Airtable or JSON serialization."""
        return {
            "Title": self.title,
            "MediaType": self.media_type.value,
            "Platform": self.platform,
            "Creator": self.creator,
            "Year": self.year,
            "UPC": self.upc,
            "CoverArt": self.cover_art,
            "Status": self.status.value,
            "Notes": self.notes,
            "AnalyzerConfidence": self.analyzer_confidence,
            "AnalyzerNotes": self.analyzer_notes,
            "ExternalIDs": self.external_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedMediaRecord':
        """Create from a dictionary (e.g., from Airtable or JSON)."""
        return cls(
            title=data.get("Title", ""),
            media_type=MediaType(data.get("MediaType", "game")),
            platform=data.get("Platform"),
            creator=data.get("Creator"),
            year=data.get("Year"),
            upc=data.get("UPC"),
            cover_art=data.get("CoverArt"),
            status=MediaStatus(data.get("Status", MediaStatus.NEW.value)),
            notes=data.get("Notes"),
            analyzer_confidence=float(data.get("AnalyzerConfidence", 0.0)),
            analyzer_notes=data.get("AnalyzerNotes"),
            external_ids=data.get("ExternalIDs", {}),
        )

    def __repr__(self) -> str:
        return f"<UnifiedMediaRecord {self.media_type.value}: {self.title}>"
