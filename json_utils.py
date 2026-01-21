"""Robust JSON extraction utilities for handling various API response formats"""
import re
import json
from typing import Any, Dict, Optional


def extract_json_from_response(content: Any) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from API response content with multiple fallback strategies.
    
    Handles:
    - Plain JSON strings
    - JSON in ```json code blocks
    - JSON in ``` code blocks
    - Lists of content (joins with spaces)
    - Raw JSON objects/arrays
    
    Args:
        content: The content to extract JSON from (string, list, or dict)
        
    Returns:
        Parsed JSON dict if found, None if unable to extract
    """
    
    # Handle list response from API
    if isinstance(content, list):
        # Try joining list elements
        content = ' '.join(str(item) for item in content if item)
    
    # Handle non-string types
    if not isinstance(content, str):
        return None
    
    content = content.strip()

    # Try to parse as JSON directly
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    # Pattern: ```json ... ``` or just ``` ... ```
    json_patterns = [
        r'```json\s*\n([^`]+)```',
        r'```\s*\n([^`]+)```',
    ]

    for pattern in json_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try to extract JSON object pattern {..} or array pattern [..]
    # Find first { or [ and match to closing
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = content.find(start_char)
        if start_idx != -1:
            # Find matching closing bracket
            level = 0
            for i in range(start_idx, len(content)):
                if content[i] == start_char:
                    level += 1
                elif content[i] == end_char:
                    level -= 1
                    if level == 0:
                        try:
                            json_str = content[start_idx:i+1]
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            break

    # No JSON found
    return None


def extract_json_safe(content: Any, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Safely extract JSON with a default fallback.
    
    Args:
        content: The content to extract JSON from
        default: Default value if extraction fails (empty dict if not provided)
    
    Returns:
        Parsed JSON dict or default value
    """
    result = extract_json_from_response(content)
    return result if result is not None else (default or {})


def validate_json_structure(data: Dict, required_keys: Optional[list] = None) -> bool:
    """
    Validate JSON structure has required keys.
    
    Args:
        data: The dictionary to validate
        required_keys: List of required top-level keys
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    if required_keys:
        return all(key in data for key in required_keys)
    
    return True
