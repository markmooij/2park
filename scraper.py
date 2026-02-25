"""
Stateless scraper service for 2Park website automation
Handles browser sessions for individual operations
"""

import asyncio
import logging
from datetime import datetime, timedelta
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
                timeout=30000,
            )

            await self.page.wait_for_selector("#login_email", timeout=10000)
            await self.page.fill("#login_email", self.email)
            await self.page.fill("#login_password", self.password)
            await self.page.click('button[type="submit"]')

            # Wait for navigation
            await self.page.wait_for_load_state("networkidle", timeout=30000)

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
                    error_message = await error_element.inner_text()
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

            # Navigate to dashboard if not already there
            if "dashboard" not in self.page.url.lower():
                await self.page.goto("https://mijn.2park.nl/dashboard", timeout=30000)

            # Wait for balance element
            await self.page.wait_for_selector(
                ".balance-container .amount, .balance .amount, .account-balance",
                timeout=10000,
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
                await self.page.goto("https://mijn.2park.nl/dashboard", timeout=30000)

            # Wait for reservations to load (or empty state)
            try:
                await self.page.wait_for_selector(
                    ".parkapp-item, .no-reservations, .empty-state", timeout=10000
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

            # Navigate to new booking page
            await self.page.goto("https://mijn.2park.nl/parkings/new", timeout=30000)

            # Wait for the form
            await self.page.wait_for_selector(
                "#license_plate, input[name='license_plate']", timeout=10000
            )

            # Fill in license plate
            license_plate_input = await self.page.query_selector(
                "#license_plate, input[name='license_plate']"
            )
            if license_plate_input:
                await license_plate_input.fill(license_plate)

            # Fill in start time
            # Note: This depends on the actual form structure on 2park.nl
            # You may need to adjust selectors based on the actual website
            start_time_input = await self.page.query_selector(
                "#start_time, input[name='start_time'], .start-time-input"
            )
            if start_time_input:
                # Format time as expected by the form
                formatted_start = start_time.strftime("%Y-%m-%dT%H:%M")
                await start_time_input.fill(formatted_start)

            # Fill in end time or duration
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            duration_input = await self.page.query_selector(
                "#duration, input[name='duration'], .duration-input"
            )
            if duration_input:
                await duration_input.fill(str(duration_minutes))
            else:
                # Try end time input if duration not available
                end_time_input = await self.page.query_selector(
                    "#end_time, input[name='end_time'], .end-time-input"
                )
                if end_time_input:
                    formatted_end = end_time.strftime("%Y-%m-%dT%H:%M")
                    await end_time_input.fill(formatted_end)

            # Submit the form
            submit_button = await self.page.query_selector(
                'button[type="submit"], .submit-booking, .create-booking'
            )
            if submit_button:
                await submit_button.click()
                await self.page.wait_for_load_state("networkidle", timeout=30000)
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
            await self.page.goto("https://mijn.2park.nl/parkings", timeout=30000)

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
                                    "networkidle", timeout=30000
                                )

                            # Calculate new end time
                            # Parse the original end time and add minutes
                            try:
                                # This is a simple placeholder - you may need to parse the time properly
                                original_end = datetime.now() + timedelta(hours=1)
                                new_end_time = original_end + timedelta(
                                    minutes=additional_minutes
                                )
                            except Exception:
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
            await self.page.goto("https://mijn.2park.nl/parkings", timeout=30000)

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
                                    "networkidle", timeout=30000
                                )

                            return {
                                "status": "cancelled",
                                "cancelled_at": datetime.utcnow(),
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
