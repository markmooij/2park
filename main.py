"""
2Park Reservation Checker CLI
Automates checking active reservations and balance on 2park.nl

This CLI tool uses the TwoParkScraper for browser automation.
"""

import asyncio
import logging
import os
import sys

from scraper import TwoParkScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_checker(email: str, password: str):
    """Run the parking checker using TwoParkScraper"""
    async with TwoParkScraper(email, password) as scraper:
        # Get active reservations
        reservations = await scraper.get_active_reservations()

        # Get current balance
        balance = await scraper.get_balance()

        # Print results
        print("\n" + "=" * 50)
        print("ACTIVE RESERVATIONS")
        print("=" * 50)
        if reservations:
            for idx, res in enumerate(reservations, 1):
                print(f"\nReservation {idx}:")
                print(f"  Name: {res.name}")
                print(f"  License Plate: {res.license_plate}")
                print(f"  Start Time: {res.start_time}")
                print(f"  End Time: {res.end_time}")
        else:
            print("No active reservations found")

        print("\n" + "=" * 50)
        print("ACCOUNT BALANCE")
        print("=" * 50)
        if balance is not None:
            print(f"\u20ac {balance:.2f}")
        else:
            print("Unable to retrieve balance")
        print("=" * 50 + "\n")


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

    try:
        await run_checker(email, password)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        sys.exit(0)
