# -*- coding: utf-8 -*-
"""
Rate Limiter Module

Provides sliding-window rate limiting for API endpoints.
Supports per-endpoint and per-user rate limits with automatic cleanup.
"""

import time
import threading
from functools import wraps
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from flask import request, jsonify


class RateLimiter:
    """Sliding-window rate limiter with per-endpoint and per-user scoping."""

    def __init__(self, cleanup_interval: int = 3600):
        """Initialize rate limiter.

        Args:
            cleanup_interval: How often to clean old timestamps (seconds)
        """
        self.limits: Dict[str, int] = {}  # endpoint -> max_requests
        self.windows: Dict[str, int] = {}  # endpoint -> window_size (seconds)
        self.requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self.lock = threading.Lock()

    def set_limit(self, endpoint: str, requests_per_minute: int, window: int = 60):
        """Configure rate limit for endpoint.

        Args:
            endpoint: Endpoint identifier (e.g., 'telegram-webhook')
            requests_per_minute: Max requests allowed in window
            window: Time window in seconds (default 60)
        """
        self.limits[endpoint] = requests_per_minute
        self.windows[endpoint] = window

    def _cleanup_old_timestamps(self):
        """Remove timestamps older than current window (prevent memory leak)."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        for endpoint in self.requests:
            for key in self.requests[endpoint]:
                window = self.windows.get(endpoint, 60)
                self.requests[endpoint][key] = [
                    ts for ts in self.requests[endpoint][key]
                    if now - ts < window
                ]

        self.last_cleanup = now

    def is_allowed(self, endpoint: str, limit_key: str = 'global') -> Tuple[bool, Optional[int]]:
        """Check if request is allowed under rate limit.

        Args:
            endpoint: Endpoint identifier
            limit_key: Unique key for limiting (default 'global' for endpoint-wide limit)

        Returns:
            Tuple of (is_allowed: bool, retry_after: Optional[int] seconds)
        """
        with self.lock:
            self._cleanup_old_timestamps()

            if endpoint not in self.limits:
                return True, None

            window = self.windows[endpoint]
            max_requests = self.limits[endpoint]
            now = time.time()
            cutoff = now - window

            timestamps = self.requests[endpoint][limit_key]
            recent = [ts for ts in timestamps if ts > cutoff]
            self.requests[endpoint][limit_key] = recent

            if len(recent) < max_requests:
                self.requests[endpoint][limit_key].append(now)
                return True, None
            else:
                oldest = recent[0]
                retry_after = int(window - (now - oldest)) + 1
                return False, retry_after

    def limit(self, endpoint: str, requests_per_minute: int = 100, use_user_id: bool = False):
        """Decorator for rate limiting endpoints.

        Args:
            endpoint: Endpoint identifier (e.g., 'telegram-webhook')
            requests_per_minute: Max requests per minute
            use_user_id: If True, per-user limits; if False, global endpoint limit

        Example:
            @app.route('/telegram-webhook', methods=['POST'])
            @limiter.limit('telegram-webhook', requests_per_minute=100)
            def webhook():
                return 'OK'
        """
        self.set_limit(endpoint, requests_per_minute)

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if use_user_id:
                    limit_key = request.remote_addr or 'unknown'
                else:
                    limit_key = 'global'

                allowed, retry_after = self.is_allowed(endpoint, limit_key)

                if not allowed:
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': retry_after
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(retry_after)
                    return response

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    def get_stats(self, endpoint: str) -> Dict:
        """Get current rate limit stats for endpoint.

        Returns:
            Dict with limit, window, and current request counts
        """
        with self.lock:
            window = self.windows.get(endpoint, 60)
            max_requests = self.limits.get(endpoint, 'unlimited')
            now = time.time()
            cutoff = now - window

            stats = {
                'endpoint': endpoint,
                'limit': max_requests,
                'window_seconds': window,
                'current_requests': {}
            }

            if endpoint in self.requests:
                for key, timestamps in self.requests[endpoint].items():
                    recent = [ts for ts in timestamps if ts > cutoff]
                    stats['current_requests'][key] = len(recent)

            return stats


limiter = RateLimiter()

DEFAULT_LIMITS = {
    'telegram-webhook': 100,
    'webhook/airtable': 50,
    'price-lookup': 20,
}
