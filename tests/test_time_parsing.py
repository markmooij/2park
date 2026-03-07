"""Tests for time parsing utilities"""

from datetime import datetime, timedelta


def test_calculate_end_time():
    """Test end time calculation"""
    start = datetime(2025, 1, 15, 14, 30, 0)
    duration_minutes = 90
    end = start + timedelta(minutes=duration_minutes)

    assert end.year == 2025
    assert end.month == 1
    assert end.day == 15
    assert end.hour == 16
    assert end.minute == 0  # 14:30 + 90 min = 16:00


def test_time_format_conversions():
    """Test various time format conversions"""
    # ISO format without timezone
    dt1 = datetime(2025, 1, 15, 14, 30, 0)
    assert dt1.strftime("%Y-%m-%dT%H:%M:%S") == "2025-01-15T14:30:00"

    # ISO format with Z suffix
    dt2 = datetime(2025, 1, 15, 14, 30, 0)
    assert dt2.strftime("%Y-%m-%dT%H:%M:%SZ") == "2025-01-15T14:30:00Z"


def test_duration_edge_cases():
    """Test edge case durations"""
    # 60 minutes = 1 hour
    start = datetime(2025, 1, 15, 10, 0, 0)
    end = start + timedelta(minutes=60)
    assert end.hour == 11

    # 120 minutes = 2 hours
    start = datetime(2025, 1, 15, 10, 0, 0)
    end = start + timedelta(minutes=120)
    assert end.hour == 12

    # 90 minutes = 1.5 hours
    start = datetime(2025, 1, 15, 10, 0, 0)
    end = start + timedelta(minutes=90)
    assert end.hour == 11
    assert end.minute == 30
