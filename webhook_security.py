# -*- coding: utf-8 -*-
"""
Webhook Security Module

Provides validation and sanitization for webhook requests.
Handles token validation, HTTPS enforcement, payload limits, and input sanitization.
"""

import hmac
import hashlib
from typing import Dict, Tuple, Optional
from flask import request, jsonify


class WebhookValidator:
    """Validates and sanitizes incoming webhook requests."""

    MAX_PAYLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_STRING_LENGTH = 10000  # Max length for string fields
    ALLOWED_CONTENT_TYPES = {'application/json'}

    def __init__(self, telegram_token: str):
        """Initialize validator.

        Args:
            telegram_token: Bot token for HMAC validation
        """
        self.telegram_token = telegram_token

    def validate_telegram_signature(self, data: bytes, signature: str) -> bool:
        """Validate Telegram webhook signature using HMAC-SHA256.

        Args:
            data: Request body (raw bytes)
            signature: X-Telegram-Bot-Api-Secret-Hash header

        Returns:
            True if signature is valid
        """
        expected = hmac.new(
            self.telegram_token.encode(),
            data,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def validate_https(self) -> Tuple[bool, Optional[str]]:
        """Ensure request uses HTTPS (production only).

        Returns:
            Tuple of (is_valid, error_message)
        """
        if request.scheme != 'https' and not request.environ.get('WERKZEUG_RUN_MAIN'):
            return False, "HTTPS required for webhook"
        return True, None

    def validate_payload_size(self) -> Tuple[bool, Optional[str]]:
        """Check request body size limit.

        Returns:
            Tuple of (is_valid, error_message)
        """
        content_length = request.content_length
        if content_length and content_length > self.MAX_PAYLOAD_SIZE:
            return False, f"Payload too large: {content_length} > {self.MAX_PAYLOAD_SIZE}"
        return True, None

    def validate_content_type(self) -> Tuple[bool, Optional[str]]:
        """Check content type is JSON.

        Returns:
            Tuple of (is_valid, error_message)
        """
        ct = request.content_type or ''
        if 'application/json' not in ct:
            return False, f"Invalid content type: {ct}"
        return True, None

    def sanitize_string(self, value: str, max_length: int = None) -> str:
        """Sanitize string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""

        limit = max_length or self.MAX_STRING_LENGTH
        if len(value) > limit:
            value = value[:limit]

        # Remove null bytes and control characters
        value = ''.join(c for c in value if ord(c) >= 32 or c in '\t\n\r')
        return value.strip()

    def sanitize_dict(self, data: Dict) -> Dict:
        """Recursively sanitize dictionary.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            safe_key = self.sanitize_string(str(key), max_length=256)
            if isinstance(value, str):
                sanitized[safe_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = self.sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[safe_key] = [self.sanitize_string(str(v)) for v in value]
            else:
                sanitized[safe_key] = value
        return sanitized

    def validate_request(self) -> Tuple[bool, Optional[Dict]]:
        """Run all validations on request.

        Returns:
            Tuple of (is_valid, error_dict)
        """
        # Check HTTPS
        valid, error = self.validate_https()
        if not valid:
            return False, {'error': error}

        # Check payload size
        valid, error = self.validate_payload_size()
        if not valid:
            return False, {'error': error}

        # Check content type
        valid, error = self.validate_content_type()
        if not valid:
            return False, {'error': error}

        # Validate Telegram signature if header present
        sig = request.headers.get('X-Telegram-Bot-Api-Secret-Hash')
        if sig:
            if not self.validate_telegram_signature(request.data, sig):
                return False, {'error': 'Invalid signature'}

        return True, None

    def get_validated_json(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Get and validate JSON body.

        Returns:
            Tuple of (data, error_dict)
        """
        valid, error = self.validate_request()
        if not valid:
            return None, error

        try:
            data = request.get_json(force=True)
            if not isinstance(data, dict):
                return None, {'error': 'JSON must be object'}
            return self.sanitize_dict(data), None
        except Exception as e:
            return None, {'error': f'Invalid JSON: {str(e)}'}


def webhook_required(validator: WebhookValidator):
    """Decorator for webhook endpoints.

    Args:
        validator: WebhookValidator instance

    Usage:
        @app.route('/webhook', methods=['POST'])
        @webhook_required(validator)
        def webhook(data):
            return jsonify({'status': 'ok'})
    """
    def decorator(f):
        def decorated_function(*args, **kwargs):
            data, error = validator.get_validated_json()
            if error:
                response = jsonify(error)
                response.status_code = 400
                return response
            return f(data, *args, **kwargs)
        return decorated_function
    return decorator
