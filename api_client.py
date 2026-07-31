"""
Direct HTTP API client for 2Park platform.

Replaces the Playwright-based scraper.py with lightweight HTTP requests
against the JSON API that the 2Park React frontend uses internally.

Usage:
    client = TwoParkClient(email, password)
    client.login()
    balance = client.get_balance()
    bookings = client.get_active_reservations()
    result = client.create_booking("51PXPN", start_dt, end_dt)
    result = client.extend_booking("51PXPN", 60)
    result = client.cancel_booking("51PXPN")
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

# The 2Park backend interprets all datetimes in Europe/Amsterdam local
# time (the frontend's Ye() helper formats using the browser's local
# timezone). We must do the same when sending/parsing timestamps.
LOCAL_TZ = ZoneInfo("Europe/Amsterdam")

from errors import (
    BookingConflictException,
    BookingNotFoundException,
    BrowserException,
    LoginFailedException,
    NoBalanceException,
    ScrapeErrorException,
    TimeoutException,
)
from models import Reservation, normalize_license_plate

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────

BASE_URL = "https://mijn.2park.nl/gsmpark-app-www/json"
LOCALE = "nl_NL"
REQUEST_TIMEOUT = 30  # seconds

# ── Date helpers ────────────────────────────────────────────────────


def _format_api_datetime(dt: datetime) -> str:
    """
    Format a datetime to the API's expected string format.

    The 2Park API uses DD-MM-YYYY HH:mm:ss in Europe/Amsterdam local
    time (the frontend's Ye() helper formats using the browser's local
    timezone). The input is converted from its own timezone (or treated
    as UTC if naive) to Amsterdam local time before formatting.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(LOCAL_TZ)
    return local.strftime("%d-%m-%Y %H:%M:%S")


def _parse_api_datetime(value: str) -> Optional[datetime]:
    """
    Parse a datetime string from the API response.

    Handles "DD-MM-YYYY HH:mm:ss" format, which the API returns in
    Europe/Amsterdam local time. Returns a timezone-aware UTC datetime,
    or None if parsing fails.
    """
    if not value:
        return None
    try:
        naive = datetime.strptime(value, "%d-%m-%Y %H:%M:%S")
        return naive.replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass
    # Fallback: try ISO format
    try:
        from dateutil import parser as date_parser
        return date_parser.isoparse(value)
    except Exception:
        return None


# ── API client ──────────────────────────────────────────────────────


class TwoParkClient:
    """
    Lightweight HTTP client for the 2Park JSON API.

    Uses requests.Session for automatic cookie persistence (JSESSIONID).
    All methods are synchronous. Call login() before other operations.
    """

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        # Default headers matching the frontend's fetch() calls
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/x-www-form-urlencoded",
        })
        self._product_id: Optional[str] = None
        self._location_code: Optional[str] = None
        self._logged_in = False

    # ── Public API ──────────────────────────────────────────────

    def login(self) -> None:
        """
        Authenticate with the 2Park API.

        POST /check_credentials.json with email + password.
        Stores the JSESSIONID cookie in the session automatically.
        On success, also discovers the product_id and location code.
        """
        logger.info("Logging in to 2Park API...")
        data = {
            "email": self.email,
            "password": self.password,
            "locale": LOCALE,
        }
        resp = self._post("/check_credentials.json", data=data)
        self._require_ok(resp, "Login failed")
        self._logged_in = True
        logger.info("Login successful")

        # Discover product_id and location from categories
        self._discover_product()

    def get_balance(self) -> float:
        """
        Get the current account balance.

        Returns the balance as a float (EUR).
        """
        self._ensure_logged_in()
        logger.info("Fetching account balance...")

        resp = self._post("/get_balance.json", {
            "product_id": self._product_id,
            "locale": LOCALE,
        })
        self._require_ok(resp, "Failed to fetch balance")

        data = resp.get("data", {})
        balance_data = data.get("balance", {})

        # The balance may be in ble_parameters or as a direct value
        ble_params = balance_data.get("ble_parameters", [])
        if ble_params:
            # Find the BLE_THRESHOLD or first parameter with a numeric value
            for param in ble_params:
                try:
                    return float(param.get("prr_value", 0))
                except (ValueError, TypeError):
                    continue

        # Fallback: try to find balance elsewhere in the response
        logger.warning(f"Could not parse balance from response: {resp}")
        raise NoBalanceException("Balance data not found in API response")

    def get_active_reservations(self) -> List[Reservation]:
        """
        Get all active parking reservations.

        Calls /get_activations.json and parses the nested category →
        product → member → action structure.

        Returns a list of Reservation objects.
        """
        self._ensure_logged_in()
        logger.info("Fetching active reservations...")

        resp = self._post("/get_activations.json")
        self._require_ok(resp, "Failed to fetch activations")

        reservations: List[Reservation] = []
        categories = resp.get("data", {}).get("categories", [])

        for cat in categories:
            products = cat.get("cty_products", [])
            for prod in products:
                members = prod.get("pdt_members", [])
                for member in members:
                    mbr_identifier = member.get("mbr_identifier", "")
                    mbr_params = member.get("mbr_parameters", [])
                    actions = member.get("mbr_actions", [])

                    # Extract name from mbr_parameters (favorite name)
                    name = "Unknown"
                    for mp in mbr_params:
                        if mp.get("prr_label") == "NAME":
                            name = mp.get("prr_value", "Unknown")
                            break

                    for action in actions:
                        atn_state = action.get("atn_state", "")
                        if atn_state not in ("ACTIVE", "SCHEDULED"):
                            continue

                        atn_params = action.get("atn_parameters", [])
                        start_time = ""
                        end_time = ""

                        for ap in atn_params:
                            label = ap.get("prr_label", "")
                            value = ap.get("prr_value", "")
                            if label == "TIMESTART":
                                start_time = value
                            elif label == "TIMEEND":
                                end_time = value

                        if not mbr_identifier:
                            continue

                        reservations.append(Reservation(
                            name=name,
                            license_plate=mbr_identifier,
                            start_time=start_time,
                            end_time=end_time,
                        ))

        logger.info(f"Found {len(reservations)} active reservation(s)")
        return reservations

    def create_booking(
        self, license_plate: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Create a new parking booking.

        POST /start_action.json with the action parameters.
        Returns a dict with license_plate, start_time, end_time, status.
        """
        self._ensure_logged_in()
        logger.info(
            f"Creating booking for {license_plate} "
            f"from {start_time.isoformat()} to {end_time.isoformat()}"
        )

        # Build the action data structure matching the frontend
        action_data = {
            "action": {
                "atn_parameters": [
                    {"prr_label": "MBR_IDENT", "prr_value": license_plate},
                    {"prr_label": "TIMESTART", "prr_value": _format_api_datetime(start_time)},
                    {"prr_label": "TIMEEND", "prr_value": _format_api_datetime(end_time)},
                    {"prr_label": "LOCATION", "prr_value": self._location_code or ""},
                ]
            }
        }

        resp = self._post("/start_action.json", {
            "data": json.dumps(action_data),
            "locale": LOCALE,
            "product_id": self._product_id,
        })
        self._require_ok(resp, "Failed to create booking")

        # Verify by checking active reservations
        reservations = self.get_active_reservations()
        matched = None
        for res in reservations:
            if normalize_license_plate(res.license_plate) == normalize_license_plate(license_plate):
                matched = res
                break

        if matched:
            # Parse scraped times for comparison
            scraped_end = _parse_api_datetime(matched.end_time)
            if scraped_end:
                time_diff = abs((scraped_end - end_time).total_seconds()) / 60
                if time_diff > 10:
                    logger.warning(
                        f"End time mismatch: calculated={end_time.isoformat()}, "
                        f"scraped={scraped_end.isoformat()}, "
                        f"diff={time_diff:.1f} min — using calculated value"
                    )
                    final_end = end_time
                else:
                    final_end = scraped_end
            else:
                final_end = end_time

            return {
                "license_plate": license_plate,
                "start_time": start_time,
                "end_time": final_end,
                "status": "active",
            }

        logger.warning("Booking creation unclear — verification failed")
        return {
            "license_plate": license_plate,
            "start_time": start_time,
            "end_time": end_time,
            "status": "active",
        }

    def extend_booking(self, license_plate: str, additional_minutes: int) -> Dict[str, Any]:
        """
        Extend an existing booking by N minutes.

        Finds the action_id for the given license plate, then
        POST /extend_action.json with the new end time.
        Returns a dict with license_plate and new_end_time.
        """
        self._ensure_logged_in()
        logger.info(f"Extending booking for {license_plate} by {additional_minutes} min")

        # Find the action_id for this license plate
        action_id, current_end = self._find_action(license_plate)
        if not action_id:
            raise BookingNotFoundException(
                f"No active booking found for {license_plate}"
            )

        # Calculate new end time
        if current_end:
            new_end = current_end + timedelta(minutes=additional_minutes)
        else:
            new_end = datetime.now(timezone.utc) + timedelta(minutes=additional_minutes)

        resp = self._post("/extend_action.json", {
            "action_id": action_id,
            "locale": LOCALE,
            "product_id": self._product_id,
            "VALID_UNTIL": _format_api_datetime(new_end),
        })
        self._require_ok(resp, "Failed to extend booking")

        return {
            "license_plate": license_plate,
            "new_end_time": new_end,
        }

    def cancel_booking(self, license_plate: str) -> Dict[str, Any]:
        """
        Cancel an active booking.

        Finds the action_id for the given license plate, then
        POST /stop_action.json.
        Returns a dict with status and cancelled_at timestamp.
        """
        self._ensure_logged_in()
        logger.info(f"Cancelling booking for {license_plate}")

        # Find the action_id for this license plate
        action_id, _ = self._find_action(license_plate)
        if not action_id:
            raise BookingNotFoundException(
                f"No active booking found for {license_plate}"
            )

        resp = self._post("/stop_action.json", {
            "action_id": action_id,
            "locale": LOCALE,
            "product_id": self._product_id,
        })
        self._require_ok(resp, "Failed to cancel booking")

        return {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc),
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Lightweight health check — verifies the API is reachable.

        Unlike the old scraper_health_check(), this doesn't need a
        browser or login. It just pings the version endpoint and
        optionally tries a login to verify credentials.

        Returns a dict with status, timestamp, and response_time_ms.
        """
        import time
        start = time.monotonic()

        result: Dict[str, Any] = {
            "selectors_checked": [],
            "missing_selectors": [],
        }

        try:
            # Ping the version endpoint (no auth needed)
            r = self.session.get(
                "https://mijn.2park.nl/version.json",
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            version_data = r.json()
            result["version"] = version_data.get("env", "")

            # Try a login to verify credentials
            try:
                self.login()
                result["login_ok"] = True
                result["product_id"] = self._product_id
            except LoginFailedException as e:
                result["login_ok"] = False
                result["login_error"] = str(e)

            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            result["status"] = "ok" if result.get("login_ok", False) else "degraded"
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            result["response_time_ms"] = elapsed_ms
            return result

        except requests.RequestException as e:
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            return {
                "status": "error",
                "error": "ConnectionError",
                "message": f"Cannot reach 2Park API: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": elapsed_ms,
            }

    # ── Internal helpers ────────────────────────────────────────

    def _post(self, path: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make a POST request to the 2Park JSON API.

        Args:
            path: API path (e.g. "/check_credentials.json")
            data: Form-encoded data dict

        Returns:
            Parsed JSON response as dict.

        Raises:
            ScrapeErrorException: On HTTP or connection errors.
        """
        url = f"{BASE_URL}{path}"
        try:
            logger.debug(f"POST {url} data={data}")
            r = self.session.post(url, data=data, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.Timeout as e:
            raise TimeoutException(f"Request timed out: {path}") from e
        except requests.RequestException as e:
            raise ScrapeErrorException(f"API request failed: {path}: {e}") from e
        except json.JSONDecodeError as e:
            raise ScrapeErrorException(f"Invalid JSON response from {path}: {e}") from e

    def _require_ok(self, resp: Dict[str, Any], message: str) -> None:
        """
        Check the API response status and raise on failure.

        Maps API status codes to appropriate exceptions.
        """
        status = resp.get("status", {})
        code = status.get("code", {})
        major = code.get("major", "")
        minor = code.get("minor", "")
        msg = status.get("message", "")

        if major == "OK":
            return

        if major == "FAIL":
            if minor == "INVALID_CREDS":
                raise LoginFailedException(msg or "Invalid credentials")
            elif minor == "SESSION_TIMEOUT":
                # Try re-login once
                logger.info("Session timed out, re-logging in...")
                self._logged_in = False
                self.login()
                raise ScrapeErrorException(
                    "Session expired — re-logged in. Please retry the operation."
                )
            elif minor in ("NO_BALANCE", "INSUFFICIENT_BALANCE"):
                raise NoBalanceException(msg or "Insufficient balance")
            elif minor == "BOOKING_CONFLICT":
                raise BookingConflictException(msg or "Booking conflict")
            elif minor == "BOOKING_NOT_FOUND":
                raise BookingNotFoundException(msg or "Booking not found")
            else:
                raise ScrapeErrorException(f"{message}: {msg}")

        raise ScrapeErrorException(f"Unexpected API status: {major}/{minor}: {msg}")

    def _ensure_logged_in(self) -> None:
        """Ensure we have an active session, logging in if needed."""
        if not self._logged_in:
            self.login()

    def _discover_product(self) -> None:
        """
        Discover the user's product_id and location code.

        Calls /get_categories.json to find the first available product,
        then /get_product_locations.json to resolve the actual location
        code (the START parameter group only contains the schema, with
        None values for LOCATION).
        """
        logger.info("Discovering product configuration...")

        resp = self._post("/get_categories.json", {"locale": LOCALE})
        self._require_ok(resp, "Failed to fetch categories")

        categories = resp.get("data", {}).get("categories", [])

        for cat in categories:
            products = cat.get("cty_products", [])
            for prod in products:
                pdt_id = prod.get("pdt_id")
                is_blocked = prod.get("pdt_is_blocked", "false")

                if pdt_id and is_blocked == "false":
                    self._product_id = pdt_id

                    # Resolve the location code via the product locations
                    # endpoint (the START group only lists the schema).
                    self._location_code = self._discover_location(pdt_id)

                    logger.info(
                        f"Discovered product_id={self._product_id}, "
                        f"location_code={self._location_code}"
                    )
                    return

        raise ScrapeErrorException(
            "No available product found for this account"
        )

    def _discover_location(self, product_id: str) -> str:
        """
        Resolve the location code for a product.

        Calls /get_product_locations.json and returns the first
        LOCATION parameter value (e.g. "AVN_11").
        """
        try:
            resp = self._post("/get_product_locations.json", {
                "locale": LOCALE,
                "product_id": product_id,
                "location": "",
            })
            self._require_ok(resp, "Failed to fetch product locations")

            locations = resp.get("data", {}).get("locations", [])
            for loc in locations:
                for param in loc.get("ltn_parameters", []):
                    if param.get("prr_label") == "LOCATION":
                        return param.get("prr_value", "")
        except Exception as e:
            logger.warning(f"Could not resolve location code: {e}")

        return ""

    def _find_action(self, license_plate: str) -> tuple[Optional[str], Optional[datetime]]:
        """
        Find the action_id and end_time for a given license plate.

        Iterates through active reservations to find a matching plate.
        Returns (action_id, end_time) or (None, None).
        """
        target_plate = normalize_license_plate(license_plate)

        resp = self._post("/get_activations.json")
        self._require_ok(resp, "Failed to fetch activations")

        categories = resp.get("data", {}).get("categories", [])

        for cat in categories:
            products = cat.get("cty_products", [])
            for prod in products:
                members = prod.get("pdt_members", [])
                for member in members:
                    mbr_identifier = member.get("mbr_identifier", "")
                    if normalize_license_plate(mbr_identifier) != target_plate:
                        continue

                    actions = member.get("mbr_actions", [])
                    for action in actions:
                        if action.get("atn_state") not in ("ACTIVE", "SCHEDULED"):
                            continue

                        action_id = action.get("atn_id")
                        end_time = None
                        for ap in action.get("atn_parameters", []):
                            if ap.get("prr_label") == "TIMEEND":
                                end_time = _parse_api_datetime(ap.get("prr_value", ""))
                                break

                        if action_id:
                            return (action_id, end_time)

        return (None, None)

    def __enter__(self):
        """Context manager entry — auto-login."""
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit — cleanup session."""
        self.session.close()
        self._logged_in = False
