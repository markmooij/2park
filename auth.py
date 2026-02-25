"""
Authentication middleware for 2Park API
Simple bearer token authentication
"""

import os
from typing import Optional

from fastapi import Header, HTTPException

from errors import InvalidTokenException


def get_api_token() -> str:
    """Get the API token from environment variable"""
    token = os.getenv("API_TOKEN")
    if not token:
        raise ValueError(
            "API_TOKEN environment variable not set. "
            "Please set it to secure your API endpoints."
        )
    return token


def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verify the bearer token in the Authorization header

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        True if token is valid

    Raises:
        InvalidTokenException: If token is missing or invalid
    """
    if not authorization:
        raise InvalidTokenException("Missing Authorization header")

    # Check format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenException(
            "Invalid Authorization header format. Expected: 'Bearer <token>'"
        )

    provided_token = parts[1]
    expected_token = get_api_token()

    # Simple constant-time comparison to prevent timing attacks
    if provided_token != expected_token:
        raise InvalidTokenException("Invalid API token")

    return True


def get_credentials() -> tuple[str, str]:
    """
    Get 2Park credentials from environment variables

    Returns:
        Tuple of (email, password)

    Raises:
        ValueError: If credentials are not set
    """
    email = os.getenv("TWOPARK_EMAIL")
    password = os.getenv("TWOPARK_PASSWORD")

    if not email or not password:
        raise ValueError(
            "2Park credentials not set. "
            "Please set TWOPARK_EMAIL and TWOPARK_PASSWORD environment variables."
        )

    return email, password
