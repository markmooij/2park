"""
FastAPI application for 2Park API
Provides RESTful endpoints for parking management
"""

import logging
import os
import uuid

from dotenv import load_dotenv

load_dotenv()
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dateutil import parser as date_parser
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import get_credentials, verify_token
from errors import APIException, ErrorResponse
from models import (
    BalanceResponse,
    BookingResponse,
    CancelBookingResponse,
    CreateBookingRequest,
    ExtendBookingRequest,
    ExtendBookingResponse,
    ListBookingsResponse,
)
from rate_limit import check_rate_limit, rate_limiter
from scraper import TwoParkScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="2Park API",
    description="RESTful API for managing parking bookings on 2park.nl",
    version="1.0.0",
)


# Add CORS middleware for Home Assistant integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to logs and response headers"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add request ID to logger
    log_with_request_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    log_with_request_id.info(f"Request started: {request.method} {request.url.path}")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    # Add rate limit headers
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limiter.get_config()[0]),
        "X-RateLimit-Remaining": str(rate_limiter.get_remaining(client_ip)),
        "X-RateLimit-Reset": str(rate_limiter.get_reset_time(client_ip)),
    }
    response.headers.update(rate_limit_headers)

    return response


# Exception handler for API exceptions
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(),
    )


# Exception handler for generic exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "2Park API",
        "version": "1.0.0",
        "endpoints": {
            "balance": "GET /api/account/balance",
            "create_booking": "POST /api/bookings",
            "extend_booking": "POST /api/bookings/{license_plate}/extend",
            "cancel_booking": "POST /api/bookings/{license_plate}/cancel",
        },
        "authentication": "Bearer token required in Authorization header",
        "rate_limit": {
            "max_requests": rate_limiter.get_config()[0],
            "window_seconds": rate_limiter.get_config()[1],
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rate_limit": {
            "max_requests": rate_limiter.get_config()[0],
            "window_seconds": rate_limiter.get_config()[1],
        },
    }


@app.get(
    "/api/account/balance",
    response_model=BalanceResponse,
    responses={
        200: {"description": "Balance retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_balance(
    request: Request,
    authorized: Annotated[bool, Depends(verify_token)],
    _: Annotated[bool, Depends(check_rate_limit)],
):
    """
    Get current account balance

    Requires valid Bearer token in Authorization header.
    Rate limited by client IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger_with_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_with_id.info("Getting account balance")

    email, password = get_credentials()

    async with TwoParkScraper(email, password) as scraper:
        balance = await scraper.get_balance()
        return BalanceResponse(
            balance=balance,
            currency="EUR",
            last_checked=datetime.now(timezone.utc),
        )


@app.get(
    "/api/bookings",
    response_model=ListBookingsResponse,
    responses={
        200: {"description": "List of active bookings retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def list_bookings(
    request: Request,
    authorized: Annotated[bool, Depends(verify_token)],
    _: Annotated[bool, Depends(check_rate_limit)],
):
    """
    Get all active parking bookings

    Requires valid Bearer token in Authorization header.
    Rate limited by client IP.

    Returns a list of all active bookings with license plate, start/end times, and status.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger_with_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_with_id.info("Listing all active bookings")

    email, password = get_credentials()

    async with TwoParkScraper(email, password) as scraper:
        reservations = await scraper.get_active_reservations()

        bookings = [
            BookingResponse(
                license_plate=res.license_plate,
                start_time=datetime.fromisoformat(res.start_time.replace("Z", "+00:00"))
                if res.start_time
                else datetime.now(timezone.utc),
                end_time=datetime.fromisoformat(res.end_time.replace("Z", "+00:00"))
                if res.end_time
                else datetime.now(timezone.utc),
                status="active",
            )
            for res in reservations
        ]

        return ListBookingsResponse(bookings=bookings, count=len(bookings))


@app.post(
    "/api/bookings",
    response_model=BookingResponse,
    status_code=201,
    responses={
        201: {"description": "Booking created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid license plate format"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Booking conflict"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def create_booking(
    request: CreateBookingRequest,
    request_obj: Request,
    authorized: Annotated[bool, Depends(verify_token)],
    _: Annotated[bool, Depends(check_rate_limit)],
):
    """
    Create a new parking booking

    Requires valid Bearer token in Authorization header.
    Rate limited by client IP.

    - **license_plate**: License plate in format XX-123-Y
    - **start_time**: "now" or ISO 8601 datetime string
    - **duration_minutes**: Duration in minutes (1-1440)
    """
    request_id = getattr(request_obj.state, "request_id", "unknown")
    logger_with_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_with_id.info(f"Creating booking for {request.license_plate}")

    # Parse start time
    if request.start_time.lower() == "now":
        start_time = datetime.now(timezone.utc)
    else:
        try:
            start_time = date_parser.isoparse(request.start_time)
            # Convert to UTC if not already
            if start_time.tzinfo is None:
                # Assume UTC if no timezone
                start_time = start_time.replace(tzinfo=None)
            else:
                start_time = start_time.astimezone(None).replace(tzinfo=None)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_TIME",
                        "message": f"Invalid start_time format: {str(e)}",
                    }
                },
            )

    # Calculate end time
    end_time = start_time + timedelta(minutes=request.duration_minutes)

    email, password = get_credentials()

    async with TwoParkScraper(email, password) as scraper:
        result = await scraper.create_booking(
            license_plate=request.license_plate,
            start_time=start_time,
            end_time=end_time,
        )

        return BookingResponse(
            license_plate=result["license_plate"],
            start_time=result["start_time"],
            end_time=result["end_time"],
            status=result["status"],
        )


@app.post(
    "/api/bookings/{license_plate}/extend",
    response_model=ExtendBookingResponse,
    responses={
        200: {"description": "Booking extended successfully"},
        400: {"model": ErrorResponse, "description": "Invalid license plate format"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Booking not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def extend_booking(
    license_plate: str,
    request: ExtendBookingRequest,
    request_obj: Request,
    authorized: Annotated[bool, Depends(verify_token)],
    _: Annotated[bool, Depends(check_rate_limit)],
):
    """
    Extend an existing parking booking

    Requires valid Bearer token in Authorization header.
    Rate limited by client IP.

    - **license_plate**: License plate of the booking to extend
    - **additional_minutes**: Additional minutes to add (1-1440)
    """
    request_id = getattr(request_obj.state, "request_id", "unknown")
    logger_with_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_with_id.info(
        f"Extending booking for {license_plate} by {request.additional_minutes} minutes"
    )

    email, password = get_credentials()

    async with TwoParkScraper(email, password) as scraper:
        result = await scraper.extend_booking(
            license_plate=license_plate,
            additional_minutes=request.additional_minutes,
        )

        return ExtendBookingResponse(
            license_plate=result["license_plate"],
            new_end_time=result["new_end_time"],
        )


@app.post(
    "/api/bookings/{license_plate}/cancel",
    response_model=CancelBookingResponse,
    responses={
        200: {"description": "Booking cancelled successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Booking not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def cancel_booking(
    license_plate: str,
    request_obj: Request,
    authorized: Annotated[bool, Depends(verify_token)],
    _: Annotated[bool, Depends(check_rate_limit)],
):
    """
    Cancel an existing parking booking

    Requires valid Bearer token in Authorization header.
    Rate limited by client IP.

    - **license_plate**: License plate of the booking to cancel
    """
    request_id = getattr(request_obj.state, "request_id", "unknown")
    logger_with_id = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_with_id.info(f"Cancelling booking for {license_plate}")

    email, password = get_credentials()

    async with TwoParkScraper(email, password) as scraper:
        result = await scraper.cancel_booking(license_plate=license_plate)

        return CancelBookingResponse(
            status=result["status"],
            cancelled_at=result["cancelled_at"],
        )


if __name__ == "__main__":
    import uvicorn

    # Check required environment variables
    required_vars = ["API_TOKEN", "TWOPARK_EMAIL", "TWOPARK_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please set the following:")
        logger.error("  API_TOKEN - Your API authentication token")
        logger.error("  TWOPARK_EMAIL - Your 2Park email")
        logger.error("  TWOPARK_PASSWORD - Your 2Park password")
        exit(1)

    # Run the API server
    logger.info("Starting 2Park API server...")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info",
    )
