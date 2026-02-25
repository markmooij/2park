"""
2Park Reservation Checker
Automates checking active reservations and balance on 2park.nl
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional

from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TwoParkChecker:
    """Class to handle 2Park website automation"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def launch_browser(self):
        """Launch browser with proper configuration"""
        try:
            logger.info("Launching browser...")
            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.chromium.launch(
                headless=False,
                slow_mo=50,
                args=[
                    "--start-maximized",
                ],
            )

            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def create_page(self):
        """Create a new page with proper viewport settings"""
        try:
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self.page = await context.new_page()
            logger.info("New page created")
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise

    async def login(self):
        """Login to 2Park website"""
        try:
            logger.info("Navigating to login page...")
            await self.page.goto(
                "https://mijn.2park.nl/login",
                wait_until="networkidle",
                timeout=30000,
            )

            logger.info("Waiting for login form...")
            await self.page.wait_for_selector("#login_email", timeout=10000)

            logger.info("Filling in email...")
            await self.page.fill("#login_email", self.email)

            logger.info("Filling in password...")
            await self.page.fill("#login_password", self.password)

            logger.info("Clicking login button...")
            await self.page.click('button[type="submit"]')

            logger.info("Waiting for navigation after login...")
            await self.page.wait_for_load_state("networkidle", timeout=30000)

            logger.info("Login successful")

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout during login: {e}")
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    async def get_active_reservations(self) -> List[Dict[str, str]]:
        """Get all active reservations"""
        try:
            logger.info("Fetching active reservations...")

            # Wait for the active reservations to load
            await self.page.wait_for_selector(".parkapp-item", timeout=10000)

            # Get all reservation items
            reservation_items = await self.page.query_selector_all(".parkapp-item")
            logger.info(f"Found {len(reservation_items)} reservation(s)")

            reservations = []
            for idx, item in enumerate(reservation_items, 1):
                try:
                    # Extract the name (if not unknown)
                    name_element = await item.query_selector(
                        ".favorite-name > span:not(.anonymouse)"
                    )
                    if name_element:
                        name = await name_element.inner_text()
                    else:
                        name = "Unknown"

                    # Extract the license plate
                    license_plate_element = await item.query_selector(
                        ".license-plate-text"
                    )
                    if license_plate_element:
                        license_plate = await license_plate_element.inner_text()
                    else:
                        license_plate = "N/A"

                    # Extract the start and end times
                    time_elements = await item.query_selector_all(
                        ".time-container > .time > div"
                    )
                    if len(time_elements) >= 2:
                        start_time = await time_elements[0].inner_text()
                        end_time = await time_elements[1].inner_text()
                    else:
                        start_time = "N/A"
                        end_time = "N/A"

                    reservation = {
                        "name": name,
                        "license_plate": license_plate,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                    reservations.append(reservation)
                    logger.info(f"Reservation {idx}: {reservation}")

                except Exception as e:
                    logger.error(f"Error extracting reservation {idx}: {e}")
                    continue

            return reservations

        except PlaywrightTimeoutError:
            logger.warning("No reservations found or timeout waiting for reservations")
            return []
        except Exception as e:
            logger.error(f"Error getting reservations: {e}")
            return []

    async def get_current_balance(self) -> Optional[float]:
        """Get current account balance"""
        try:
            logger.info("Fetching current balance...")

            # Wait for the balance element to load
            await self.page.wait_for_selector(
                ".balance-container .amount", timeout=10000
            )

            # Extract the amount element
            amount_element = await self.page.query_selector(
                ".balance-container .amount"
            )
            if amount_element:
                amount_text = await amount_element.inner_text()

                # Clean and convert the amount text to a float
                amount = amount_text.replace("€", "").replace(",", ".").strip()
                balance = float(amount)
                logger.info(f"Balance: € {balance}")
                return balance
            else:
                logger.warning("Balance element not found")
                return None

        except PlaywrightTimeoutError:
            logger.warning("Timeout waiting for balance element")
            return None
        except ValueError as e:
            logger.error(f"Error parsing balance amount: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None

    async def close(self):
        """Close the browser and playwright"""
        try:
            if self.browser:
                logger.info("Closing browser...")
                await self.browser.close()
                logger.info("Browser closed")

            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def run(self):
        """Main execution flow"""
        try:
            await self.launch_browser()
            await self.create_page()
            await self.login()

            # Get active reservations
            reservations = await self.get_active_reservations()

            # Get current balance
            balance = await self.get_current_balance()

            # Print results
            print("\n" + "=" * 50)
            print("ACTIVE RESERVATIONS")
            print("=" * 50)
            if reservations:
                for idx, res in enumerate(reservations, 1):
                    print(f"\nReservation {idx}:")
                    print(f"  Name: {res['name']}")
                    print(f"  License Plate: {res['license_plate']}")
                    print(f"  Start Time: {res['start_time']}")
                    print(f"  End Time: {res['end_time']}")
            else:
                print("No active reservations found")

            print("\n" + "=" * 50)
            print("ACCOUNT BALANCE")
            print("=" * 50)
            if balance is not None:
                print(f"€ {balance:.2f}")
            else:
                print("Unable to retrieve balance")
            print("=" * 50 + "\n")

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main entry point"""
    # Get credentials from environment variables
    email = os.getenv("TWOPARK_EMAIL")
    password = os.getenv("TWOPARK_PASSWORD")

    if not email or not password:
        logger.error("Missing credentials!")
        logger.error(
            "Please set environment variables: TWOPARK_EMAIL and TWOPARK_PASSWORD"
        )
        logger.info("\nExample:")
        logger.info("  export TWOPARK_EMAIL='your-email@example.com'")
        logger.info("  export TWOPARK_PASSWORD='your-password'")
        sys.exit(1)

    checker = TwoParkChecker(email, password)

    try:
        await checker.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        await checker.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await checker.close()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        sys.exit(0)
