"""
Example test script for 2Park API
Demonstrates how to use the API endpoints
"""

import os
import sys
from datetime import datetime

# requests is used for testing the API endpoints
# Install with: uv add requests
try:
    import requests
except ImportError:
    requests = None

# Configuration
API_BASE = "http://localhost:8090"
API_TOKEN = os.getenv("API_TOKEN", "your-token-here")

# Headers with authentication
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        import json

        print(json.dumps(data, indent=2))
    except Exception:
        print(response.text)


def test_health_check():
    """Test health check endpoint (no auth required)"""
    print_section("Health Check")
    try:
        response = requests.get(f"{API_BASE}/health")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_get_balance():
    """Test getting account balance"""
    print_section("Get Account Balance")
    try:
        response = requests.get(f"{API_BASE}/api/account/balance", headers=headers)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_create_booking(license_plate: str = "TEST-123-X"):
    """Test creating a booking"""
    print_section(f"Create Booking for {license_plate}")
    try:
        data = {
            "license_plate": license_plate,
            "start_time": "now",
            "duration_minutes": 60,
        }
        response = requests.post(f"{API_BASE}/api/bookings", headers=headers, json=data)
        print_response(response)
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_extend_booking(license_plate: str = "TEST-123-X"):
    """Test extending a booking"""
    print_section(f"Extend Booking for {license_plate}")
    try:
        data = {"additional_minutes": 30}
        response = requests.post(
            f"{API_BASE}/api/bookings/{license_plate}/extend",
            headers=headers,
            json=data,
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_cancel_booking(license_plate: str = "TEST-123-X"):
    """Test cancelling a booking"""
    print_section(f"Cancel Booking for {license_plate}")
    try:
        response = requests.post(
            f"{API_BASE}/api/bookings/{license_plate}/cancel", headers=headers
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_invalid_token():
    """Test with invalid token"""
    print_section("Test Invalid Token")
    try:
        invalid_headers = {
            "Authorization": "Bearer invalid-token-here",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{API_BASE}/api/account/balance", headers=invalid_headers
        )
        print_response(response)
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_missing_token():
    """Test with missing token"""
    print_section("Test Missing Token")
    try:
        response = requests.get(f"{API_BASE}/api/account/balance")
        print_response(response)
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  2PARK API TEST SUITE")
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE}")
    print(
        f"Using Token: {API_TOKEN[:10]}..." if len(API_TOKEN) > 10 else "No token set"
    )
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Health check (should always work)
    results.append(("Health Check", test_health_check()))

    # Test 2: Invalid token (should fail with 401)
    results.append(("Invalid Token", test_invalid_token()))

    # Test 3: Missing token (should fail with 401)
    results.append(("Missing Token", test_missing_token()))

    # Test 4: Get balance (requires valid credentials)
    results.append(("Get Balance", test_get_balance()))

    # Uncomment to test booking operations (be careful with real bookings!)
    # results.append(("Create Booking", test_create_booking()))
    # results.append(("Extend Booking", test_extend_booking()))
    # results.append(("Cancel Booking", test_cancel_booking()))

    # Print summary
    print_section("TEST RESULTS SUMMARY")
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    # Check if API token is set
    if API_TOKEN == "your-token-here":
        print("Error: API_TOKEN not set!")
        print("Please set the API_TOKEN environment variable:")
        print("  export API_TOKEN='your-token'")
        sys.exit(1)

    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print(f"Warning: API server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to API server at {API_BASE}")
        print("Please start the server first:")
        print("  python api.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking API server: {e}")
        sys.exit(1)

    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
