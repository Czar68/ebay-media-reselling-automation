"""Media image analysis module.
Uses Perplexity API to extract metadata from disc images.
Provides a unified interface that can be stubbed for testing.
"""
import requests
import json
from typing import Dict, Optional, List, Any
from config import PERPLEXITY_API_KEY, USE_STUB_ANALYZER
from debug_logging import setup_debug_logger

logger = setup_debug_logger()


def analyze_disc_image(image_bytes: bytes) -> Dict[str, Any]:
    """Analyze a disc image using Perplexity AI.

    Args:
        image_bytes: Raw bytes of the disc image.

    Returns:
        Dict with keys: media_type, title_candidates, year_hint, platform_hint,
                       notes, confidence
    """
    if USE_STUB_ANALYZER:
        return _stub_analyze(image_bytes)

    # Convert bytes to base64 for Perplexity API
    import base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{image_base64}"

    return _perplexity_analyze(image_url)


def _perplexity_analyze(image_url: str) -> Dict[str, Any]:
    """Call Perplexity API to analyze the disc image."""
    prompt = """Analyze this disc image and extract metadata. Return JSON with:
{
  "media_type": "game" | "movie" | "music" | null,
  "title_candidates": [list of possible titles from visible text],
  "year_hint": integer release year or null,
  "platform_hint": "specific platform/format" or null,
  "notes": "raw OCR or observations from the disc",
  "confidence": 0.0 to 1.0
}
Be concise and extract exact text visible on the disc."""

    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar-pro',
                'messages': [{
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': prompt
                    }, {
                        'type': 'image_url',
                        'image_url': {'url': image_url}
                    }]
                }],
                'temperature': 0.1,
                'max_tokens': 500
            },
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Perplexity API error: {response.status_code}")
            return _stub_analyze(None)

        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Extract JSON from response
        try:
            data = json.loads(content)
            logger.debug(f"Successfully analyzed image: {data}")
            return data
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from Perplexity: {content}")
            return _stub_analyze(None)

    except Exception as e:
        logger.error(f"Perplexity analysis failed: {str(e)}")
        return _stub_analyze(None)


def _stub_analyze(image_bytes: Optional[bytes]) -> Dict[str, Any]:
    """Return stub analysis for testing without Perplexity key."""
    return {
        "media_type": "game",
        "title_candidates": ["Test Game Title"],
        "year_hint": 2020,
        "platform_hint": "PlayStation 4",
        "notes": "Stub analysis - no Perplexity key configured. Replace with real image analysis.",
        "confidence": 0.5
    }
