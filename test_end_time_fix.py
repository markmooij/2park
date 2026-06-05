#!/usr/bin/env python3
"""
Test script to verify the end_time fix for booking creation.
Tests against the live API at rasp-pi-4-service.local:8090.

Usage:
    python test_end_time_fix.py
"""

import json
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Install with: pip install requests")
    sys.exit(1)

API_BASE = "http://rasp-pi-4-service.local:8090"
API_TOKEN = "b6a32d1cde51a1dce7e21343f8233a501afe49cbf3bc0983263591fbf3e3ce43"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


def check_server():
    """Verify the API server is reachable."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"ERROR: Cannot reach API server: {e}")
        return False


def create_booking(license_plate: str, start_time: str, duration_minutes: int):
    """Create a booking and return the response JSON."""
    data = {
        "license_plate": license_plate,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
    }
    r = requests.post(f"{API_BASE}/api/bookings", headers=HEADERS, json=data, timeout=120)
    return r.status_code, r.json()


def list_bookings():
    """List active bookings and return the response JSON."""
    r = requests.get(f"{API_BASE}/api/bookings", headers=HEADERS, timeout=30)
    return r.status_code, r.json()


def cancel_booking(license_plate: str):
    """Cancel a booking and return the response JSON."""
    r = requests.post(
        f"{API_BASE}/api/bookings/{license_plate}/cancel",
        headers=HEADERS,
        timeout=120,
    )
    return r.status_code, r.json()


def print_result(test_name: str, passed: bool):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}  {test_name}")
    return passed


def run_test(duration_minutes: int, label: str) -> bool:
    """Run a full create → verify → list → cancel → verify cycle."""
    print(f"\n{'='*60}")
    print(f"  TEST RUN: {label} (duration={duration_minutes} min)")
    print(f"{'='*60}")

    license_plate = "51TEST"
    all_passed = True

    # --- 1. Create booking with start_time="now" ---
    now = datetime.now(timezone.utc)
    expected_end = now + timedelta(minutes=duration_minutes)
    print(f"\n1. Create booking  (license={license_plate}, duration={duration_minutes} min)")
    print(f"   Expected end_time: {expected_end.isoformat()}")

    status, body = create_booking(license_plate, "now", duration_minutes)
    if status != 201:
        print(f"   ✗ Create failed: {status} {body}")
        return False
    print(f"   Response: {json.dumps(body, indent=2)}")

    returned_end = datetime.fromisoformat(body["end_time"].replace("Z", "+00:00"))
    diff_seconds = abs((returned_end - expected_end).total_seconds())
    diff_minutes = diff_seconds / 60

    passed = diff_minutes <= 1  # allow 1 minute tolerance for processing delay
    all_passed &= print_result(
        f"end_time correct (diff={diff_minutes:.1f} min)", passed
    )
    if not passed:
        print(f"   Expected: {expected_end.isoformat()}")
        print(f"   Got:      {returned_end.isoformat()}")

    # --- 2. List bookings and verify end_time is correct ---
    print(f"\n2. List bookings")
    status, body = list_bookings()
    if status != 200:
        print(f"   ✗ List failed: {status} {body}")
        return False

    found = False
    for b in body.get("bookings", []):
        if b["license_plate"] == license_plate:
            found = True
            list_end = datetime.fromisoformat(b["end_time"].replace("Z", "+00:00"))
            # The scraper can't reliably read exact times from the 2Park website.
            # We verify that:
            #  1. The end_time is NOT the buggy "23:59" placeholder
            #  2. The end_time is after the start_time (reasonable for a future booking)
            is_2359_bug = list_end.hour == 23 and list_end.minute == 59
            is_reasonable = list_end > now and list_end < now + timedelta(hours=4)
            passed = not is_2359_bug and is_reasonable
            all_passed &= print_result(
                f"List end_time reasonable (not 23:59 bug, after start)", passed
            )
            if not passed:
                if is_2359_bug:
                    print("   FAIL: end_time is 23:59 (the original bug)")
                if not is_reasonable:
                    print(f"   FAIL: end_time {list_end} is not reasonable")
                print(f"   Note: The scraper cannot read exact times from the website.")
                print(f"   The create_booking endpoint returns the correct calculated time.")
            break

    if not found:
        all_passed &= print_result("Booking found in list", False)

    # --- 3. Cancel booking ---
    print(f"\n3. Cancel booking")
    status, body = cancel_booking(license_plate)
    if status != 200:
        print(f"   ✗ Cancel failed: {status} {body}")
        return False
    print(f"   Response: {json.dumps(body, indent=2)}")

    passed = body.get("status") == "cancelled"
    all_passed &= print_result("Booking cancelled successfully", passed)

    # --- 4. Verify booking no longer in active list ---
    print(f"\n4. Verify cancelled booking removed from active list")
    status, body = list_bookings()
    still_active = any(
        b["license_plate"] == license_plate
        for b in body.get("bookings", [])
    )
    passed = not still_active
    all_passed &= print_result("Booking removed from active list", passed)

    return all_passed


def main():
    print("=" * 60)
    print("  2Park API — end_time Fix Verification")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not check_server():
        sys.exit(1)

    results = []

    # Run 1: 120 minutes
    results.append(("Run 1 — 120 min", run_test(120, "120-minute booking")))

    # Run 2: 90 minutes
    results.append(("Run 2 — 90 min", run_test(90, "90-minute booking")))

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for name, passed in results:
        print_result(name, passed)

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} runs passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
