"""
Error codes and standardized error handling for 2Park API
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standardized error codes"""

    # Authentication errors
    LOGIN_FAILED = "LOGIN_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"

    # Balance errors
    NO_BALANCE = "NO_BALANCE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"

    # Booking errors
    BOOKING_CONFLICT = "BOOKING_CONFLICT"
    BOOKING_NOT_FOUND = "BOOKING_NOT_FOUND"
    INVALID_LICENSE_PLATE = "INVALID_LICENSE_PLATE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_TIME = "INVALID_TIME"

    # Scraping errors
    SCRAPE_ERROR = "SCRAPE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BROWSER_ERROR = "BROWSER_ERROR"


class ErrorDetail(BaseModel):
    """Error detail structure"""

    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    """Standardized error response"""

    error: ErrorDetail


class APIException(Exception):
    """Base exception for API errors"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_response(self) -> dict:
        """Convert to API response format"""
        return {"error": {"code": self.code.value, "message": self.message}}


class LoginFailedException(APIException):
    """Login failed exception"""

    def __init__(self, message: str = "Failed to login to 2Park"):
        super().__init__(code=ErrorCode.LOGIN_FAILED, message=message, status_code=401)


class InvalidTokenException(APIException):
    """Invalid token exception"""

    def __init__(self, message: str = "Invalid or missing authorization token"):
        super().__init__(code=ErrorCode.INVALID_TOKEN, message=message, status_code=401)


class BookingConflictException(APIException):
    """Booking conflict exception"""

    def __init__(self, message: str = "Booking conflict detected"):
        super().__init__(
            code=ErrorCode.BOOKING_CONFLICT, message=message, status_code=409
        )


class BookingNotFoundException(APIException):
    """Booking not found exception"""

    def __init__(self, message: str = "Booking not found for the given license plate"):
        super().__init__(
            code=ErrorCode.BOOKING_NOT_FOUND, message=message, status_code=404
        )


class NoBalanceException(APIException):
    """No balance exception"""

    def __init__(self, message: str = "Unable to retrieve account balance"):
        super().__init__(code=ErrorCode.NO_BALANCE, message=message, status_code=500)


class ScrapeErrorException(APIException):
    """Scrape error exception"""

    def __init__(self, message: str = "Error scraping data from 2Park website"):
        super().__init__(code=ErrorCode.SCRAPE_ERROR, message=message, status_code=500)


class TimeoutException(APIException):
    """Timeout exception"""

    def __init__(self, message: str = "Operation timed out"):
        super().__init__(code=ErrorCode.TIMEOUT_ERROR, message=message, status_code=504)


class BrowserException(APIException):
    """Browser error exception"""

    def __init__(self, message: str = "Browser automation error"):
        super().__init__(code=ErrorCode.BROWSER_ERROR, message=message, status_code=500)


class RateLimitExceededException(APIException):
    """Rate limit exceeded exception"""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED, message=message, status_code=429
        )
