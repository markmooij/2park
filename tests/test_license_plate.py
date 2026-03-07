"""Tests for license plate validation"""

import pytest

from models import validate_license_plate


def test_validate_license_plate_valid_formats():
    """Test valid Dutch license plate formats"""
    # Current EU format with dashes (XX-XX-X)
    assert validate_license_plate("AB-12-X") == "AB-12-X"
    # Historic format with dashes (XX-XX-XX)
    assert validate_license_plate("XX-XX-12") == "XX-XX-12"
    # Historic format with letters (XX-XXX-XX)
    assert validate_license_plate("XX-AAA-12") == "XX-AAA-12"

    # Simple format without dashes (7 chars: 2 letters + 3 digits + 2 letters)
    assert validate_license_plate("AB123CD") == "AB123CD"

    # Mixed case should be normalized to uppercase
    assert validate_license_plate("ab-12-x") == "AB-12-X"
    assert validate_license_plate("Ab123Cd") == "AB123CD"


def test_validate_license_plate_invalid_formats():
    """Test invalid license plate formats raise ValueError"""
    # Too short
    with pytest.raises(ValueError):
        validate_license_plate("A-12-BC")

    # Too long
    with pytest.raises(ValueError):
        validate_license_plate("ABC-123-DEF")

    # Invalid characters
    with pytest.raises(ValueError):
        validate_license_plate("AB-12-CD!")

    # All numbers
    with pytest.raises(ValueError):
        validate_license_plate("123-456")

    # Empty after stripping
    with pytest.raises(ValueError):
        validate_license_plate("   ")


def test_validate_license_plate_whitespace():
    """Test that whitespace is handled correctly"""
    assert validate_license_plate(" AB-12-X ") == "AB-12-X"
    assert validate_license_plate("  AB123CD  ") == "AB123CD"


def test_validate_license_plate_empty():
    """Test empty string handling"""
    with pytest.raises(ValueError):
        validate_license_plate("")
