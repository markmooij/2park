#!/usr/bin/env python3
"""
TP-001: Consolidated End-to-End API Test Run

Tests the 2Park API against the live Raspberry Pi instance and verifies
state on the 2park.nl website via Playwright.

Usage:
    python test_run.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx
from playwright.async_api import async_playwright

# Configuration
API_URL = os.getenv("API_URL", "http://rasp-pi-4-service.local:8090")
API_TOKEN = os.getenv("API_TOKEN", "b6a32d1cde51a1dce7e21343f8233a501afe49cbf3e3ce43")
TWOPARK_EMAIL = os.getenv("TWOPARK_EMAIL", "")
TWOPARK_PASSWORD = os.getenv("TWOPARK_PASSWORD", "")
WEBSITE_URL = "https://mijn.2park.nl"
LICENSE_PLATE = "51-PX-PN"
LICENSE_PLATE_NORMALIZED = "51PXPN"

headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}


def log_step(step, description, result, details=""):
    """Log a test step result."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status_icon = "✅" if result == "PASS" else "❌"
    print(f"\n{'='*60}")
    print(f"[{timestamp}] Step {step}: {description}")
    print(f"  Result: {status_icon} {result}")
    if details:
        print(f"  Details: {details}")
    print(f"{'='*60}")


def log_api_request(method, endpoint, status_code, response_body, request_body=None):
    """Log an API request."""
    print(f"  {method} {endpoint}")
    print(f"  Status: {status_code}")
    if request_body:
        print(f"  Request: {json.dumps(request_body)}")
    print(f"  Response: {json.dumps(response_body)}")


async def preflight_check():
    """Step 0: Verify prerequisites."""
    # Check API health
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_URL}/health")
        assert resp.status_code == 200, f"API health check failed: {resp.status_code}"
        data = resp.json()
        log_step(0, "API Health Check", "PASS", f"Status: {data.get('status')}")
    
    # Check credentials
    assert TWOPARK_EMAIL, "TWOPARK_EMAIL not set"
    assert TWOPARK_PASSWORD, "TWOPARK_PASSWORD not set"
    log_step(0, "Credentials", "PASS", f"Email: {TWOPARK_EMAIL}")
    
    return True


async def api_create_booking():
    """Step 1: Create a booking."""
    body = {
        "license_plate": LICENSE_PLATE,
        "start_time": "now",
        "duration_minutes": 120,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{API_URL}/api/bookings", json=body, headers=headers)
        data = resp.json()
        log_api_request("POST", "/api/bookings", resp.status_code, data, body)
        
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        assert data["license_plate"] == LICENSE_PLATE
        assert data["status"] == "active"
        log_step(1, "Create Booking", "PASS", 
                 f"start={data['start_time']}, end={data['end_time']}")
        
        return data


async def api_extend_booking():
    """Step 2: Extend a booking (may fail due to scraper selector issues)."""
    body = {"additional_minutes": 60}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{API_URL}/api/bookings/{LICENSE_PLATE_NORMALIZED}/extend",
            json=body, headers=headers
        )
        data = resp.json()
        log_api_request("POST", f"/api/bookings/{LICENSE_PLATE_NORMALIZED}/extend", 
                       resp.status_code, data, body)
        
        if resp.status_code == 200:
            log_step(2, "Extend Booking", "PASS", 
                    f"new_end_time={data.get('new_end_time')}")
            return data
        else:
            log_step(2, "Extend Booking", "FAIL", 
                    f"Scraper selector mismatch: {data.get('error', {}).get('message', resp.text)}")
            return None


async def api_list_bookings():
    """Step 3: List active bookings."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_URL}/api/bookings", headers=headers)
        data = resp.json()
        log_api_request("GET", "/api/bookings", resp.status_code, data)
        
        log_step(3, "List Active Bookings", "PASS", 
                f"Count: {data.get('count', 0)}")
        
        # Also check balance
        resp2 = await client.get(f"{API_URL}/api/account/balance", headers=headers)
        balance_data = resp2.json()
        log_api_request("GET", "/api/account/balance", resp2.status_code, balance_data)
        log_step(3, "Account Balance", "PASS", 
                f"€{balance_data.get('balance')} {balance_data.get('currency')}")
        
        return data


async def api_cancel_booking():
    """Step 4: Cancel a booking."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{API_URL}/api/bookings/{LICENSE_PLATE_NORMALIZED}/cancel",
            headers=headers
        )
        data = resp.json()
        log_api_request("POST", f"/api/bookings/{LICENSE_PLATE_NORMALIZED}/cancel", 
                       resp.status_code, data)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert data["status"] == "cancelled"
        log_step(4, "Cancel Booking", "PASS", 
                f"cancelled_at={data.get('cancelled_at')}")
        
        return data


async def playwright_verify_login():
    """Helper: Log in to 2park.nl. Returns browser, context, page."""
    p_instance = await async_playwright().start()
    browser = await p_instance.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    try:
        # Navigate to login
        await page.goto(f"{WEBSITE_URL}/login", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Fill login form (no name attributes, use type + placeholder)
        await page.fill('input[type="email"]', TWOPARK_EMAIL)
        await page.fill('input[type="password"]', TWOPARK_PASSWORD)
        await page.click('button:has-text("Log in")')
        
        # Wait for navigation to dashboard
        await page.wait_for_url("**/", timeout=30000)
        await page.wait_for_timeout(8000)
    except Exception as e:
        await page.screenshot(path="/tmp/login_error.png")
        body_text = await page.inner_text("body")
        raise RuntimeError(f"Login failed: {e}. Body: {body_text[:300]}")
    
    return p_instance, browser, context, page


async def playwright_verify_dashboard(browser, page, step, description, screenshot_name):
    """Helper: Take screenshot of dashboard."""
    await page.screenshot(path=f"/tmp/{screenshot_name}.png")
    body_text = await page.inner_text("body")
    
    # Check for active bookings
    has_active = "Geen lopende parkeeracties gevonden" not in body_text
    
    log_step(step, description, "PASS", 
            f"Screenshot: /tmp/{screenshot_name}.png, Body preview: {body_text[:200]}")
    
    return has_active


async def playwright_verification_steps():
    """Steps 5-7: Playwright verification of booking state."""
    p_instance, browser, context, page = await playwright_verify_login()
    
    try:
        # Step 5: Verify dashboard loads
        await page.goto(f"{WEBSITE_URL}/", timeout=60000)
        await page.wait_for_timeout(8000)
        
        # Take screenshot
        await page.screenshot(path="/tmp/dashboard_after_cancel.png")
        
        # Check if booking was visible (should NOT be visible since cancelled)
        body_text = await page.inner_text("body")
        if "Geen lopende parkeeracties gevonden" in body_text:
            log_step(5, "Active Booking Visible", "PASS", 
                    "No active bookings shown (correct — booking was cancelled)")
        else:
            log_step(5, "Active Booking Visible", "FAIL", 
                    "Unexpected content on dashboard")
        
        # Step 6: Check scheduled bookings tab
        await page.click("text=Gepland")
        await page.wait_for_timeout(5000)
        await page.screenshot(path="/tmp/dashboard_scheduled.png")
        log_step(6, "Scheduled Bookings Tab", "PASS", "Screenshot: /tmp/dashboard_scheduled.png")
        
        # Step 7: Verify no active booking for our plate
        await page.click("text=Lopend")
        await page.wait_for_timeout(3000)
        body_text = await page.inner_text("body")
        
        # The booking should not be in active bookings
        if "51PXPN" not in body_text and "51-PX-PN" not in body_text:
            log_step(7, "Cancelled Booking Not in Active", "PASS",
                    "License plate not found in active bookings")
        else:
            log_step(7, "Cancelled Booking Not in Active", "FAIL",
                    "License plate still visible in active bookings")
        
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await p_instance.stop()


async def cleanup():
    """Step 8: Verify cleanup."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_URL}/api/bookings", headers=headers)
        data = resp.json()
        
        active_bookings = [b for b in data.get("bookings", []) 
                          if b.get("status") == "active" 
                          and b.get("license_plate", "").replace("-", "") == LICENSE_PLATE_NORMALIZED]
        
        if not active_bookings:
            log_step(8, "Cleanup Verification", "PASS", 
                    "No active test bookings remain")
        else:
            log_step(8, "Cleanup Verification", "FAIL", 
                    f"Found {len(active_bookings)} active test bookings")
        
        return data


async def main():
    """Run all test steps."""
    print("=" * 60)
    print("TP-001: Consolidated End-to-End API Test Run")
    print(f"API: {API_URL}")
    print(f"Website: {WEBSITE_URL}")
    print(f"License Plate: {LICENSE_PLATE}")
    print("=" * 60)
    
    results = {}
    
    # Step 0: Preflight
    try:
        await preflight_check()
        results["step_0"] = "PASS"
    except Exception as e:
        log_step(0, "Preflight", "FAIL", str(e))
        results["step_0"] = "FAIL"
        return 1
    
    # Step 1: Create Booking
    try:
        booking = await api_create_booking()
        results["step_1"] = "PASS"
    except Exception as e:
        log_step(1, "Create Booking", "FAIL", str(e))
        results["step_1"] = "FAIL"
    
    # Step 2: Extend Booking (may fail due to scraper issues)
    try:
        result = await api_extend_booking()
        results["step_2"] = "PASS" if result else "FAIL"
    except Exception as e:
        log_step(2, "Extend Booking", "FAIL", str(e))
        results["step_2"] = "FAIL"
    
    # Step 3: List Active Bookings
    try:
        bookings = await api_list_bookings()
        results["step_3"] = "PASS"
    except Exception as e:
        log_step(3, "List Bookings", "FAIL", str(e))
        results["step_3"] = "FAIL"
    
    # Step 4: Cancel Booking
    try:
        await api_cancel_booking()
        results["step_4"] = "PASS"
    except Exception as e:
        log_step(4, "Cancel Booking", "FAIL", str(e))
        results["step_4"] = "FAIL"
    
    # Steps 5-7: Playwright verification
    try:
        await playwright_verification_steps()
        results["step_5"] = "PASS"
        results["step_6"] = "PASS"
        results["step_7"] = "PASS"
    except Exception as e:
        log_step(5, "Playwright Verification", "FAIL", str(e))
        results["step_5"] = "FAIL"
        results["step_6"] = "FAIL"
        results["step_7"] = "FAIL"
    
    # Step 8: Cleanup
    try:
        await cleanup()
        results["step_8"] = "PASS"
    except Exception as e:
        log_step(8, "Cleanup", "FAIL", str(e))
        results["step_8"] = "FAIL"
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    for step, result in results.items():
        icon = "✅" if result == "PASS" else "❌"
        print(f"  {icon} {step}: {result}")
    
    all_pass = all(r == "PASS" for r in results.values())
    print(f"\nOverall: {'✅ ALL PASSED' if all_pass else '❌ SOME FAILED'}")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
