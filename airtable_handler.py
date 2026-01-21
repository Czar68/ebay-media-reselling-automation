"""Airtable API integration module.
Handles creation and updating of records in the eBay Listings table.
"""
import requests
from typing import Dict, Optional, Any
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME
from debug_logging import setup_debug_logger
from media_models import UnifiedMediaRecord

logger = setup_debug_logger()

AIRTABLE_API_BASE = "https://api.airtable.com/v0"


def create_listing(media_record: UnifiedMediaRecord) -> Dict[str, Any]:
    """Create a new listing record in Airtable.

    Args:
        media_record: UnifiedMediaRecord instance with all metadata.

    Returns:
        Dict with 'success' and 'record_id' on success, or 'error' on failure.
    """
    if not AIRTABLE_API_KEY:
        logger.warning("AIRTABLE_API_KEY not set; simulating record creation")
        return _simulate_create(media_record)

    # Map unified record to Airtable fields
    airtable_fields = _map_to_airtable_fields(media_record)

    try:
        url = f"{AIRTABLE_API_BASE}/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"fields": airtable_fields}

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 201:
            result = response.json()
            record_id = result.get("id")
            logger.info(f"Created Airtable record: {record_id}")
            return {
                "success": True,
                "record_id": record_id,
                "fields": airtable_fields
            }
        else:
            logger.error(f"Airtable error {response.status_code}: {response.text}")
            return {"error": f"Airtable returned {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to create Airtable record: {str(e)}")
        return {"error": str(e)}


def update_listing(record_id: str, media_record: UnifiedMediaRecord) -> Dict[str, Any]:
    """Update an existing listing record in Airtable.

    Args:
        record_id: The Airtable record ID.
        media_record: UnifiedMediaRecord instance with updated metadata.

    Returns:
        Dict with 'success' on success, or 'error' on failure.
    """
    if not AIRTABLE_API_KEY:
        logger.warning(f"AIRTABLE_API_KEY not set; simulating update for {record_id}")
        return {"success": True, "record_id": record_id}

    airtable_fields = _map_to_airtable_fields(media_record)

    try:
        url = f"{AIRTABLE_API_BASE}/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"fields": airtable_fields}

        response = requests.patch(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info(f"Updated Airtable record: {record_id}")
            return {"success": True, "record_id": record_id}
        else:
            logger.error(f"Airtable error {response.status_code}: {response.text}")
            return {"error": f"Airtable returned {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to update Airtable record: {str(e)}")
        return {"error": str(e)}


def _map_to_airtable_fields(media_record: UnifiedMediaRecord) -> Dict[str, Any]:
    """Map UnifiedMediaRecord to Airtable field names and values.

    Uses the current Airtable schema:
    - Title
    - Media Type (Game/Movie/Music)
    - Platform
    - UPC/Barcode
    - Status (New, Ready to list, Listed, Sold)
    - Notes
    - Creator (optional)
    - Year (optional)
    """
    fields = {}

    # Required fields
    if media_record.title:
        fields["Title"] = media_record.title

    # Media Type (map from enum value)
    fields["Media Type"] = _map_media_type(media_record.media_type.value)

    # Platform
    if media_record.platform:
        fields["Platform"] = media_record.platform

    # UPC/Barcode
    if media_record.upc:
        fields["UPC/Barcode"] = media_record.upc
        fields["UPC"] = media_record.upc  # Also update UPC field if it exists

    # Status
    fields["Status"] = media_record.status.value

    # Notes (combine analyzer notes and any other metadata)
    notes_parts = []
    if media_record.analyzer_notes:
        notes_parts.append(f"Analyzer: {media_record.analyzer_notes}")
    if media_record.creator:
        notes_parts.append(f"Creator: {media_record.creator}")
    if media_record.year:
        notes_parts.append(f"Year: {media_record.year}")
    if media_record.cover_art:
        notes_parts.append(f"Cover: {media_record.cover_art}")
    if media_record.external_ids:
        notes_parts.append(f"External IDs: {media_record.external_ids}")

    if notes_parts:
        fields["Notes"] = "\n".join(notes_parts)

    # Optional fields
    if media_record.creator and "Creator" not in fields:
        fields["Creator"] = media_record.creator
    if media_record.year and "Year" not in fields:
        fields["Year"] = media_record.year

    return fields


def _map_media_type(media_type: str) -> str:
    """Map internal media type to Airtable Media Type field value.

    Airtable might use different labels (e.g., "Video Game" vs "game").
    """
    mapping = {
        "game": "Video Game",
        "movie": "Movie",
        "music": "Music"
    }
    return mapping.get(media_type, "Video Game")


def _simulate_create(media_record: UnifiedMediaRecord) -> Dict[str, Any]:
    """Simulate record creation when API key is not available."""
    fields = _map_to_airtable_fields(media_record)
    logger.debug(f"Simulated Airtable create: {fields}")
    return {
        "success": True,
        "record_id": "rec_STUB_001",
        "simulated": True,
        "fields": fields
    }
