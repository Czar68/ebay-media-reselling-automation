"""Telegram bot handler module.
Receives disc images via Telegram, orchestrates analysis and cataloging.
"""
import requests
from typing import Dict, Optional, Any
from config import TELEGRAM_BOT_TOKEN, get_config_status
from debug_logging import setup_debug_logger
from media_analyzer import analyze_disc_image
from database_lookup import resolve_metadata
from airtable_handler import create_listing
from media_models import UnifiedMediaRecord

logger = setup_debug_logger()

TELEGRAM_API_BASE = "https://api.telegram.org"


def handle_update(update_json: Dict[str, Any]) -> Dict[str, Any]:
    """Main handler for incoming Telegram updates.

    Args:
        update_json: Telegram update object (from webhook POST body).

    Returns:
        Dict with 'success' and response details.
    """
    try:
        # Check if this is a message update
        if "message" not in update_json:
            logger.debug(f"Ignoring non-message update: {update_json.get('update_id')}")
            return {"success": True, "ignored": True}

        message = update_json["message"]
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")

        if not chat_id:
            logger.warning("No chat_id in update")
            return {"success": False, "error": "No chat_id"}

        # Handle different message types
        if "text" in message:
            text = message["text"]
            if text.startswith("/start"):
                return _handle_start(chat_id, message_id)
            elif text.startswith("/help"):
                return _handle_help(chat_id, message_id)
            elif text.startswith("/status"):
                return _handle_status(chat_id, message_id)
            else:
                return _send_message(chat_id, "I analyze disc images. Send me a photo of a game, movie, or music disc!")

        elif "photo" in message:
            return _handle_photo(chat_id, message_id, message["photo"])

        else:
            return _send_message(chat_id, "Please send a disc image or use /help for commands.")

    except Exception as e:
        logger.error(f"Error handling update: {str(e)}")
        return {"success": False, "error": str(e)}


def _handle_start(chat_id: int, message_id: int) -> Dict[str, Any]:
    """Handle /start command."""
    welcome_text = """Welcome to Games Movies Music Bot! 🤖

I analyze disc images and automatically catalog them to your eBay inventory.

Send me a photo of a video game disc, movie DVD/Blu-ray, or music CD and I'll extract the metadata.

Commands:
/help - Show available commands
/status - Check API connection status"""
    return _send_message(chat_id, welcome_text)


def _handle_help(chat_id: int, message_id: int) -> Dict[str, Any]:
    """Handle /help command."""
    help_text = """📖 How to use this bot:

1. Send a clear photo of the disc face (showing title, platform, year, etc.)
2. Bot analyzes the image using AI and metadata databases
3. Extracted data is saved to your Airtable inventory
4. You'll get confirmation with what was found

📸 Tips for best results:
- Good lighting
- Focus on disc artwork and text
- Front-facing angle

Supported media:
🎮 Video games (all platforms)
🎬 Movies (DVD/Blu-ray)
🎵 Music CDs

Command /status to check if all APIs are ready."""
    return _send_message(chat_id, help_text)


def _handle_status(chat_id: int, message_id: int) -> Dict[str, Any]:
    """Handle /status command."""
    config = get_config_status()
    status_text = f"""🔧 System Status:

Environment: {config['environment']}

APIs Ready:
{'✅' if config['perplexity_ready'] else '❌'} Perplexity (image analysis)
{'✅' if config['airtable_ready'] else '❌'} Airtable (inventory storage)
{'✅' if config['omdb_ready'] else '❌'} OMDb (movie lookup)
{'✅' if config['igdb_ready'] else '❌'} IGDB (game lookup)
{'✅' if config['musicbrainz_ready'] else '❌'} MusicBrainz (music lookup)
{'✅' if config['telegram_ready'] else '❌'} Telegram (this bot)

Using stubs: {config['use_stub_analyzer'] or config['use_stub_lookups']}

Ready to analyze discs: {'Yes ✅' if not (config['use_stub_analyzer'] and config['use_stub_lookups']) else 'Partial (using test data)'}"""
    return _send_message(chat_id, status_text)


def _handle_photo(chat_id: int, message_id: int, photos: list) -> Dict[str, Any]:
    """Handle incoming photo message.

    Args:
        chat_id: Telegram chat ID.
        message_id: Telegram message ID.
        photos: List of photo objects from Telegram.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return _send_message(chat_id, "⚠️ Bot not configured. Check TELEGRAM_BOT_TOKEN.")

    try:
        # Get the largest photo
        photo = max(photos, key=lambda p: p.get("file_size", 0))
        file_id = photo.get("file_id")

        if not file_id:
            return _send_message(chat_id, "❌ Could not process image. Please try again.")

        # Download image from Telegram
        logger.debug(f"Downloading image {file_id}...")
        image_bytes = _download_file(file_id)
        if not image_bytes:
            return _send_message(chat_id, "❌ Failed to download image. Please try again.")

        # Send "typing" indicator
        _send_chat_action(chat_id, "typing")

        # Step 1: Analyze image
        logger.debug("Analyzing image...")
        analyzer_result = analyze_disc_image(image_bytes)
        if "error" in analyzer_result:
            logger.error(f"Analysis failed: {analyzer_result['error']}")
            return _send_message(chat_id, f"❌ Analysis failed: {analyzer_result['error']}")

        # Step 2: Resolve metadata
        logger.debug("Resolving metadata...")
        media_record = resolve_metadata(analyzer_result)

        # Step 3: Create Airtable listing
        logger.debug("Creating Airtable record...")
        airtable_result = create_listing(media_record)
        if "error" in airtable_result:
            logger.error(f"Airtable creation failed: {airtable_result['error']}")
            return _send_message(chat_id, f"❌ Failed to save to inventory: {airtable_result['error']}")

        # Step 4: Send confirmation
        record_id = airtable_result.get("record_id", "unknown")
        confidence = analyzer_result.get("confidence", 0)
        title_candidates = analyzer_result.get("title_candidates", [])
        chosen_title = media_record.title

        confirmation_text = f"""✅ Disc Cataloged!

📚 Title: {chosen_title}
🎮 Type: {media_record.media_type.value.title()}
🖥️ Platform: {media_record.platform or 'Unknown'}
📅 Year: {media_record.year or 'Unknown'}
🎯 Confidence: {confidence:.0%}

Record ID: `{record_id}`
Saved to Airtable ✓"""

        return _send_message(chat_id, confirmation_text)

    except Exception as e:
        logger.error(f"Error handling photo: {str(e)}")
        return _send_message(chat_id, f"❌ Error: {str(e)}")


def _download_file(file_id: str) -> Optional[bytes]:
    """Download a file from Telegram.

    Args:
        file_id: Telegram file ID.

    Returns:
        File bytes or None if failed.
    """
    try:
        # Get file info
        url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/getFile"
        response = requests.get(url, params={"file_id": file_id}, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to get file info: {response.text}")
            return None

        file_path = response.json().get("result", {}).get("file_path")
        if not file_path:
            logger.error("No file_path in response")
            return None

        # Download file
        file_url = f"{TELEGRAM_API_BASE}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_response = requests.get(file_url, timeout=30)
        if file_response.status_code != 200:
            logger.error(f"Failed to download file: {file_response.status_code}")
            return None

        return file_response.content
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None


def _send_message(chat_id: int, text: str) -> Dict[str, Any]:
    """Send a text message to Telegram.

    Args:
        chat_id: Telegram chat ID.
        text: Message text.

    Returns:
        Result dict with 'success' status.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning(f"Not sending message (no token): {text}")
        return {"success": True, "simulated": True}

    try:
        url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.debug(f"Message sent to {chat_id}")
            return {"success": True}
        else:
            logger.error(f"Failed to send message: {response.text}")
            return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {"success": False, "error": str(e)}


def _send_chat_action(chat_id: int, action: str) -> Dict[str, Any]:
    """Send a chat action (typing, upload_photo, etc.).

    Args:
        chat_id: Telegram chat ID.
        action: Action type (typing, upload_photo, etc.)

    Returns:
        Result dict with 'success' status.
    """
    if not TELEGRAM_BOT_TOKEN:
        return {"success": True, "simulated": True}

    try:
        url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
        payload = {"chat_id": chat_id, "action": action}
        response = requests.post(url, json=payload, timeout=10)
        return {"success": response.status_code == 200}
    except Exception as e:
        logger.warning(f"Error sending chat action: {str(e)}")
        return {"success": False}
