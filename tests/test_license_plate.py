"""Tests for license plate validation and normalization"""

import pytest

from models import normalize_license_plate, validate_license_plate


# ── normalize_license_plate tests ────────────────────────────────────


class TestNormalizeLicensePlate:
    """Tests for normalize_license_plate utility"""

    def test_strips_hyphens(self):
        assert normalize_license_plate("51-PX-PN") == "51PXPN"
        assert normalize_license_plate("AB-12-X") == "AB12X"

    def test_strips_spaces(self):
        assert normalize_license_plate("5 1 P X P N") == "51PXPN"
        assert normalize_license_plate("AB 12 X") == "AB12X"

    def test_uppercases(self):
        assert normalize_license_plate("51-px-pn") == "51PXPN"
        assert normalize_license_plate("ab-12-x") == "AB12X"

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_license_plate("  AB-12-X  ") == "AB12X"

    def test_idempotent(self):
        already = "51PXPN"
        assert normalize_license_plate(already) == already
        assert normalize_license_plate(normalize_license_plate("51-PX-PN")) == "51PXPN"

    def test_no_change_when_already_normalized(self):
        assert normalize_license_plate("AB123CD") == "AB123CD"
        assert normalize_license_plate("51PXPN") == "51PXPN"

    def test_mixed_hyphens_and_spaces(self):
        assert normalize_license_plate("51- PX PN") == "51PXPN"


# ── validate_license_plate tests ─────────────────────────────────────


class TestValidateLicensePlate:
    """Tests for validate_license_plate — now normalizes before validating"""

    def test_valid_formats_return_normalized(self):
        """Valid plates with hyphens should be normalized (hyphens removed)"""
        assert validate_license_plate("AB-12-X") == "AB12X"
        assert validate_license_plate("XX-XX-12") == "XXXX12"
        assert validate_license_plate("XX-AAA-12") == "XXAAA12"

        # Already normalized — no change
        assert validate_license_plate("AB123CD") == "AB123CD"

    def test_kv_format(self):
        """KV/KVX format plates"""
        assert validate_license_plate("51-PXPN") == "51PXPN"
        assert validate_license_plate("51PXPN") == "51PXPN"
        assert validate_license_plate("51-pxpn") == "51PXPN"

    def test_mixed_case_normalized(self):
        assert validate_license_plate("ab-12-x") == "AB12X"
        assert validate_license_plate("Ab123Cd") == "AB123CD"

    def test_invalid_formats(self):
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

    def test_whitespace_handled(self):
        assert validate_license_plate(" AB-12-X ") == "AB12X"
        assert validate_license_plate("  AB123CD  ") == "AB123CD"

    def test_empty_string(self):
        with pytest.raises(ValueError):
            validate_license_plate("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError):
            validate_license_plate("   ")
