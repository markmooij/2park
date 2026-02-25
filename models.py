"""
Pydantic models for 2Park API requests and responses
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Request Models


class CreateBookingRequest(BaseModel):
    """Request model for creating a booking"""

    license_plate: str = Field(
        ..., description="License plate in format XX-123-Y", min_length=1
    )
    start_time: str = Field(..., description="Start time: 'now' or ISO 8601 datetime")
    duration_minutes: int = Field(..., description="Duration in minutes", gt=0, le=1440)


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


# Internal Models


class Reservation(BaseModel):
    """Internal model for a reservation"""

    name: str
    license_plate: str
    start_time: str
    end_time: str
