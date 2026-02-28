"""
Rate limiting middleware for 2Park API
Implements token bucket algorithm for request throttling
"""

import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, Response

from errors import RateLimitExceededException


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def get_config(self) -> tuple[int, int]:
        """Get rate limit configuration from environment"""
        max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
        window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        return max_requests, window_seconds

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed under rate limit"""
        max_requests, window_seconds = self.get_config()

        current_time = time.time()
        window_start = current_time - window_seconds

        # Clean old requests outside the window
        self.requests[client_ip] = [
            timestamp
            for timestamp in self.requests[client_ip]
            if timestamp > window_start
        ]

        # Check if under limit
        return len(self.requests[client_ip]) < max_requests

    def record_request(self, client_ip: str) -> None:
        """Record a request timestamp"""
        self.requests[client_ip].append(time.time())

    def get_remaining(self, client_ip: str) -> int:
        """Get remaining requests in current window"""
        max_requests, _ = self.get_config()
        return max(0, max_requests - len(self.requests.get(client_ip, [])))

    def get_reset_time(self, client_ip: str) -> int:
        """Get seconds until rate limit resets"""
        _, window_seconds = self.get_config()
        timestamps = self.requests.get(client_ip, [])
        if not timestamps:
            return 0
        oldest = min(timestamps)
        return max(0, int(window_seconds - (time.time() - oldest)))


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_rate_limit_headers(client_ip: str) -> dict[str, str]:
    """Generate rate limit headers for response"""
    remaining = rate_limiter.get_remaining(client_ip)
    reset_time = rate_limiter.get_reset_time(client_ip)

    return {
        "X-RateLimit-Limit": str(rate_limiter.get_config()[0]),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_time),
    }


def check_rate_limit(request: Request) -> Optional[Response]:
    """
    Check rate limit and raise exception if exceeded
    Returns None if allowed, Response with 429 if exceeded
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Skip rate limiting for localhost in development
    if client_ip in ("127.0.0.1", "localhost") and os.getenv("ENV") != "production":
        return None

    if not rate_limiter.is_allowed(client_ip):
        raise RateLimitExceededException("Rate limit exceeded. Please try again later.")

    # Record the request
    rate_limiter.record_request(client_ip)

    return None
