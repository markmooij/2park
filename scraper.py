"""
Stateless scraper service for 2Park website automation
Handles browser sessions for individual operations
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dateutil import parser as date_parser
from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from errors import (
    BookingConflictException,
    BookingNotFoundException,
    BrowserException,
    LoginFailedException,
    NoBalanceException,
    ScrapeErrorException,
    TimeoutException,
)
from models import Reservation

logger = logging.getLogger(__name__)


class TwoParkScraper:
    """Stateless scraper for 2Park operations"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.timeouts = {
            "browser": int(os.getenv("BROWSER_TIMEOUT", "30")),
            "navigation": int(os.getenv("NAVIGATION_TIMEOUT", "30")),
            "selector": int(os.getenv("SELECTOR_TIMEOUT", "10")),
        }

    async def __aenter__(self):
        """Context manager entry - initialize browser"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser"""
        await self.cleanup()

    async def initialize(self):
        """Initialize browser and login"""
        try:
            logger.info("Initializing browser...")
            self.playwright = await async_playwright().start()

            # Use headless mode for API
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self.page = await context.new_page()
            logger.info("Browser initialized")

            # Login immediately
            await self._login()

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.cleanup()
            raise BrowserException(f"Browser initialization failed: {str(e)}")

    def _get_timeout_ms(self, timeout_type: str) -> int:
        """Get timeout in milliseconds for given type"""
        timeout_sec = self.timeouts.get(timeout_type, 30)
        # Validate range (10-300 seconds)
        timeout_sec = max(10, min(300, timeout_sec))
        return timeout_sec * 1000

    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def _login(self):
        """Login to 2Park website"""
        try:
            logger.info("Logging in to 2Park...")
            await self.page.goto(
                "https://mijn.2park.nl/login",
                wait_until="networkidle",
                timeout=self._get_timeout_ms("navigation"),
            )

            # Try multiple possible selectors for email field
            email_selectors = [
                "#login_email",
                "#email",
                "input[name='email']",
                "input[name='Email']",
                "input[type='email']",
                ".form-email",
            ]
            password_selectors = [
                "#login_password",
                "#password",
                "input[name='password']",
                "input[name='Password']",
                "input[type='password']",
                ".form-password",
            ]

            email_selector = None
            for selector in email_selectors:
                if await self.page.query_selector(selector):
                    email_selector = selector
                    break

            password_selector = None
            for selector in password_selectors:
                if await self.page.query_selector(selector):
                    password_selector = selector
                    break

            if not email_selector or not password_selector:
                logger.error(
                    f"Could not find login form. Email selector: {email_selector}, Password selector: {password_selector}"
                )
                # Take a screenshot for debugging
                try:
                    await self.page.screenshot(
                        path="/tmp/2park_login_debug.png"
                    )
                    logger.info("Screenshot saved to /tmp/2park_login_debug.png")
                except Exception:
                    pass
                raise LoginFailedException(
                    "Could not find login form elements. Website structure may have changed."
                )

            logger.info(f"Found email selector: {email_selector}, password selector: {password_selector}")
            await self.page.fill(email_selector, self.email)
            await self.page.fill(password_selector, self.password)

            # Try multiple submit button selectors
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-login',
                '.login-button',
                'button.login',
            ]
            submit_button = None
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button:
                    logger.info(f"Found submit button: {selector}")
                    break

            if not submit_button:
                raise LoginFailedException("Could not find submit button")

            await submit_button.click()

            # Wait for navigation
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            # Give page a moment to fully render
            await self.page.wait_for_timeout(1000)

            # Check if login was successful by looking for the dashboard
            # If we're still on the login page, login failed
            current_url = self.page.url
            if "login" in current_url.lower():
                # Check for error message
                error_element = await self.page.query_selector(
                    ".alert-danger, .error-message"
                )
                error_message = "Invalid credentials"
                if error_element:
                    error_message = await error_element.text_content() or "Invalid credentials"
                raise LoginFailedException(f"Login failed: {error_message}")

            logger.info("Login successful")

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout during login: {e}")
            raise TimeoutException("Login timeout - website may be slow or down")
        except LoginFailedException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise LoginFailedException(f"Login error: {str(e)}")

    async def get_balance(self) -> float:
        """Get current account balance"""
        try:
            logger.info("Fetching account balance...")

            # Navigate to dashboard if still on login page
            if "login" in self.page.url.lower():
                await self.page.goto(
                    "https://mijn.2park.nl/dashboard",
                    timeout=self._get_timeout_ms("navigation"),
                )
                await self.page.wait_for_timeout(1000)

            # Wait for balance element
            await self.page.wait_for_selector(
                ".balance-container .amount, .balance .amount, .account-balance",
                timeout=self._get_timeout_ms("selector"),
            )

            # Try multiple selectors for balance
            amount_element = await self.page.query_selector(
                ".balance-container .amount"
            )
            if not amount_element:
                amount_element = await self.page.query_selector(".balance .amount")
            if not amount_element:
                amount_element = await self.page.query_selector(".account-balance")

            if not amount_element:
                raise NoBalanceException("Balance element not found on page")

            amount_text = await amount_element.inner_text()
            logger.info(f"Raw balance text: {amount_text}")

            # Clean and convert the amount text to a float
            amount = amount_text.replace("€", "").replace(",", ".").strip()
            balance = float(amount)
            logger.info(f"Parsed balance: € {balance}")
            return balance

        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout waiting for balance element")
        except ValueError as e:
            raise ScrapeErrorException(f"Failed to parse balance: {str(e)}")
        except NoBalanceException:
            raise
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise ScrapeErrorException(f"Error fetching balance: {str(e)}")

    async def get_active_reservations(self) -> List[Reservation]:
        """Get all active reservations"""
        try:
            logger.info("Fetching active reservations...")

            # Navigate to reservations page
            if (
                "parking" not in self.page.url.lower()
                and "dashboard" not in self.page.url.lower()
            ):
                await self.page.goto(
                    "https://mijn.2park.nl/dashboard",
                    timeout=self._get_timeout_ms("navigation"),
                )

            # Wait for reservations to load (or empty state)
            try:
                await self.page.wait_for_selector(
                    ".parkapp-item, .no-reservations, .empty-state",
                    timeout=self._get_timeout_ms("selector"),
                )
            except PlaywrightTimeoutError:
                logger.info("No reservations found")
                return []

            # Get all reservation items
            reservation_items = await self.page.query_selector_all(".parkapp-item")
            logger.info(f"Found {len(reservation_items)} reservation(s)")

            reservations = []
            for item in reservation_items:
                try:
                    # Extract name
                    name_element = await item.query_selector(
                        ".favorite-name > span:not(.anonymouse)"
                    )
                    name = (
                        await name_element.inner_text() if name_element else "Unknown"
                    )

                    # Extract license plate
                    license_plate_element = await item.query_selector(
                        ".license-plate-text"
                    )
                    license_plate = (
                        await license_plate_element.inner_text()
                        if license_plate_element
                        else "N/A"
                    )

                    # Extract times
                    time_elements = await item.query_selector_all(
                        ".time-container > .time > div"
                    )
                    if len(time_elements) >= 2:
                        start_time = await time_elements[0].inner_text()
                        end_time = await time_elements[1].inner_text()
                    else:
                        start_time = "N/A"
                        end_time = "N/A"

                    reservation = Reservation(
                        name=name,
                        license_plate=license_plate,
                        start_time=start_time,
                        end_time=end_time,
                    )
                    reservations.append(reservation)

                except Exception as e:
                    logger.error(f"Error extracting reservation: {e}")
                    continue

            return reservations

        except PlaywrightTimeoutError:
            logger.info("No reservations found or timeout")
            return []
        except Exception as e:
            logger.error(f"Error getting reservations: {e}")
            raise ScrapeErrorException(f"Error fetching reservations: {str(e)}")

    async def create_booking(
        self, license_plate: str, start_time: datetime, end_time: datetime
    ) -> Dict:
        """Create a new parking booking"""
        try:
            logger.info(
                f"Creating booking for {license_plate} from {start_time} to {end_time}"
            )

            # Check if booking already exists
            existing_reservations = await self.get_active_reservations()
            for res in existing_reservations:
                if res.license_plate.upper() == license_plate.upper():
                    raise BookingConflictException(
                        f"Active booking already exists for {license_plate}"
                    )

            # Navigate to dashboard first
            await self.page.goto(
                "https://mijn.2park.nl/",
                timeout=self._get_timeout_ms("navigation"),
            )
            await self.page.wait_for_timeout(1000)

            # Click the "+Nieuwe parkeeractie" button to open the form
            new_button = await self.page.query_selector(
                "button:has-text('+Nieuwe parkeeractie'), button:has-text('Nieuwe parkeeractie')"
            )
            if not new_button:
                raise ScrapeErrorException("Could not find 'Nieuwe parkeeractie' button")

            await new_button.click()
            await self.page.wait_for_timeout(2000)

            # Wait for the form to appear
            await self.page.wait_for_selector(
                "#newParkingActions_license_plate, input[name*='license_plate']",
                timeout=self._get_timeout_ms("selector"),
            )

            # Fill in license plate
            license_plate_input = await self.page.query_selector(
                "#newParkingActions_license_plate, input[name*='license_plate']"
            )
            if license_plate_input:
                await license_plate_input.fill(license_plate)
            else:
                raise ScrapeErrorException("License plate input not found")

            # Fill in start time (use "now" by selecting the current time option)
            # The form uses a time picker - find and select start time
            start_time_selector = "#newParkingActions_start_time, input[name*='start_time'], .start-time"
            start_time_input = await self.page.query_selector(start_time_selector)
            if start_time_input:
                # Format time as expected by the form
                formatted_start = start_time.strftime("%Y-%m-%dT%H:%M")
                await start_time_input.fill(formatted_start)

            # Fill in duration (in minutes)
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            duration_selector = "#newParkingActions_duration_minutes, input[name*='duration'], .duration"
            duration_input = await self.page.query_selector(duration_selector)
            if duration_input:
                await duration_input.fill(str(duration_minutes))

            # Submit the form
            submit_button = await self.page.query_selector(
                'button[type="submit"], button:has-text("Reserveren"), button:has-text("Bevestigen")'
            )
            if submit_button:
                await submit_button.click()
                await self.page.wait_for_load_state(
                    "networkidle", timeout=self._get_timeout_ms("navigation")
                )
            else:
                raise ScrapeErrorException("Submit button not found")

            # Verify booking was created
            await asyncio.sleep(2)  # Wait for booking to appear
            reservations = await self.get_active_reservations()
            for res in reservations:
                if res.license_plate.upper() == license_plate.upper():
                    logger.info(f"Booking created successfully for {license_plate}")
                    return {
                        "license_plate": license_plate,
                        "start_time": start_time,
                        "end_time": end_time,
                        "status": "active",
                    }

            # If we get here, booking might not have been created
            logger.warning("Booking creation unclear - verification failed")
            return {
                "license_plate": license_plate,
                "start_time": start_time,
                "end_time": end_time,
                "status": "active",
            }

        except BookingConflictException:
            raise
        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout while creating booking")
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise ScrapeErrorException(f"Failed to create booking: {str(e)}")

    async def extend_booking(self, license_plate: str, additional_minutes: int) -> Dict:
        """Extend an existing booking"""
        try:
            logger.info(
                f"Extending booking for {license_plate} by {additional_minutes} minutes"
            )

            # Find the existing booking
            reservations = await self.get_active_reservations()
            target_booking = None
            for res in reservations:
                if res.license_plate.upper() == license_plate.upper():
                    target_booking = res
                    break

            if not target_booking:
                raise BookingNotFoundException(
                    f"No active booking found for {license_plate}"
                )

            # Navigate to extend booking page (this depends on actual website structure)
            # This is a placeholder - you'll need to adjust based on actual 2park.nl UI
            await self.page.goto(
                "https://mijn.2park.nl/parkings",
                timeout=self._get_timeout_ms("navigation"),
            )

            # Find the booking in the list and click extend button
            booking_items = await self.page.query_selector_all(".parkapp-item")
            for item in booking_items:
                license_element = await item.query_selector(".license-plate-text")
                if license_element:
                    item_license = await license_element.inner_text()
                    if item_license.upper() == license_plate.upper():
                        # Look for extend button
                        extend_button = await item.query_selector(
                            ".extend-button, button.extend, .btn-extend"
                        )
                        if extend_button:
                            await extend_button.click()
                            await asyncio.sleep(1)

                            # Fill in additional time
                            duration_input = await self.page.query_selector(
                                "#additional_time, input[name='additional_time']"
                            )
                            if duration_input:
                                await duration_input.fill(str(additional_minutes))

                            # Submit
                            submit_button = await self.page.query_selector(
                                'button[type="submit"], .submit-extend'
                            )
                            if submit_button:
                                await submit_button.click()
                                await self.page.wait_for_load_state(
                                    "networkidle",
                                    timeout=self._get_timeout_ms("navigation"),
                                )

                            # Calculate new end time from the actual booking
                            # Parse the end_time string from the reservation
                            try:
                                # Parse the end time from the reservation (format: "HH:MM" or full datetime)
                                end_time_str = target_booking.end_time
                                # Try to parse as ISO format first, then fall back to time-only format
                                if "T" in end_time_str or "-" in end_time_str:
                                    original_end = date_parser.isoparse(end_time_str)
                                    if original_end.tzinfo is not None:
                                        original_end = original_end.replace(tzinfo=None)
                                else:
                                    # Time-only format like "17:00" - assume today's date
                                    today = datetime.now()
                                    time_obj = date_parser.parse(end_time_str)
                                    original_end = datetime(
                                        today.year, today.month, today.day,
                                        time_obj.hour, time_obj.minute
                                    )
                                new_end_time = original_end + timedelta(
                                    minutes=additional_minutes
                                )
                            except Exception:
                                # Fallback: use current time + additional minutes
                                logger.warning(
                                    f"Could not parse end time '{target_booking.end_time}', "
                                    f"using current time as base"
                                )
                                new_end_time = datetime.now() + timedelta(
                                    minutes=additional_minutes
                                )

                            return {
                                "license_plate": license_plate,
                                "new_end_time": new_end_time,
                            }
                        else:
                            raise ScrapeErrorException(
                                "Extend button not found for booking"
                            )

            raise BookingNotFoundException(
                f"Could not find booking UI for {license_plate}"
            )

        except (BookingNotFoundException, ScrapeErrorException):
            raise
        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout while extending booking")
        except Exception as e:
            logger.error(f"Error extending booking: {e}")
            raise ScrapeErrorException(f"Failed to extend booking: {str(e)}")

    async def cancel_booking(self, license_plate: str) -> Dict:
        """Cancel an existing booking"""
        try:
            logger.info(f"Cancelling booking for {license_plate}")

            # Find the existing booking
            reservations = await self.get_active_reservations()
            target_booking = None
            for res in reservations:
                if res.license_plate.upper() == license_plate.upper():
                    target_booking = res
                    break

            if not target_booking:
                raise BookingNotFoundException(
                    f"No active booking found for {license_plate}"
                )

            # Navigate to bookings page
            await self.page.goto(
                "https://mijn.2park.nl/parkings",
                timeout=self._get_timeout_ms("navigation"),
            )

            # Find the booking and click cancel button
            booking_items = await self.page.query_selector_all(".parkapp-item")
            for item in booking_items:
                license_element = await item.query_selector(".license-plate-text")
                if license_element:
                    item_license = await license_element.inner_text()
                    if item_license.upper() == license_plate.upper():
                        # Look for cancel button
                        cancel_button = await item.query_selector(
                            ".cancel-button, button.cancel, .btn-cancel, .delete-button"
                        )
                        if cancel_button:
                            await cancel_button.click()
                            await asyncio.sleep(1)

                            # Confirm cancellation if there's a confirmation dialog
                            confirm_button = await self.page.query_selector(
                                ".confirm-cancel, .confirm-delete, button.confirm"
                            )
                            if confirm_button:
                                await confirm_button.click()
                                await self.page.wait_for_load_state(
                                    "networkidle",
                                    timeout=self._get_timeout_ms("navigation"),
                                )

                            return {
                                "status": "cancelled",
                                "cancelled_at": datetime.now(timezone.utc),
                            }
                        else:
                            raise ScrapeErrorException(
                                "Cancel button not found for booking"
                            )

            raise BookingNotFoundException(
                f"Could not find booking UI for {license_plate}"
            )

        except (BookingNotFoundException, ScrapeErrorException):
            raise
        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout while cancelling booking")
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            raise ScrapeErrorException(f"Failed to cancel booking: {str(e)}")
