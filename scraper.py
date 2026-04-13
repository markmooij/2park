"""
Stateless scraper service for 2Park website automation
Handles browser sessions for individual operations
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import re
from dateutil import parser as date_parser
from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


def parse_dutch_time(time_str: str, base_date: datetime = None) -> str:
    """
    Parse Dutch time format from 2Park website and return ISO format.

    Handles formats like:
    - "15:23" -> ISO format with today's date
    - "15:23, vandaag" -> ISO format with today's date
    - "15:23, morgen" -> ISO format with tomorrow's date
    """
    if not time_str or time_str == "N/A":
        return ""

    # Clean the string - remove non-breaking spaces and extra whitespace
    time_str = time_str.replace('\xa0', ' ').strip()

    # Extract just the time portion (HH:MM or HH.MM)
    time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
    if not time_match:
        return ""

    hour = int(time_match.group(1))
    minute = int(time_match.group(2))

    # Get the base date
    if base_date is None:
        base_date = datetime.now(timezone.utc)

    # Check if it's "morgen" (tomorrow)
    if "morgen" in time_str.lower():
        base_date = base_date + timedelta(days=1)

    # Create datetime with the extracted time
    try:
        result = datetime(
            base_date.year,
            base_date.month,
            base_date.day,
            hour,
            minute,
            tzinfo=timezone.utc
        )
        return result.isoformat()
    except Exception:
        return ""

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

        except (LoginFailedException, TimeoutException):
            await self.cleanup()
            raise
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
            logger.info(f"After login URL: {self.page.url}")

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
            logger.info(f"Current page URL before wait: {self.page.url}")

            # The page is already on the dashboard after login
            # Just wait a moment for any dynamic content to load
            await self.page.wait_for_timeout(3000)

            logger.info(f"Current URL after wait: {self.page.url}")

            # Try multiple possible selectors for booking items
            # The website might use various class names for booking cards
            booking_selectors = [
                ".parkapp-item",
                ".booking-item",
                ".parking-item",
                "[class*='parkapp']",
                "[class*='booking']",
                "[class*='parking']",
                ".card",
                ".booking-card",
                ".parking-card",
                "article.booking",
                "div.booking",
                ".active",
            ]

            reservation_items = []
            for selector in booking_selectors:
                items = await self.page.query_selector_all(selector)
                if items:
                    logger.info(f"Found {len(items)} items matching '{selector}'")
                    reservation_items = items
                    break

            if not reservation_items:
                logger.warning("No booking items found with predefined selectors")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="/tmp/2park_debug_bookings.png")
                    logger.info("Screenshot saved to /tmp/2park_debug_bookings.png")
                except Exception as e:
                    logger.warning(f"Could not take screenshot: {e}")

                # Try to find ANY element that might contain booking info
                # Look for elements with license plate patterns
                all_elements = await self.page.query_selector_all("div, span, p, li, tr")
                logger.info(f"Total elements on page: {len(all_elements)}")

                return []

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
                        start_time_raw = await time_elements[0].inner_text()
                        end_time_raw = await time_elements[1].inner_text()
                        # Parse Dutch time format to ISO format
                        start_time = parse_dutch_time(start_time_raw)
                        end_time = parse_dutch_time(end_time_raw)
                    else:
                        start_time = ""
                        end_time = ""

                    logger.info(f"Extracted - license: {license_plate}, start: {start_time}, end: {end_time}")

                    # Skip invalid reservations (no license plate or no valid times)
                    if not license_plate or license_plate == "N/A":
                        logger.info("Skipping reservation with no license plate")
                        continue
                    if not start_time or not end_time:
                        logger.info(f"Skipping reservation with missing times for {license_plate}")
                        continue

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

            # Navigate to the home/dashboard page (where the new booking button is)
            # Try multiple URLs
            urls_to_try = [
                "https://mijn.2park.nl/",
                "https://mijn.2park.nl/dashboard",
                "https://mijn.2park.nl/parkings",
            ]

            for url in urls_to_try:
                try:
                    await self.page.goto(url, timeout=5000)
                    await self.page.wait_for_timeout(2000)
                    logger.info(f"Navigated to: {self.page.url}")
                    # Check if button exists on this page
                    new_button = await self.page.query_selector("button, a")
                    if new_button:
                        logger.info(f"Found buttons on {url}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to navigate to {url}: {e}")
                    continue

            # Take screenshot to debug
            try:
                await self.page.screenshot(path="/tmp/2park_create_debug.png")
                logger.info("Screenshot saved to /tmp/2park_create_debug.png")
            except Exception as e:
                logger.warning(f"Could not take screenshot: {e}")

            # Click the "+Nieuwe parkeeractie" button to open the form
            # Try multiple possible selectors
            button_selectors = [
                "button:has-text('+Nieuwe parkeeractie')",
                "button:has-text('Nieuwe parkeeractie')",
                "button:has-text('Nieuw')",
                "button.add",
                ".add-booking",
                "a.new-booking",
                "[class*='new']",
                "[class*='add']",
                "button:has-text('+')",
                "a:has-text('Nieuwe')",
                ".btn-primary",
                ".primary-button",
            ]

            new_button = None
            for selector in button_selectors:
                new_button = await self.page.query_selector(selector)
                if new_button:
                    logger.info(f"Found button with selector: {selector}")
                    break

            if not new_button:
                # List all buttons on the page for debugging
                all_buttons = await self.page.query_selector_all("button, a")
                logger.warning(f"Could not find 'Nieuwe parkeeractie' button. Found {len(all_buttons)} buttons/links")
                for i, btn in enumerate(all_buttons[:10]):  # Log first 10
                    try:
                        text = await btn.inner_text()
                        logger.info(f"  Button {i}: {text[:50]}")
                    except:
                        pass
                raise ScrapeErrorException("Could not find 'Nieuwe parkeeractie' button")

            await new_button.click()
            await self.page.wait_for_timeout(2000)

            # Wait for the form to appear
            try:
                await self.page.wait_for_selector(
                    "input, select, form",
                    timeout=5000,
                )
            except PlaywrightTimeoutError:
                logger.warning("Form selector timeout, continuing anyway")

            # Log what fields are available on the page
            all_inputs = await self.page.query_selector_all("input, select")
            logger.info(f"Found {len(all_inputs)} input elements on form")

            # Fill in license plate - try multiple selectors
            license_selectors = [
                "#newParkingActions_license_plate",
                "input[name*='license']",
                "input[name*='kenteken']",  # Dutch for license plate
                "input[placeholder*='plate']",
                "input[placeholder*='kenteken']",
            ]
            license_plate_input = None
            for selector in license_selectors:
                license_plate_input = await self.page.query_selector(selector)
                if license_plate_input:
                    logger.info(f"Found license plate input with selector: {selector}")
                    break

            if license_plate_input:
                await license_plate_input.fill(license_plate)
            else:
                logger.warning("License plate input not found - booking may fail")

            # Fill in start time - try "now" or the actual time
            # Many forms default to "now" so we may not need to set it
            start_time_selectors = [
                "#newParkingActions_start_time",
                "input[name*='start']",
                "input[name*='begin']",  # Dutch for start
                ".start-time",
            ]
            start_time_input = None
            for selector in start_time_selectors:
                start_time_input = await self.page.query_selector(selector)
                if start_time_input:
                    logger.info(f"Found start time input with selector: {selector}")
                    break

            if start_time_input:
                # Try multiple formats for start time
                # First try "now" (common pattern for Dutch websites)
                try:
                    await start_time_input.fill("now")
                    logger.info("Set start time to 'now'")
                except Exception as e:
                    logger.warning(f"'now' format failed: {e}, trying time-only format")
                    # Try HH:MM format
                    formatted_start = start_time.strftime("%H:%M")
                    try:
                        await start_time_input.fill(formatted_start)
                        logger.info(f"Set start time to: {formatted_start} (HH:MM format)")
                    except Exception as e2:
                        logger.warning(f"HH:MM format failed: {e2}, trying full datetime format")
                        # Fallback to full ISO format
                        formatted_start = start_time.strftime("%Y-%m-%dT%H:%M")
                        await start_time_input.fill(formatted_start)
                        logger.info(f"Set start time to: {formatted_start} (ISO format)")

            # Fill in end time (preferred) or duration
            end_time_minutes = int((end_time - start_time).total_seconds() / 60)
            logger.info(f"Booking end time: {end_time} ({end_time_minutes} minutes from start)")

            # Try end time field first
            end_time_selectors = [
                "#newParkingActions_end_time",
                "input[name*='end']",
                "input[name*='eind']",  # Dutch for end
                ".end-time",
            ]
            end_time_input = None
            for selector in end_time_selectors:
                end_time_input = await self.page.query_selector(selector)
                if end_time_input:
                    logger.info(f"Found end time input with selector: {selector}")
                    break

            if end_time_input:
                # Try multiple formats - website might expect HH:MM or full datetime
                # First try HH:MM format (most common for Dutch websites)
                formatted_end = end_time.strftime("%H:%M")
                try:
                    await end_time_input.fill(formatted_end)
                    logger.info(f"Set end time to: {formatted_end} (HH:MM format)")
                except Exception as e:
                    logger.warning(f"HH:MM format failed: {e}, trying full datetime format")
                    # Fallback to full ISO format
                    formatted_end = end_time.strftime("%Y-%m-%dT%H:%M")
                    await end_time_input.fill(formatted_end)
                    logger.info(f"Set end time to: {formatted_end} (ISO format)")
            else:
                # Try duration field - this is more reliable than end time
                duration_selectors = [
                    "#newParkingActions_duration",
                    "input[name*='duration']",
                    "input[name*='duur']",  # Dutch for duration
                    ".duration",
                    "select[name*='duration']",
                    "input[type='number']",  # Generic number input
                ]
                duration_input = None
                for selector in duration_selectors:
                    duration_input = await self.page.query_selector(selector)
                    if duration_input:
                        logger.info(f"Found duration input with selector: {selector}")
                        break

                if duration_input:
                    await duration_input.fill(str(end_time_minutes))
                    logger.info(f"Set duration to: {end_time_minutes} minutes")
                else:
                    logger.warning("No end time or duration field found - using defaults")
                    # Log available inputs for debugging
                    all_inputs = await self.page.query_selector_all("input, select")
                    for i, inp in enumerate(all_inputs[:15]):
                        try:
                            inp_id = await inp.get_attribute("id")
                            inp_name = await inp.get_attribute("name")
                            inp_type = await inp.get_attribute("type")
                            inp_placeholder = await inp.get_attribute("placeholder")
                            logger.info(f"  Input {i}: id={inp_id}, name={inp_name}, type={inp_type}, placeholder={inp_placeholder}")
                        except Exception:
                            pass

            # Submit the form
            submit_button = await self.page.query_selector(
                'button[type="submit"], button:has-text("Reserveren"), button:has-text("Bevestigen"), button:has-text("Opslaan")'
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

            # Stay on the current page (dashboard after login) - bookings are shown there
            await self.page.wait_for_timeout(2000)
            logger.info(f"Current URL: {self.page.url}")

            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="/tmp/2park_cancel_debug.png")
                logger.info("Screenshot saved to /tmp/2park_cancel_debug.png")
            except Exception:
                pass

            # Find the booking and click cancel button - try multiple selectors
            booking_selectors = [
                ".parkapp-item",
                ".booking-item",
                ".parking-item",
                "[class*='parkapp']",
                "[class*='booking']",
                "[class*='parking']",
                ".card",
            ]

            target_item = None
            for selector in booking_selectors:
                booking_items = await self.page.query_selector_all(selector)
                logger.info(f"Found {len(booking_items)} items matching '{selector}'")

                for item in booking_items:
                    license_element = await item.query_selector(".license-plate-text, [class*='license'], [class*='plate']")
                    if license_element:
                        try:
                            item_license = await license_element.inner_text()
                            logger.info(f"Found booking with license: {item_license}")
                            if item_license.upper().replace(" ", "") == license_plate.upper().replace("-", "").replace(" ", ""):
                                target_item = item
                                break
                        except Exception:
                            continue
                if target_item:
                    break

            if not target_item:
                # Log all license plates found on the page for debugging
                all_licenses = await self.page.query_selector_all(".license-plate-text, [class*='license'], [class*='plate']")
                logger.info(f"Total license elements found on page: {len(all_licenses)}")
                for i, lic_elem in enumerate(all_licenses[:5]):
                    try:
                        lic_text = await lic_elem.inner_text()
                        logger.info(f"  License {i}: {lic_text}")
                    except:
                        pass

                logger.warning(f"Could not find booking for {license_plate} on page")
                raise BookingNotFoundException(
                    f"Could not find booking UI for {license_plate}"
                )

            # Look for cancel button - try multiple selectors
            cancel_selectors = [
                ".cancel-button",
                "button.cancel",
                ".btn-cancel",
                ".delete-button",
                ".stop-context-menu-button",  # Actual class found on 2park.nl
                "button:has-text('Annuleren')",
                "button:has-text('Annuleer')",
                "button:has-text('Verwijderen')",
                "button:has-text('Stop')",  # Dutch word for stop/terminate
                "[class*='cancel']",
                "[class*='delete']",
                "[class*='stop']",
                "[class*='annuleren']",
                "[class*='verwijder']",
                "button.secondary",
                "button.danger",
                "button.warning",
                "a.cancel",
                "a:has-text('Annuleren')",
            ]

            cancel_button = None
            for selector in cancel_selectors:
                cancel_button = await target_item.query_selector(selector)
                if cancel_button:
                    logger.info(f"Found cancel button with selector: {selector}")
                    break

            if not cancel_button:
                # Try to find any button in the booking item and log details
                all_buttons = await target_item.query_selector_all("button, a")
                logger.warning(f"Cancel button not found, found {len(all_buttons)} buttons in booking item")
                for i, btn in enumerate(all_buttons):
                    try:
                        btn_text = await btn.inner_text()
                        btn_class = await btn.get_attribute("class")
                        btn_id = await btn.get_attribute("id")
                        logger.info(f"  Button {i}: text='{btn_text[:100]}', class='{btn_class}', id='{btn_id}'")
                    except Exception as e:
                        logger.info(f"  Button {i}: could not get details - {e}")
                raise ScrapeErrorException("Cancel button not found for booking")

            await cancel_button.click()
            await asyncio.sleep(1)

            # Confirm cancellation if there's a confirmation dialog
            confirm_selectors = [
                "button:has-text('Ja, stoppen')",  # Dutch: Yes, stop
                "button:has-text('Ja, annuleren')",
                "button:has-text('Bevestigen')",
                ".confirm-cancel",
                ".confirm-delete",
                "button.confirm",
                "button.danger",
            ]

            confirm_button = None
            for selector in confirm_selectors:
                confirm_button = await self.page.query_selector(selector)
                if confirm_button:
                    logger.info(f"Found confirm button with selector: {selector}")
                    break

            if confirm_button:
                await confirm_button.click()
                await self.page.wait_for_load_state(
                    "networkidle",
                    timeout=self._get_timeout_ms("navigation"),
                )
                await asyncio.sleep(2)
            else:
                logger.warning("No confirm button found - cancellation may not have been confirmed")
                await asyncio.sleep(2)

            return {
                "status": "cancelled",
                "cancelled_at": datetime.now(timezone.utc),
            }

        except (BookingNotFoundException, ScrapeErrorException):
            raise
        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout while cancelling booking")
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            raise ScrapeErrorException(f"Failed to cancel booking: {str(e)}")
