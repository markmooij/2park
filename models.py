"""
Pydantic models for 2Park API requests and responses
"""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Request Models


def normalize_license_plate(license_plate: str) -> str:
    """
    Normalize a Dutch license plate to the format used by 2park.nl

    Strips hyphens, spaces, and converts to uppercase.
    Idempotent — calling twice produces the same result.

    Args:
        license_plate: Any license plate string

    Returns:
        Normalized plate string (no hyphens, no spaces, uppercase)
    """
    return license_plate.strip().upper().replace("-", "").replace(" ", "")


def validate_license_plate(license_plate: str) -> str:
    """
    Validate Dutch license plate format

    Supports:
    - Current EU format: XX-XX-X or XX-XXX
    - Historic format: XX-XX-XX
    - Temporary format: XX-XX-??
    - KV/KVX format: DD-LLLL (2 digits + 4 letters, e.g., 51PXPN)
    """
    # Normalize first: strip whitespace, remove hyphens, uppercase
    normalized = normalize_license_plate(license_plate)

    if not normalized:
        raise ValueError(
            f"Invalid license plate format: '{license_plate}'. "
            f"Plate is empty after normalization"
        )

    # Dutch license plate patterns (all checked against normalized, no-hyphen form)
    patterns = [
        # Current EU format (2 letters, 2 letters, 1 digit)
        r"^[A-Z]{2}[A-Z]{2}[0-9]{1}$",
        # Current EU format (2 letters, 3 digits, 2 letters)
        r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$",
        # Current EU format (2 letters, 2 digits, 1 letter)
        r"^[A-Z]{2}[0-9]{2}[A-Z]{1}$",
        # Historic format (2 letters, 2 letters, 2 digits)
        r"^[A-Z]{2}[A-Z]{2}[0-9]{2}$",
        # Historic format (2 letters, 3 letters, 2 digits)
        r"^[A-Z]{2}[A-Z]{3}[0-9]{2}$",
        # Temporary format
        r"^[A-Z]{2}[A-Z]{2}[\?]{2}$",
        # KV/KVX format (2 digits + 4 letters, e.g., 51PXPN)
        r"^[0-9]{2}[A-Z]{4}$",
    ]

    for pattern in patterns:
        if re.match(pattern, normalized):
            return normalized

    raise ValueError(
        f"Invalid license plate format: {license_plate}. "
        f"Use format like 'AB-12-CD', 'AB123CD', or '51-PXPN'"
    )


class CreateBookingRequest(BaseModel):
    """Request model for creating a booking"""

    license_plate: str = Field(
        ..., description="License plate in format XX-123-Y", min_length=1
    )
    start_time: str = Field(..., description="Start time: 'now' or ISO 8601 datetime")
    duration_minutes: int = Field(..., description="Duration in minutes", gt=0, le=1440)

    @field_validator("license_plate", mode="before")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        """Validate license plate format"""
        if isinstance(v, str):
            return validate_license_plate(v)
        return v


class ExtendBookingRequest(BaseModel):
    """Request model for extending a booking"""

    additional_minutes: int = Field(
        ..., description="Additional minutes to add", gt=0, le=1440
    )


# Response Models


class BookingResponse(BaseModel):
    """Response model for booking operations"""

    license_plate: str = Field(..., description="License plate")
    start_time: datetime = Field(..., description="Booking start time in ISO 8601")
    end_time: datetime = Field(..., description="Booking end time in ISO 8601")
    status: Literal["active", "cancelled"] = Field(..., description="Booking status")

    class Config:
        json_schema_extra = {
            "example": {
                "license_plate": "XX-123-Y",
                "start_time": "2025-01-05T14:00:00Z",
                "end_time": "2025-01-05T15:00:00Z",
                "status": "active",
            }
        }


class ExtendBookingResponse(BaseModel):
    """Response model for extending a booking"""

    license_plate: str = Field(..., description="License plate")
    new_end_time: datetime = Field(
        ..., description="New end time after extension in ISO 8601"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "license_plate": "XX-123-Y",
                "new_end_time": "2025-01-05T16:00:00Z",
            }
        }


class CancelBookingResponse(BaseModel):
    """Response model for cancelling a booking"""

    status: Literal["cancelled"] = Field(..., description="Cancellation status")
    cancelled_at: datetime = Field(
        ..., description="Timestamp when booking was cancelled in ISO 8601"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "cancelled",
                "cancelled_at": "2025-01-05T15:20:00Z",
            }
        }


class BalanceResponse(BaseModel):
    """Response model for account balance"""

    balance: float = Field(..., description="Current account balance")
    currency: Literal["EUR"] = Field(default="EUR", description="Currency code")
    last_checked: datetime = Field(
        ..., description="Timestamp when balance was checked in ISO 8601"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "balance": 12.35,
                "currency": "EUR",
                "last_checked": "2025-01-05T13:55:00Z",
            }
        }


class ListBookingsResponse(BaseModel):
    """Response model for listing all active bookings"""

    bookings: list[BookingResponse] = Field(
        ..., description="List of active bookings"
    )
    count: int = Field(..., description="Number of active bookings")

    class Config:
        json_schema_extra = {
            "example": {
                "bookings": [
                    {
                        "license_plate": "AB-12-CD",
                        "start_time": "2025-01-05T14:00:00Z",
                        "end_time": "2025-01-05T16:00:00Z",
                        "status": "active",
                    }
                ],
                "count": 1,
            }
        }


# Internal Models


class Reservation(BaseModel):
    """Internal model for a reservation"""

    name: str
    license_plate: str
    start_time: str
    end_time: str
