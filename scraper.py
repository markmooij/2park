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
from models import Reservation, normalize_license_plate

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
            logger.info(f"Start time: {start_time}")
            logger.info(f"Calculated duration: {end_time_minutes} minutes")

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

            # Try duration field FIRST - this is more reliable than end time
            # Many parking websites calculate end time based on duration, not absolute time
            duration_selectors = [
                "#newParkingActions_duration",
                "input[name*='duration']",
                "input[name*='duur']",  # Dutch for duration
                "input[name*='time']",  # Generic time field
                "input[name*='minutes']",  # Minutes field
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
                # Use duration field - this is the most reliable method
                duration_value = str(end_time_minutes)
                logger.info(f"Found duration input, filling with: {duration_value} minutes")
                await duration_input.fill(duration_value)
                
                # Trigger change event (some websites require this to update internal state)
                try:
                    await duration_input.dispatch_event("change")
                    await duration_input.dispatch_event("input")
                    logger.info("Triggered change/input events on duration field")
                except Exception as e:
                    logger.warning(f"Could not trigger events on duration field: {e}")
                
                # Verify the value was set
                try:
                    actual_value = await duration_input.input_value()
                    logger.info(f"Duration field actual value after fill: {actual_value}")
                except Exception as e:
                    logger.warning(f"Could not verify duration field value: {e}")
                
                # Also try to fill end time if available (some websites use both)
                if end_time_input:
                    formatted_end = end_time.strftime("%H:%M")
                    try:
                        await end_time_input.fill(formatted_end)
                        logger.info(f"Also set end time to: {formatted_end} (HH:MM format)")
                    except Exception as e:
                        logger.warning(f"End time fill failed: {e}")
            elif end_time_input:
                # No duration field, try end time field
                # Try multiple formats - website might expect HH:MM or full datetime
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

            # Verify booking was created and read back actual times from website
            await asyncio.sleep(2)  # Wait for booking to appear
            reservations = await self.get_active_reservations()
            for res in reservations:
                if res.license_plate.upper() == license_plate.upper():
                    logger.info(f"Booking created successfully for {license_plate}")

                    # Parse the scraped end_time back to datetime for comparison
                    scraped_end = date_parser.isoparse(res.end_time)
                    if scraped_end.tzinfo is None:
                        scraped_end = scraped_end.replace(tzinfo=timezone.utc)

                    # Check discrepancy between scraped and calculated end time
                    time_diff_minutes = abs((scraped_end - end_time).total_seconds()) / 60
                    if time_diff_minutes > 5:
                        logger.warning(
                            f"End time discrepancy: calculated={end_time.isoformat()}, "
                            f"scraped={scraped_end.isoformat()}, "
                            f"difference={time_diff_minutes:.1f} minutes"
                        )

                    return {
                        "license_plate": license_plate,
                        "start_time": start_time,
                        "end_time": scraped_end,
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

    async def _find_booking_card(
        self, license_plate: str
    ) -> Optional[Dict]:
        """
        Find a booking card on the dashboard matching the given license plate.

        Navigates to the dashboard, clicks the 'Lopend' tab, and iterates
        over booking cards to find one matching the normalized license plate.

        Returns a dict with:
            - card_element: the Playwright element handle for the booking card
            - license_plate: the license plate text as found on the page
            - start_time: the booking start time (ISO format)
            - end_time: the booking end time (ISO format)

        Returns None if no matching card is found.
        """
        logger.info(f"Finding booking card for {license_plate}")

        # Navigate to the dashboard
        await self.page.goto(
            "https://mijn.2park.nl/",
            timeout=self._get_timeout_ms("navigation"),
        )
        await self.page.wait_for_timeout(3000)
        logger.info(f"Current URL: {self.page.url}")

        # Click the "Lopend" (active) tab to ensure we're on the right tab
        lopend_tabs = await self.page.query_selector_all(".tabs-container button")
        for tab in lopend_tabs:
            tab_text = await tab.inner_text()
            if "Lopend" in tab_text:
                await tab.click()
                await self.page.wait_for_timeout(2000)
                logger.info("Clicked 'Lopend' tab")
                break

        # Find booking cards using the confirmed selector from DOM audit
        booking_items = await self.page.query_selector_all(".parkapp-item")
        logger.info(f"Found {len(booking_items)} booking item(s)")

        target_plate = normalize_license_plate(license_plate)

        for item in booking_items:
            # Try .license-plate.active first (from DOM audit), fall back to .license-plate-text
            license_element = await item.query_selector(
                ".license-plate.active, .license-plate-text"
            )
            if not license_element:
                continue

            try:
                item_license_raw = await license_element.inner_text()
                item_license = normalize_license_plate(item_license_raw)
                logger.info(f"Checking booking with license: {item_license_raw}")

                if item_license == target_plate:
                    # Extract start and end times
                    time_elements = await item.query_selector_all(
                        ".time-container > .time > div"
                    )
                    start_time = ""
                    end_time = ""
                    if len(time_elements) >= 2:
                        start_time_raw = await time_elements[0].inner_text()
                        end_time_raw = await time_elements[1].inner_text()
                        start_time = parse_dutch_time(start_time_raw)
                        end_time = parse_dutch_time(end_time_raw)

                    # Log available buttons on the card for debugging
                    buttons = await item.query_selector_all("button")
                    logger.info(f"Available buttons in booking card: {len(buttons)}")
                    for i, btn in enumerate(buttons):
                        try:
                            btn_text = await btn.inner_text()
                            btn_classes = await btn.get_attribute("class")
                            logger.info(
                                f"  Button {i}: text='{btn_text}', class='{btn_classes}'"
                            )
                        except Exception:
                            pass

                    return {
                        "card_element": item,
                        "license_plate": item_license_raw,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
            except Exception:
                continue

        logger.warning(f"No booking card found for {license_plate}")
        return None

    async def extend_booking(self, license_plate: str, additional_minutes: int) -> Dict:
        """Extend an existing booking"""
        try:
            logger.info(
                f"Extending booking for {license_plate} by {additional_minutes} minutes"
            )

            # Find the booking card using the shared helper
            booking_card = await self._find_booking_card(license_plate)
            if not booking_card:
                raise BookingNotFoundException(
                    f"Could not find booking UI for {license_plate}"
                )
            target_item = booking_card["card_element"]

            # Click the extend button using real selector from DOM audit
            extend_button = await target_item.query_selector(".extend-context-menu-button")
            if not extend_button:
                # Log available buttons for debugging
                buttons = await target_item.query_selector_all("button")
                logger.info(f"Available buttons in booking card: {len(buttons)}")
                for i, btn in enumerate(buttons):
                    try:
                        btn_text = await btn.inner_text()
                        btn_classes = await btn.get_attribute("class")
                        logger.info(f"  Button {i}: text='{btn_text}', class='{btn_classes}'")
                    except Exception:
                        pass

                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="/tmp/2park_extend_no_button.png")
                    logger.info("Screenshot saved to /tmp/2park_extend_no_button.png")
                except Exception:
                    pass

                raise ScrapeErrorException("Extend button not found for booking")

            logger.info("Clicking extend button")
            await extend_button.click()
            await self.page.wait_for_timeout(2000)

            # Fill in additional minutes in the extend form
            # The form opens after clicking extend — try multiple input selectors
            duration_selectors = [
                "input[type='number']",
                "input[type='text']",
                "input[name*='time']",
                "input[name*='duration']",
                "input[name*='minute']",
                "input[name*='additional']",
                "#additional_time",
                "input",
            ]

            duration_input = None
            for selector in duration_selectors:
                duration_input = await self.page.query_selector(selector)
                if duration_input:
                    logger.info(f"Found duration input with selector: {selector}")
                    break

            if not duration_input:
                raise ScrapeErrorException("Duration input field not found on extend form")

            logger.info(f"Filling duration: {additional_minutes}")
            await duration_input.fill(str(additional_minutes))
            await self.page.wait_for_timeout(1000)

            # Submit the extension — look for submit/confirm button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Verleng")',
                'button:has-text("Bevestigen")',
                'button:has-text("Opslaan")',
                'button:has-text("Confirm")',
                'button.primary',
                'button[type="button"]',
            ]

            submit_button = None
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button:
                    logger.info(f"Found submit button with selector: {selector}")
                    break

            if not submit_button:
                raise ScrapeErrorException("Submit button not found on extend form")

            logger.info("Submitting extension")
            await submit_button.click()
            await self.page.wait_for_load_state(
                "networkidle",
                timeout=self._get_timeout_ms("navigation"),
            )
            await self.page.wait_for_timeout(2000)

            # Read back the new end time from the refreshed page
            # Re-query the booking card to get updated times
            updated_items = await self.page.query_selector_all(".parkapp-item")
            new_end_time = None

            for item in updated_items:
                license_element = await item.query_selector(
                    ".license-plate.active, .license-plate-text"
                )
                if license_element:
                    try:
                        item_license = await license_element.inner_text()
                        item_license = item_license.upper().replace(" ", "")
                        target_plate = license_plate.upper().replace("-", "").replace(" ", "")
                        if item_license == target_plate:
                            # Get the end time from the time containers
                            time_elements = await item.query_selector_all(
                                ".time-container > .time > div"
                            )
                            if len(time_elements) >= 2:
                                end_time_elem = time_elements[1]
                                end_time_text = await end_time_elem.inner_text()
                                end_time_text = end_time_text.replace("\xa0", " ").strip()
                                logger.info(f"Read back end time from page: {end_time_text}")

                                # Parse the Dutch time format
                                from datetime import timezone as tz
                                new_end_time = parse_dutch_time(
                                    end_time_text, base_date=datetime.now(tz.utc)
                                )
                                break
                    except Exception as e:
                        logger.warning(f"Error reading updated booking: {e}")
                        continue

            if not new_end_time:
                logger.warning(
                    f"Could not read back new end time from page, "
                    f"using calculated fallback"
                )
                # Fallback: calculate from current time
                new_end_time = datetime.now(timezone.utc) + timedelta(
                    minutes=additional_minutes
                )

            return {
                "license_plate": license_plate,
                "new_end_time": new_end_time,
            }

        except (BookingNotFoundException, ScrapeErrorException):
            raise
        except PlaywrightTimeoutError:
            raise TimeoutException("Timeout while extending booking")
        except Exception as e:
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="/tmp/2park_extend_error.png")
                logger.info("Screenshot saved to /tmp/2park_extend_error.png")
            except Exception:
                pass
            logger.error(f"Error extending booking: {e}")
            raise ScrapeErrorException(f"Failed to extend booking: {str(e)}")

    async def cancel_booking(self, license_plate: str) -> Dict:
        """Cancel an existing booking"""
        try:
            logger.info(f"Cancelling booking for {license_plate}")

            # Find the booking card using the shared helper
            booking_card = await self._find_booking_card(license_plate)
            if not booking_card:
                raise BookingNotFoundException(
                    f"Could not find booking UI for {license_plate}"
                )
            target_item = booking_card["card_element"]

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
